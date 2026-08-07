import os, re, glob, json, uuid, time, traceback, threading
from datetime import datetime, timedelta
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, send_file, jsonify, abort)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user,
                         logout_user, login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

import pdfplumber

# win32com sadece Windows + Excel kuruluysa çalışır
try:
    import win32com.client
    import pythoncom
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

# ─── UYGULAMA YAPISI ─────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER  = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER  = os.path.join(BASE_DIR, 'outputs')
TEMPLATE_PATH  = os.path.join(BASE_DIR, 'FATURA2026.xlsx')   # Şablonu buraya koy

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'TSE-FATURA-SECRET-2026-LOCAL-ONLY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

ADSENSE_CLIENT = 'ca-pub-6335356250153811'  # Google AdSense Yayıncı ID'niz
ADSENSE_SLOT_LEFT  = 'XXXXXXXXXX'   # Sol reklam alanı
ADSENSE_SLOT_RIGHT = 'XXXXXXXXXX'   # Sağ reklam alanı

FREE_LIMIT          = 3   # Ücretsiz kullanıcı için günlük PDF limiti
FREE_MONTHLY_LIMIT  = 3   # Veritabanı modeli için
AD_REWARD_COUNT     = 3   # Reklam izleme başına kazanılan ek hak

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
with app.app_context():
    db.create_all()

# ─── VERİTABANI MODELLERİ ────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    plan          = db.Column(db.String(20), default='free')   # free / pro / kurumsal
    monthly_usage = db.Column(db.Integer, default=0)
    reset_date    = db.Column(db.DateTime, default=datetime.utcnow)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw): self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)

    def can_process(self):
        if self.plan != 'free': return True
        # Aylık sayacı sıfırla
        if datetime.utcnow() - self.reset_date > timedelta(days=30):
            self.monthly_usage = 0
            self.reset_date = datetime.utcnow()
            db.session.commit()
        return self.monthly_usage < FREE_MONTHLY_LIMIT

    def remaining(self):
        if self.plan != 'free': return 999
        return max(0, FREE_MONTHLY_LIMIT - self.monthly_usage)

@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))

# ─── YARDIMCI FONKSİYONLAR ───────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'

# ─── PDF OKUMA (masaüstü versiyondan birebir taşındı) ────────────────────────
def extract_data_from_pdf(pdf_path):
    data = {
        "evrak_no":"","basvuru_yili":"","firma_adi":"",
        "fatura_adresi":"","vergi_dairesi":"","vergi_no":"",
        "telefon":"","eposta":"","items":[]
    }
    with pdfplumber.open(pdf_path) as pdf:
        for table in pdf.pages[0].extract_tables():
            for row in table:
                row = [str(c).strip() if c else '' for c in row]
                if len(row)>=4 and 'Evrak No' in row[0]:
                    data['evrak_no'] = row[1]
                    ds = row[3]
                    if '.' in ds:
                        try: data['basvuru_yili'] = int(ds.split('.')[-1])
                        except: pass
                if len(row)>=3:
                    lbl = row[1].lower()
                    if 'adı' in lbl or 'adi' in lbl:
                        data['firma_adi'] = row[2].replace('\n',' ')
                    elif 'fatura adresi' in lbl:
                        data['fatura_adresi'] = row[2].replace('\n',' ')
                    elif 'vergi dairesi' in lbl:
                        data['vergi_dairesi'] = row[2].replace('\n',' ')
                    elif 'vergi no' in lbl:
                        data['vergi_no'] = row[2].replace('\n',' ')

        full = "".join(p.extract_text() or "" for p in pdf.pages)
        m = re.search(r"GSM\s*(\d+)", full)
        if not m: m = re.search(r"Telefon\s*(\d+)", full)
        if m: data["telefon"] = m.group(1).strip()
        m2 = re.search(r"E-Posta\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", full, re.IGNORECASE)
        if m2: data["eposta"] = m2.group(1).strip()

        raw = []
        for p in pdf.pages:
            for table in p.extract_tables():
                hi=prj=tab=btr=-1
                for i, row in enumerate(table):
                    rc=[str(c).replace('\n',' ').strip() if c else '' for c in row]
                    if 'Proje Kay' in ' '.join(rc):
                        hi=i
                        for j,cell in enumerate(rc):
                            if 'Proje Kay' in cell: prj=j
                            elif 'Tabanca' in cell or 'Saya' in cell: tab=j
                            elif 'Türü' in cell or 'T\u00fcr\u00fc' in cell: btr=j
                        break
                if hi!=-1 and prj!=-1:
                    for row in table[hi+1:]:
                        if len(row)>prj:
                            pno=str(row[prj]).replace('\n','').strip()
                            if re.match(r'^[A-Z]+-\d+',pno):
                                adet=1
                                if tab!=-1 and len(row)>tab and row[tab]:
                                    try: adet=int(str(row[tab]).replace('\n','').strip())
                                    except: pass
                                bt=""
                                if btr!=-1 and len(row)>btr and row[btr]:
                                    bt=str(row[btr]).replace('\n',' ').strip()
                                raw.append({'proje_no':pno,'adet':adet,'basvuru_turu':bt})

        grouped={}
        for item in raw:
            pfx=item['proje_no'].split('-')[0].upper()
            is_tas=any(k in item['basvuru_turu'].upper() for k in ('TAS','TAMİR','TAMIR'))
            key=f"{pfx}_{'TAS' if is_tas else 'PER'}"
            if key not in grouped: grouped[key]={'prefix':pfx,'is_tas':is_tas,'adet':0}
            grouped[key]['adet']+=item['adet']

        MAP={
            'AKR':('Akaryakıt_LPG_Adblue_Dispenserleri','Mak. Akış Hızı 130 L/dk-100 kg/dk Kadar-({})'),
            'LHB':('Lastik_Hava_Basınçölçerler','Lastik Hava Basınçölçerler'),
            'TNK':('Tanker_Sayaçları','Tanker Sayaçları-({})'),
            'TRT':('Tartı_Aletleri','Tartı Aletleri-({})'),
        }
        for val in grouped.values():
            sfx='TAS' if val['is_tas'] else 'Periyodik, Stok'
            adi,bil=MAP.get(val['prefix'],(val['prefix'],val['prefix']))
            data['items'].append({'adi':adi,'bilgisi':bil.format(sfx) if '{}' in bil else bil,'adet':val['adet']})

        if not data['items']:
            data['items'].append({'adi':'Bulunamadı','bilgisi':'Bulunamadı','adet':1})

    return data

import zipfile
import html
import subprocess

def set_cell_xml(sheet_xml, cell_ref, value, is_number=False, style=None):
    if value is None:
        value = ""
    val_str = str(value)
    escaped = html.escape(val_str)
    
    pattern = rf'<c\s+r="{cell_ref}"([^>]*?)(?:/>|>(.*?)</c>)'
    match = re.search(pattern, sheet_xml)
    if match:
        attrs = match.group(1)
        s_match = re.search(r's="(\d+)"', attrs)
        s_attr = f's="{s_match.group(1)}"' if s_match else (f's="{style}"' if style else '')
        
        if is_number and val_str != "":
            new_cell = f'<c r="{cell_ref}" {s_attr}><v>{escaped}</v></c>'
        elif val_str == "":
            new_cell = f'<c r="{cell_ref}" {s_attr}/>'
        else:
            new_cell = f'<c r="{cell_ref}" {s_attr} t="inlineStr"><is><t>{escaped}</t></is></c>'
            
        sheet_xml = sheet_xml[:match.start()] + new_cell + sheet_xml[match.end():]
    else:
        row_num = ''.join(filter(str.isdigit, cell_ref))
        row_pattern = rf'(<row\s+r="{row_num}"[^>]*>)'
        s_attr = f's="{style}"' if style else ''
        if is_number and val_str != "":
            new_cell = f'<c r="{cell_ref}" {s_attr}><v>{escaped}</v></c>'
        else:
            new_cell = f'<c r="{cell_ref}" {s_attr} t="inlineStr"><is><t>{escaped}</t></is></c>'
            
        sheet_xml = re.sub(row_pattern, rf'\1{new_cell}', sheet_xml, count=1)
        
    return sheet_xml

def fill_template_lossless(template_path, output_path, data):
    """Excel şablonundaki kırmızı başlık, logo, VML çizimleri ve formülleri %100 koruyarak hücreleri günceller."""
    with zipfile.ZipFile(template_path, 'r') as zin:
        sheet_xml = zin.read('xl/worksheets/sheet1.xml').decode('utf-8')
        
        # _x000a_ kaçış karakterlerini temizle
        sheet_xml = sheet_xml.replace('_x000a_', '\n')
        
        # Başlık ve firma bilgileri
        sheet_xml = set_cell_xml(sheet_xml, 'C2', data.get('evrak_no', ''))
        if data.get('basvuru_yili'):
            sheet_xml = set_cell_xml(sheet_xml, 'C3', data.get('basvuru_yili'), is_number=True)
        sheet_xml = set_cell_xml(sheet_xml, 'C4', data.get('firma_adi', ''))
        if 'tamir_ayar_firmasi' in data:
            sheet_xml = set_cell_xml(sheet_xml, 'C5', data.get('tamir_ayar_firmasi', ''))
        sheet_xml = set_cell_xml(sheet_xml, 'C6', data.get('fatura_adresi', ''))
        sheet_xml = set_cell_xml(sheet_xml, 'C7', data.get('telefon', ''))
        sheet_xml = set_cell_xml(sheet_xml, 'C8', data.get('eposta', ''))
        sheet_xml = set_cell_xml(sheet_xml, 'C9', f"{data.get('vergi_dairesi','')} - {data.get('vergi_no','')}")
        
        # Kalemler (Ölçü Aletleri)
        items = data.get('items', [])
        for i in range(8):
            row = 12 + i
            if i < len(items):
                item = items[i]
                sheet_xml = set_cell_xml(sheet_xml, f'B{row}', item.get('adi', ''))
                sheet_xml = set_cell_xml(sheet_xml, f'C{row}', item.get('bilgisi', ''))
                sheet_xml = set_cell_xml(sheet_xml, f'E{row}', item.get('adet', 1), is_number=True)
            else:
                # Boş kalan satırları temizle
                sheet_xml = set_cell_xml(sheet_xml, f'B{row}', '')
                sheet_xml = set_cell_xml(sheet_xml, f'C{row}', '')
                sheet_xml = set_cell_xml(sheet_xml, f'E{row}', '')
            
        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == 'xl/worksheets/sheet1.xml':
                    zout.writestr(item.filename, sheet_xml.encode('utf-8'))
                else:
                    zout.writestr(item.filename, zin.read(item.filename))

# ─── EXCEL VE PDF YAZMA (ÇAPRAZ PLATFORM: WINDOWS & LINUX) ────────────────────
def process_excel(template_path, out_excel, out_pdf, data):
    # 1. Kayıpsız XML şablon doldurma ile Excel oluştur (TSE Kırmızı Başlığı ve Logolar %100 korunur)
    fill_template_lossless(template_path, out_excel, data)

    # 2. PDF Dönüştürme (Windows için Excel COM, Linux için LibreOffice)
    pdf_converted = False
    if WIN32_AVAILABLE:
        try:
            import pythoncom
            pythoncom.CoInitialize()
            excel = win32com.client.DispatchEx("Excel.Application")
            excel.Visible = False; excel.DisplayAlerts = False
            wb_com = excel.Workbooks.Open(os.path.abspath(out_excel))
            wb_com.ActiveSheet.ExportAsFixedFormat(0, os.path.abspath(out_pdf))
            wb_com.Close(False)
            excel.Quit()
            pythoncom.CoUninitialize()
            pdf_converted = True
        except Exception as e:
            pass

    # Eğer Windows COM yoksa veya başarısız olursa (Linux ortamı için LibreOffice)
    if not pdf_converted:
        # LibreOffice'i birden fazla olası yoldan dene
        soffice_paths = [
            "soffice",
            "/usr/bin/soffice",
            "/usr/lib/libreoffice/program/soffice",
            "/opt/libreoffice/program/soffice",
        ]
        last_err = None
        for soffice_bin in soffice_paths:
            try:
                cmd = [
                    soffice_bin, "--headless", "--convert-to", "pdf",
                    "--outdir", os.path.dirname(os.path.abspath(out_pdf)),
                    os.path.abspath(out_excel)
                ]
                result = subprocess.run(
                    cmd, check=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    timeout=60
                )
                # LibreOffice bazen çıktı dosyasını farklı isimle oluşturur
                # (xlsx → xlsx.pdf yerine xlsx adıyla) — kontrol edelim
                expected_pdf = os.path.abspath(out_pdf)
                lo_pdf = os.path.splitext(os.path.abspath(out_excel))[0] + ".pdf"
                if not os.path.exists(expected_pdf) and os.path.exists(lo_pdf):
                    os.rename(lo_pdf, expected_pdf)
                pdf_converted = True
                break
            except FileNotFoundError:
                last_err = f"{soffice_bin} bulunamadı"
                continue
            except subprocess.TimeoutExpired:
                last_err = "PDF dönüşümü zaman aşımına uğradı"
                break
            except subprocess.CalledProcessError as e:
                last_err = e.stderr.decode(errors='ignore') if e.stderr else str(e)
                break

        if not pdf_converted:
            raise RuntimeError(
                f"PDF oluşturulamadı — LibreOffice kurulu değil veya hata verdi. "
                f"Detay: {last_err}"
            )


# ─── IP BAZLI KOTA TAKIBI (veritabanı gerektirmiyor) ──────────────────────────
ip_quota = {}   # { ip: {'used': int, 'bonus': int, 'date': str} }

def get_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

def get_quota():
    """Kullanıcının günlük kota bilgisini döndürür."""
    ip    = get_ip()
    today = datetime.utcnow().strftime('%Y-%m-%d')
    if ip not in ip_quota or ip_quota[ip]['date'] != today:
        ip_quota[ip] = {'used': 0, 'bonus': 0, 'date': today}
    return ip_quota[ip]

def remaining_quota():
    q = get_quota()
    return max(0, FREE_LIMIT + q['bonus'] - q['used'])

# ─── ROTALAR ───────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('upload.html',
                           adsense_client=ADSENSE_CLIENT,
                           adsense_slot_left=ADSENSE_SLOT_LEFT,
                           adsense_slot_right=ADSENSE_SLOT_RIGHT,
                           remaining=remaining_quota(),
                           free_limit=FREE_LIMIT,
                           ad_reward=AD_REWARD_COUNT)

@app.route('/upload')
def upload():
    return redirect(url_for('index'))

# ─ Reklam izleme: bonus hak ver ─────────────────────────────────────────────
@app.route('/api/ad_reward', methods=['POST'])
def api_ad_reward():
    """Reklam izlendikten sonra çağrılır; IP'ye bonus hak ekler."""
    q = get_quota()
    q['bonus'] += AD_REWARD_COUNT
    return jsonify({'remaining': remaining_quota(), 'added': AD_REWARD_COUNT})

@app.route('/api/quota')
def api_quota():
    return jsonify({'remaining': remaining_quota(), 'free_limit': FREE_LIMIT})

@app.route('/api/process', methods=['POST'])
def api_process():
    # Kota kontrolü
    if remaining_quota() <= 0:
        return jsonify({'error': 'limit_exceeded', 'remaining': 0}), 429

    if 'pdf_files' not in request.files:
        return jsonify({'error': 'Dosya seçilmedi'}), 400

    files = request.files.getlist('pdf_files')
    if not files or all(f.filename == '' for f in files):
        return jsonify({'error': 'Dosya seçilmedi'}), 400

    job_id   = str(uuid.uuid4())[:8]
    job_dir  = os.path.join(OUTPUT_FOLDER, job_id)
    os.makedirs(job_dir, exist_ok=True)

    # Excel şablonu kontrolü
    custom_template = request.files.get('excel_template')
    template_to_use = TEMPLATE_PATH
    temp_template_path = None

    if custom_template and custom_template.filename != '':
        temp_template_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_template.xlsx")
        custom_template.save(temp_template_path)
        template_to_use = temp_template_path
    elif not os.path.exists(TEMPLATE_PATH):
        return jsonify({'error': 'Sunucuda Excel şablonu bulunamadı ve şablon yüklenmedi.'}), 400

    results  = []
    errors   = []

    for f in files:
        if not allowed_file(f.filename):
            errors.append(f"{f.filename}: PDF değil")
            continue

        safe   = secure_filename(f.filename)
        in_pdf = os.path.join(UPLOAD_FOLDER, f"{job_id}_{safe}")
        f.save(in_pdf)

        try:
            data      = extract_data_from_pdf(in_pdf)
            clean     = "".join(c for c in data['firma_adi'] if c.isalnum() or c in ' _-').strip().replace(' ','_')[:30]
            base      = f"Fatura_{data['evrak_no']}_{clean}"
            out_excel = os.path.join(job_dir, f"{base}.xlsx")
            out_pdf   = os.path.join(job_dir, f"{base}.pdf")

            process_excel(template_to_use, out_excel, out_pdf, data)
            results.append({'pdf': f"{base}.pdf", 'excel': f"{base}.xlsx", 'firma': data['firma_adi']})
        except Exception as e:
            errors.append(f"{safe}: {str(e)}")
        finally:
            try: os.remove(in_pdf)
            except: pass

    if temp_template_path and os.path.exists(temp_template_path):
        try: os.remove(temp_template_path)
        except: pass

    # Kota düşüşü
    if results:
        q = get_quota()
        q['used'] += len(results)

    return jsonify({'job_id': job_id, 'results': results, 'errors': errors, 'remaining': remaining_quota()})

@app.route('/result/<job_id>')
def result(job_id):
    job_dir = os.path.join(OUTPUT_FOLDER, job_id)
    if not os.path.exists(job_dir):
        abort(404)
    files = os.listdir(job_dir)
    return render_template('result.html', job_id=job_id, files=files,
                           user=None,
                           adsense_client=ADSENSE_CLIENT, adsense_slot=ADSENSE_SLOT)

@app.route('/download/<job_id>/<filename>')
def download(job_id, filename):
    safe_filename = os.path.basename(filename)
    file_path = os.path.abspath(os.path.join(OUTPUT_FOLDER, job_id, safe_filename))
    if not file_path.startswith(os.path.abspath(OUTPUT_FOLDER)):
        abort(403)
    if not os.path.exists(file_path):
        abort(404)
    return send_file(file_path, as_attachment=True, download_name=safe_filename)

@app.route('/pricing')
def pricing():
    return render_template('pricing.html',
                           user=current_user if current_user.is_authenticated else None)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        pw    = request.form.get('password','')
        user  = User.query.filter_by(email=email).first()
        if user and user.check_password(pw):
            login_user(user)
            return redirect(url_for('upload'))
        flash('E-posta veya şifre hatalı.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('upload'))
    if request.method == 'POST':
        email = request.form.get('email','').strip().lower()
        pw    = request.form.get('password','')
        if User.query.filter_by(email=email).first():
            flash('Bu e-posta zaten kayıtlı.', 'error')
        elif len(pw) < 6:
            flash('Şifre en az 6 karakter olmalı.', 'error')
        else:
            u = User(email=email)
            u.set_password(pw)
            db.session.add(u)
            db.session.commit()
            login_user(u)
            return redirect(url_for('upload'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ─── BAŞLAT ──────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
