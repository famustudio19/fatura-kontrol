import os, re, glob, json, uuid, time, traceback, threading, shutil
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

# PDF damgalama için zorunlu bağımlılıklar (eksikse başlık sessizce kaybolmasın)
try:
    import pypdfium2 as _pdfium
    from PIL import Image as _PILImage
    STAMP_AVAILABLE = True
except ImportError:
    STAMP_AVAILABLE = False

# ─── UYGULAMA YAPISI ─────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER  = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER  = os.path.join(BASE_DIR, 'outputs')
TEMPLATE_PATH  = os.path.join(BASE_DIR, 'FATURA2026.xlsx')   # Şablonu buraya koy
BANNER_FALLBACK = os.path.join(BASE_DIR, 'tse_banner.png')   # Şablonda yoksa kullanılacak PNG

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'TSE-FATURA-SECRET-2026-LOCAL-ONLY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

ADSENSE_CLIENT = 'ca-pub-6336356250153811'  # Google AdSense Yayıncı ID'niz
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

        # Adreste il (şehir) eksikse otomatik tespit edip ekle (Keşan -> Keşan / EDİRNE)
        try:
            from turkey_geo import enrich_address_with_city
            data["fatura_adresi"] = enrich_address_with_city(
                data.get("fatura_adresi", ""),
                data.get("vergi_dairesi", ""),
                full
            )
        except Exception as e:
            pass

        raw = []
        for p in pdf.pages:
            for table in p.extract_tables():
                hi=prj=tab=btr=-1
                for i, row in enumerate(table):
                    rc=[str(c).replace('\n',' ').strip() if c else '' for c in row]
                    joined=' '.join(rc)
                    if 'Proje Kay' in joined:
                        hi=i
                        for j,cell in enumerate(rc):
                            if 'Proje Kay' in cell: prj=j
                            elif 'Tabanca' in cell or 'Saya' in cell: tab=j
                            # Başvuru Türü sütununu çeşitli yazım biçimleriyle yakala
                            elif any(k in cell for k in ('Türü','Türü','Turu','Tür','Basvuru','Başvuru','Muayene Tür')): btr=j
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

        # Tüm PDF metninden de TAS tespiti yap (tablo sütunu bulunamasa bile)
        full_text_upper = full.upper() if full else ''
        full_text_is_tas = any(k in full_text_upper for k in (
            'TAMİR AYAR SONRASI', 'TAMIR AYAR SONRASI', 'TAS İLK', 'TAS ILK',
            'BAŞVURU TÜRÜ: TAS', 'BASVURU TURU: TAS',
            'TAMİR-AYAR', 'TAMIR-AYAR'
        ))

        grouped={}
        for item in raw:
            pfx=item['proje_no'].split('-')[0].upper()
            # Hem satır bazlı başvuru türü hem de tam metin tespitine bak
            is_tas=(
                any(k in item['basvuru_turu'].upper() for k in ('TAS','TAMİR','TAMIR','TAMIR AYAR','TAMİR AYAR'))
                or (item['basvuru_turu'] == '' and full_text_is_tas)
            )
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

def update_cell_value_only(sheet_xml, cell_ref, value):
    """Mevcut hücrenin formülünü ve stilini %100 koruyup sadece <v> hesaplanmış değerini günceller."""
    pattern = rf'<c\s+r="{cell_ref}"([^>]*?)(?:/>|>(.*?)</c>)'
    match = re.search(pattern, sheet_xml, re.DOTALL)
    if not match:
        return sheet_xml
    
    attrs = match.group(1)
    inner = match.group(2) if match.group(2) else ""
    
    val_str = "" if value is None or value == "" else str(value)
    if isinstance(value, float) and value.is_integer():
        val_str = str(int(value))
        
    v_tag = f"<v>{html.escape(val_str)}</v>" if val_str != "" else "<v/>"
    
    if "<f" in inner:
        f_match = re.search(r'(<f[^>]*>.*?</f>)', inner, re.DOTALL)
        if f_match:
            f_tag = f_match.group(1)
            clean_attrs = re.sub(r'\s*t="(?:s|str|inlineStr)"', '', attrs)
            new_inner = f"{f_tag}{v_tag}"
            new_cell = f'<c r="{cell_ref}"{clean_attrs}>{new_inner}</c>'
            sheet_xml = sheet_xml[:match.start()] + new_cell + sheet_xml[match.end():]
            return sheet_xml
            
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
    """Excel şablonundaki kırmızı başlık, logo, formüller ve fiyatları %100 hatasız işler."""
    price_lookup = load_price_lookup(template_path)
    
    with zipfile.ZipFile(template_path, 'r') as zin:
        sheet_xml = zin.read('xl/worksheets/sheet1.xml').decode('utf-8')
        rels_xml = zin.read('xl/_rels/workbook.xml.rels').decode('utf-8') if 'xl/_rels/workbook.xml.rels' in zin.namelist() else ""
        ct_xml = zin.read('[Content_Types].xml').decode('utf-8') if '[Content_Types].xml' in zin.namelist() else ""
        
        # calcChain.xml referanslarını temizle (Excel onarım uyarısı vermemesi için)
        if rels_xml:
            rels_xml = re.sub(r'<Relationship[^>]*Target="calcChain\.xml"[^>]*/>', '', rels_xml)
        if ct_xml:
            ct_xml = re.sub(r'<Override[^>]*PartName="/xl/calcChain\.xml"[^>]*/>', '', ct_xml)
        
        # _x000a_ kaçış karakterlerini temizle
        sheet_xml = sheet_xml.replace('_x000a_', '\n')
        
        # Üst bilgi (header) ve kenar boşluklarını evrensel standartta garanti et
        clean_header = (
            '<oddHeader>&amp;C&amp;G\r\n'
            '&amp;B&amp;"Times New Roman"&amp;10&amp;K000000MUAYENE GÖZETİM MERKEZİ BAŞKANLIĞI\r\n'
            'ÖLÇÜ ALETLERİ FATURA DETAYI FORMU</oddHeader>'
        )
        sheet_xml = re.sub(r'<oddHeader>.*?</oddHeader>', clean_header, sheet_xml, flags=re.DOTALL)
        sheet_xml = re.sub(r'top="[\d\.]+"', 'top="1.5748031496063"', sheet_xml)
        sheet_xml = re.sub(r'header="[\d\.]+"', 'header="0.118110236220472"', sheet_xml)
        
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
                    for k, v in price_lookup.items():
                        if k in bilgisi or bilgisi in k:
                            birim_fiyat = v.get(yil, v.get(2026, 0.0))
                            break
                
                ara_toplam = adet * birim_fiyat
                toplam_tutar += ara_toplam
                
                sheet_xml = set_cell_xml(sheet_xml, f'B{row}', adi)
                sheet_xml = set_cell_xml(sheet_xml, f'C{row}', bilgisi)
                sheet_xml = set_cell_xml(sheet_xml, f'E{row}', adet, is_number=True)
                sheet_xml = update_cell_value_only(sheet_xml, f'F{row}', birim_fiyat)
                sheet_xml = update_cell_value_only(sheet_xml, f'H{row}', ara_toplam)
            else:
                # Boş satırlar
                sheet_xml = set_cell_xml(sheet_xml, f'B{row}', '')
                sheet_xml = set_cell_xml(sheet_xml, f'C{row}', '')
                sheet_xml = set_cell_xml(sheet_xml, f'E{row}', '')
                sheet_xml = update_cell_value_only(sheet_xml, f'F{row}', '')
                sheet_xml = update_cell_value_only(sheet_xml, f'H{row}', '')
        
        # 4. Alt Toplamlar ve Dipnot (H20: Toplam, H21: KDV, H22: Genel Toplam)
        dipnot_metin = f"* Bu formda yer alan muayene ücretleri {yil} yılında yapılan muayene başvuruları için geçerlidir. Lütfen başvuru yılının doğruluğundan emin olunuz."
        m_a20 = re.search(r'<c\s+r="A20"([^>]*?)>(.*?)</c>', sheet_xml, re.DOTALL)
        if m_a20:
            f_a20 = re.search(r'(<f[^>]*>.*?</f>)', m_a20.group(2))
            if f_a20:
                new_a20 = f'<c r="A20"{m_a20.group(1)}>{f_a20.group(1)}<v>{html.escape(dipnot_metin)}</v></c>'
                sheet_xml = sheet_xml[:m_a20.start()] + new_a20 + sheet_xml[m_a20.end():]
        
        kdv = toplam_tutar * 0.20
        genel_toplam = toplam_tutar + kdv
        
        sheet_xml = update_cell_value_only(sheet_xml, 'H20', toplam_tutar)
        sheet_xml = update_cell_value_only(sheet_xml, 'H21', kdv)
        sheet_xml = update_cell_value_only(sheet_xml, 'H22', genel_toplam)

        with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == 'xl/worksheets/sheet1.xml':
                    zout.writestr(item, sheet_xml.encode('utf-8'))
                elif item.filename == 'xl/_rels/workbook.xml.rels' and rels_xml:
                    zout.writestr(item, rels_xml.encode('utf-8'))
                elif item.filename == '[Content_Types].xml' and ct_xml:
                    zout.writestr(item, ct_xml.encode('utf-8'))
                elif item.filename == 'xl/calcChain.xml':
                    continue
                else:
                    zout.writestr(item, zin.read(item.filename))

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

            # Üst bilgi formatını evrensel &B formatında ve doğru kenar boşluğuyla ayarla
            try:
                sh.PageSetup.CenterHeader = (
                    "&G\n&B&\"Times New Roman\"&10&K000000MUAYENE GÖZETİM MERKEZİ BAŞKANLIĞI\n"
                    "ÖLÇÜ ALETLERİ FATURA DETAYI FORMU"
                )
                sh.PageSetup.TopMargin = excel.InchesToPoints(1.575)
                sh.PageSetup.HeaderMargin = excel.InchesToPoints(0.12)
                try:
                    excel.ActiveWindow.View = 3  # xlPageLayoutView (üst bilginin PDF'e çıkmasını sağlar)
                except:
                    pass
            except:
                pass

            sh.ExportAsFixedFormat(0, os.path.abspath(out_pdf))
            wb_com.Save()
            wb_com.Close(False)
            excel.Quit()
            pythoncom.CoUninitialize()
            pdf_converted = True
        except Exception as e:
            print(f"Excel COM PDF dönüşümü başarısız, LibreOffice denenecek: {e}")
            traceback.print_exc()

    # Eğer Windows COM yoksa veya başarısız olursa LibreOffice
    if not pdf_converted:
        soffice_paths = [
            shutil.which("soffice") or "",
            shutil.which("soffice.exe") or "",
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            "soffice",
            "/usr/bin/soffice",
            "/usr/lib/libreoffice/program/soffice",
            "/opt/libreoffice/program/soffice",
        ]
        seen = set()
        unique_paths = []
        for p in soffice_paths:
            if p and p not in seen:
                seen.add(p)
                unique_paths.append(p)

        last_err = None
        for soffice_bin in unique_paths:
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
                f"PDF oluşturulamadı — Excel COM çalışmadı ve LibreOffice bulunamadı. "
                f"Detay: {last_err}"
            )

        # LibreOffice PageSetup üstbilgisini basmadığından başlık damgalaması zorunludur
        if os.path.exists(out_pdf):
            stamp_pdf_banner(out_pdf, template_path)

def _load_banner_bytes(template_path):
    """Şablondaki image2.png veya yedek tse_banner.png dosyasını yükler."""
    if template_path and os.path.exists(template_path):
        try:
            with zipfile.ZipFile(template_path, 'r') as z:
                if 'xl/media/image2.png' in z.namelist():
                    return z.read('xl/media/image2.png')
        except Exception as e:
            print(f"Şablondan banner okunamadı: {e}")

    if os.path.exists(BANNER_FALLBACK):
        with open(BANNER_FALLBACK, 'rb') as f:
            return f.read()

    raise FileNotFoundError(
        "Kırmızı TSE başlığı bulunamadı. "
        "FATURA2026.xlsx içinde xl/media/image2.png veya uygulama klasöründe "
        "tse_banner.png olmalı."
    )

def stamp_pdf_banner(pdf_path, template_path):
    """
    LibreOffice PDF çıktısına kırmızı TSE başlığı ve altındaki form başlık metnini
    tablo satırlarını kapatmayacak şekilde kompakt ve net (300 DPI) yerleştirir.
    """
    if not STAMP_AVAILABLE:
        raise RuntimeError(
            "PDF banner damgalama için pypdfium2 ve pillow gerekli. "
            "pip install pypdfium2 pillow"
        )

    import pypdfium2 as pdfium
    from PIL import Image, ImageDraw, ImageFont
    import io

    banner_bytes = _load_banner_bytes(template_path)
    banner_pil = Image.open(io.BytesIO(banner_bytes)).convert('RGB')

    pdf = pdfium.PdfDocument(pdf_path)
    try:
        if len(pdf) == 0:
            raise RuntimeError("PDF boş — banner damgalanamadı")

        page = pdf[0]
        page_width  = page.get_width()
        page_height = page.get_height()

        textpage = page.get_textpage()

        # Tablo başlangıç konumunu dinamik tespit et
        table_top_y = None
        searcher = textpage.search("FATURA DETAYI")
        match = searcher.get_next()
        if match:
            cbox = textpage.get_charbox(match[0], loose=False)
            y_from_top = page_height - cbox[3]
            table_top_y = max(y_from_top - 6.0, 80.0)

        if table_top_y is None:
            searcher2 = textpage.search("EVRAK NO")
            match2 = searcher2.get_next()
            if match2:
                cbox2 = textpage.get_charbox(match2[0], loose=False)
                y_from_top2 = page_height - cbox2[3]
                table_top_y = max(y_from_top2 - 30.0, 80.0)

        banner_h_pt = page_width * (69.0 / 842.25)  # ~48.8 pt
        header_h_pt = table_top_y if table_top_y is not None else 113.4

        SCALE = 4
        img_w = int(page_width * SCALE)
        img_h = int(header_h_pt * SCALE)

        composite = Image.new('RGB', (img_w, img_h), 'white')

        # 1. Kırmızı banner (en üst kısım)
        banner_h_px = int(banner_h_pt * SCALE)
        composite.paste(
            banner_pil.resize((img_w, banner_h_px), Image.Resampling.LANCZOS),
            (0, 0)
        )

        # 2. Başlık metni (MUAYENE GÖZETİM MERKEZİ BAŞKANLIĞI / ÖLÇÜ ALETLERİ FATURA DETAYI FORMU)
        draw = ImageDraw.Draw(composite)
        font_candidates = [
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSerif-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
            "C:/Windows/Fonts/timesbd.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "LiberationSerif-Bold.ttf",
            "DejaVuSerif-Bold.ttf",
            "timesbd.ttf",
            "arialbd.ttf",
        ]
        font = None
        for fp in font_candidates:
            try:
                font = ImageFont.truetype(fp, size=int(9.5 * SCALE))
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

        y1_px = int((banner_h_pt + 7.5) * SCALE)
        y2_px = int((banner_h_pt + 7.5 + 11.5) * SCALE)

        draw.text(((img_w - w1) / 2, y1_px), text1, fill="black", font=font)
        draw.text(((img_w - w2) / 2, y2_px), text2, fill="black", font=font)

        # 3. PDF'e yerleştir (Tablo satırlarını asla kapatmaz)
        pdf_image = pdfium.PdfImage.new(pdf)
        pdf_image.set_bitmap(pdfium.PdfBitmap.from_pil(composite))

        pdf_image.set_matrix(pdfium.PdfMatrix(
            page_width, 0,
            0, header_h_pt,
            0, page_height - header_h_pt
        ))
        page.insert_obj(pdf_image)
        page.gen_content()

        buf = io.BytesIO()
        pdf.save(buf)
    finally:
        pdf.close()

    with open(pdf_path, 'wb') as f:
        f.write(buf.getvalue())








# ─── OTURUM BAZLI KOTA TAKIBI (Veritabanı gerektirmez, çerezde saklanır) ───
def get_quota():
    """Kullanıcının günlük kota bilgisini (tarayıcı çerezinde) döndürür."""
    today = datetime.utcnow().strftime('%Y-%m-%d')
    session.permanent = True  # Tarayıcı kapanıp açılsa da sürsün
    
    quota = session.get('quota', {})
    if not quota or quota.get('date') != today:
        quota = {'used': 0, 'bonus': 0, 'date': today}
        session['quota'] = quota
        
    return quota

def save_quota(q):
    session['quota'] = q

def remaining_quota():
    q = get_quota()
    return max(0, FREE_LIMIT + q.get('bonus', 0) - q.get('used', 0))

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
    """Reklam izlendikten sonra çağrılır; bonus hak ekler."""
    q = get_quota()
    q['bonus'] += AD_REWARD_COUNT
    save_quota(q)
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
        save_quota(q)

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
