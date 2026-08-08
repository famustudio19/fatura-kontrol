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

def set_formula_cell_xml(sheet_xml, cell_ref, formula, value, style=None):
    """Formula ve hesaplanmış değeri XML'e kayıpsız yazar."""
    pattern = rf'<c\s+r="{cell_ref}"([^>]*?)(?:/>|>(.*?)</c>)'
    match = re.search(pattern, sheet_xml, re.DOTALL)
    
    val_str = "" if value is None or value == "" else str(value)
    if isinstance(value, float) and value.is_integer():
        val_str = str(int(value))
    v_tag = f"<v>{html.escape(val_str)}</v>" if val_str != "" else ""
    f_tag = f"<f>{html.escape(formula)}</f>" if formula else ""
    
    if match:
        attrs = match.group(1)
        s_match = re.search(r's="(\d+)"', attrs)
        s_attr = f's="{s_match.group(1)}"' if s_match else (f's="{style}"' if style else '')
        
        if not f_tag and not v_tag:
            new_cell = f'<c r="{cell_ref}" {s_attr}/>'
        else:
            new_cell = f'<c r="{cell_ref}" {s_attr}>{f_tag}{v_tag}</c>'
        sheet_xml = sheet_xml[:match.start()] + new_cell + sheet_xml[match.end():]
    return sheet_xml

def load_price_lookup(template_path):
    """Excel şablonundaki Veriler sayfasından tüm fiyat tablosunu dinamik okur."""
    lookup = {}
    try:
        with zipfile.ZipFile(template_path, 'r') as z:
            if 'xl/worksheets/sheet2.xml' not in z.namelist():
                return lookup
            sheet2 = z.read('xl/worksheets/sheet2.xml').decode('utf-8')
            ss = z.read('xl/sharedStrings.xml').decode('utf-8') if 'xl/sharedStrings.xml' in z.namelist() else ""
            strings = re.findall(r'<si>.*?</si>', ss, re.DOTALL)
            
            def get_str(idx):
                if idx < len(strings):
                    m = re.search(r'<t[^>]*>(.*?)</t>', strings[idx])
                    return m.group(1) if m else ''
                return ''

            rows = re.findall(r'<row r="(\d+)"[^>]*>(.*?)</row>', sheet2, re.DOTALL)
            for r_num, r_content in rows:
                cells = re.findall(r'<c r="([A-Z]+\d+)"([^>]*)(?:/>|>(.*?)</c>)', r_content, re.DOTALL)
                c_val = d_val = e_val = ""
                for ref, attrs, val in cells:
                    v_match = re.search(r'<v>(.*?)</v>', val) if val else None
                    v = v_match.group(1) if v_match else ''
                    if 't="s"' in attrs:
                        try: v = get_str(int(v))
                        except: pass
                    col = re.match(r'([A-Z]+)', ref).group(1)
                    if col == 'C': c_val = v.strip()
                    elif col == 'D': d_val = v.strip()
                    elif col == 'E': e_val = v.strip()
                
                if c_val:
                    try:
                        p25 = float(d_val) if d_val else 0.0
                        p26 = float(e_val) if e_val else 0.0
                        if p25 > 0 or p26 > 0:
                            lookup[c_val] = {2025: p25, 2026: p26}
                    except ValueError:
                        pass
    except Exception as e:
        print(f"Fiyat tablosu okuma uyarısı: {e}")
    return lookup

def fill_template_lossless(template_path, output_path, data):
    """Excel şablonundaki kırmızı başlık, logo, formüller ve fiyatları %100 doğrulukla işler."""
    price_lookup = load_price_lookup(template_path)
    
    with zipfile.ZipFile(template_path, 'r') as zin:
        sheet_xml = zin.read('xl/worksheets/sheet1.xml').decode('utf-8')
        wb_xml = zin.read('xl/workbook.xml').decode('utf-8') if 'xl/workbook.xml' in zin.namelist() else ""
        
        # _x000a_ kaçış karakterlerini temizle
        sheet_xml = sheet_xml.replace('_x000a_', '\n')
        
        # 1. Başvuru Yılı
        yil = data.get('basvuru_yili')
        try: yil = int(yil) if yil else 2026
        except: yil = 2026
        
        # 2. Başlık ve firma bilgileri
        sheet_xml = set_cell_xml(sheet_xml, 'C2', data.get('evrak_no', ''))
        sheet_xml = set_cell_xml(sheet_xml, 'C3', yil, is_number=True)
        sheet_xml = set_cell_xml(sheet_xml, 'C4', data.get('firma_adi', ''))
        if 'tamir_ayar_firmasi' in data:
            sheet_xml = set_cell_xml(sheet_xml, 'C5', data.get('tamir_ayar_firmasi', ''))
        sheet_xml = set_cell_xml(sheet_xml, 'C6', data.get('fatura_adresi', ''))
        sheet_xml = set_cell_xml(sheet_xml, 'C7', data.get('telefon', ''))
        sheet_xml = set_cell_xml(sheet_xml, 'C8', data.get('eposta', ''))
        sheet_xml = set_cell_xml(sheet_xml, 'C9', f"{data.get('vergi_dairesi','')} - {data.get('vergi_no','')}")
        
        # 3. Kalemler ve Fiyat Hesaplamaları
        items = data.get('items', [])
        toplam_tutar = 0.0
        
        for i in range(8):
            row = 12 + i
            f_formula = f'IF($C$3="","",IFERROR(VLOOKUP(C{row},Veriler!$C$2:$E$53,IF($C$3=Veriler!$A$2,2,3),0),""))'
            h_formula = f'IF(OR(E{row}="",F{row}=""),"",E{row}*F{row})'
            
            if i < len(items):
                item = items[i]
                adi = item.get('adi', '')
                bilgisi = item.get('bilgisi', '')
                adet = item.get('adet', 1)
                try: adet = int(adet)
                except: adet = 1
                
                # Fiyatı bul
                birim_fiyat = 0.0
                if bilgisi in price_lookup:
                    birim_fiyat = price_lookup[bilgisi].get(yil, price_lookup[bilgisi].get(2026, 0.0))
                else:
                    # Kısmi eşleşme dene
                    for k, v in price_lookup.items():
                        if k in bilgisi or bilgisi in k:
                            birim_fiyat = v.get(yil, v.get(2026, 0.0))
                            break
                
                ara_toplam = adet * birim_fiyat
                toplam_tutar += ara_toplam
                
                sheet_xml = set_cell_xml(sheet_xml, f'B{row}', adi)
                sheet_xml = set_cell_xml(sheet_xml, f'C{row}', bilgisi)
                sheet_xml = set_cell_xml(sheet_xml, f'E{row}', adet, is_number=True)
                sheet_xml = set_formula_cell_xml(sheet_xml, f'F{row}', f_formula, birim_fiyat)
                sheet_xml = set_formula_cell_xml(sheet_xml, f'H{row}', h_formula, ara_toplam)
            else:
                # Boş satırlar
                sheet_xml = set_cell_xml(sheet_xml, f'B{row}', '')
                sheet_xml = set_cell_xml(sheet_xml, f'C{row}', '')
                sheet_xml = set_cell_xml(sheet_xml, f'E{row}', '')
                sheet_xml = set_formula_cell_xml(sheet_xml, f'F{row}', f_formula, '')
                sheet_xml = set_formula_cell_xml(sheet_xml, f'H{row}', '', '')
        
        # 4. Alt Toplamlar ve Dipnot
        dipnot_metin = f"* Bu formda yer alan muayene ücretleri {yil} yılında yapılan muayene başvuruları için geçerlidir. Lütfen başvuru yılının doğruluğundan emin olunuz."
        dipnot_formula = f'CONCATENATE("* Bu formda yer alan muayene ücretleri ",IF(C3="","...",C3)," yılında yapılan muayene başvuruları için geçerlidir. Lütfen başvuru yılının doğruluğundan emin olunuz.")'
        sheet_xml = set_formula_cell_xml(sheet_xml, 'A20', dipnot_formula, dipnot_metin)
        
        kdv = toplam_tutar * 0.20
        genel_toplam = toplam_tutar + kdv
        
        sheet_xml = set_formula_cell_xml(sheet_xml, 'F20', 'IF(F12="","",SUM(H12:H19))', toplam_tutar)
        sheet_xml = set_formula_cell_xml(sheet_xml, 'F21', 'IF(H20="","",H20*0.2)', kdv)
        sheet_xml = set_formula_cell_xml(sheet_xml, 'F22', 'IF(H20="","",H20+H21)', genel_toplam)
        
        # 5. Workbook XML - Excel açılışında zorunlu yeniden hesaplama
        if wb_xml:
            if '<calcPr' in wb_xml:
                wb_xml = re.sub(r'<calcPr[^>]*/>', '<calcPr calcId="0" fullCalcOnLoad="1" forceFullCalc="1"/>', wb_xml)
            else:
                wb_xml = wb_xml.replace('</workbook>', '<calcPr calcId="0" fullCalcOnLoad="1" forceFullCalc="1"/></workbook>')

        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == 'xl/worksheets/sheet1.xml':
                    zout.writestr(item.filename, sheet_xml.encode('utf-8'))
                elif item.filename == 'xl/workbook.xml' and wb_xml:
                    zout.writestr(item.filename, wb_xml.encode('utf-8'))
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
            excel.EnableEvents = True
            wb_com = excel.Workbooks.Open(os.path.abspath(out_excel))
            sh = wb_com.ActiveSheet

            # Tüm formülleri (VLOOKUP fiyat tablosu dahil) sıfırdan yeniden hesapla
            wb_com.Application.Calculate()
            wb_com.Application.CalculateFull()
            wb_com.Application.CalculateFullRebuild()

            # Yazdırma alanını temizle ve sayfa ayarlarını düzenle (kırmızı başlık dahil)
            try: sh.PageSetup.PrintArea = ""
            except: pass
            try:
                ps = sh.PageSetup
                ps.TopMargin = excel.InchesToPoints(0.3)
                ps.BottomMargin = excel.InchesToPoints(0.3)
                ps.LeftMargin = excel.InchesToPoints(0.25)
                ps.RightMargin = excel.InchesToPoints(0.25)
                ps.Zoom = False
                ps.FitToPagesWide = 1
                ps.FitToPagesTall = 1
                ps.PrintGridlines = False
            except: pass

            sh.ExportAsFixedFormat(0, os.path.abspath(out_pdf))
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

    # 3. PDF'in en üstüne kırmızı TSE başlığını damgala (LibreOffice VML desteklemediği için bu adım PDF'te başlığı %100 garanti eder)
    if pdf_converted and os.path.exists(out_pdf):
        stamp_pdf_banner(out_pdf, template_path)

def stamp_pdf_banner(pdf_path, template_path):
    """
    PDF'deki 'FATURA DETAYI' satırının üstüne kadar olan header alanını
    dinamik olarak tespit eder ve kırmızı banner + başlık metnini Excel'in
    orijinal piksel ve tipografi oranlarıyla yüksek çözünürlükte enjekte eder.
    'FATURA DETAYI' tablosunun üstünde orijinal nefes payı (boşluk) tam korunur.
    """
    try:
        import pypdfium2 as pdfium
        from PIL import Image, ImageDraw, ImageFont
        import io

        with zipfile.ZipFile(template_path, 'r') as z:
            banner_bytes = z.read('xl/media/image2.png')

        banner_pil = Image.open(io.BytesIO(banner_bytes)).convert('RGB')

        pdf = pdfium.PdfDocument(pdf_path)
        if len(pdf) == 0:
            return

        page = pdf[0]
        page_width  = page.get_width()   # A4 ~595.28 pt
        page_height = page.get_height()  # A4 ~841.92 pt

        # ── "FATURA DETAYI" metninin gerçek TABLO konumunu bul ───────────────
        header_height_pts = 1.5748031496063 * 72   # varsayılan üst kenar boşluğu (~113.4 pt)
        try:
            textpage = page.get_textpage()
            searcher = textpage.search('FATURA DETAYI', match_case=True)
            best_y = None  # en alttaki (tablo içindeki) eşleşme
            for _ in range(10):
                match = searcher.get_next()
                if not match:
                    break
                idx = match[0]
                box = textpage.get_charbox(idx, loose=False)
                y_from_top = page_height - box[3]
                if 10 < y_from_top < 200:
                    if best_y is None or y_from_top > best_y:
                        best_y = y_from_top
            if best_y is not None:
                # Tablo üst kenarı metin tabanından ~8.8 pt yukarıdadır
                header_height_pts = max(best_y - 8.8, 60)
        except Exception as e:
            print(f"Text search error (fallback to margin): {e}")

        # ── Kompozit görsel oluştur: banner + başlık metni ──────────────────────
        SCALE = 4   # 288 DPI -> kristal netliğinde vektörel kalite
        img_w = int(page_width  * SCALE)
        img_h = int(header_height_pts * SCALE)

        composite = Image.new('RGB', (img_w, img_h), 'white')

        # Kırmızı banner (orijinal VML en-boy oranı: 842.25 x 69 pt)
        banner_h_pt = page_width * (69.0 / 842.25)  # ~48.8 pt
        banner_h_px = int(banner_h_pt * SCALE)
        composite.paste(
            banner_pil.resize((img_w, banner_h_px), Image.Resampling.LANCZOS),
            (0, 0)
        )

        # Başlık metni (Times New Roman Kalın, 9.5-10 pt)
        draw = ImageDraw.Draw(composite)
        font_size_px = int(9.5 * SCALE)
        font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        font = None
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    font = ImageFont.truetype(fp, size=font_size_px)
                    break
                except Exception:
                    pass
        if font is None:
            font = ImageFont.load_default()

        text1 = "MUAYENE GÖZETİM MERKEZİ BAŞKANLIĞI"
        text2 = "ÖLÇÜ ALETLERİ FATURA DETAYI FORMU"
        bb1 = draw.textbbox((0, 0), text1, font=font)
        w1  = bb1[2] - bb1[0]
        bb2 = draw.textbbox((0, 0), text2, font=font)
        w2  = bb2[2] - bb2[0]

        # Excel orijinal konumu: banner bitiminden sonra sırasıyla 7.5 pt ve 18.5 pt
        y1_px = int((banner_h_pt + 7.5) * SCALE)
        y2_px = int((banner_h_pt + 7.5 + 11.0) * SCALE)

        draw.text(((img_w - w1) / 2, y1_px), text1, fill="black", font=font)
        draw.text(((img_w - w2) / 2, y2_px), text2, fill="black", font=font)

        # ── PDF image nesnesi olarak enjekte et ─────────────────────────────────
        pdf_image = pdfium.PdfImage.new(pdf)
        pdf_image.set_bitmap(pdfium.PdfBitmap.from_pil(composite))

        # PDF koord: sol-alt orijin, y yukarı; header alanı sayfanın üstünde
        pdf_image.set_matrix(pdfium.PdfMatrix(
            page_width, 0,
            0, header_height_pts,
            0, page_height - header_height_pts
        ))
        page.insert_obj(pdf_image)
        page.gen_content()
        pdf.save(pdf_path)
        pdf.close()
    except Exception as e:
        print(f"PDF stamp hatası: {e}")








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

@app.route('/ads.txt')
def ads_txt():
    return send_file(os.path.join(BASE_DIR, 'static', 'ads.txt'), mimetype='text/plain')

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
