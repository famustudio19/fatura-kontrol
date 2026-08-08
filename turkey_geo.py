# -*- coding: utf-8 -*-
"""
Turkiye 81 Il ve Ilceler Haritasi
"""

TURKEY_DISTRICTS = {
    'ADANA': ['ALADAĞ', 'CEYHAN', 'ÇUKUROVA', 'FEKE', 'İMAMOĞLU', 'KARAİSALI', 'KARATAŞ', 'KOZAN', 'POZANTI', 'SAİMBEYLİ', 'SARIÇAM', 'SEYHAN', 'TUFANBEYLİ', 'YUMURTALIK', 'YÜREĞİR'],
    'ADIYAMAN': ['BESNİ', 'ÇELİKHAN', 'GERGER', 'GÖLBAŞI', 'KAHTA', 'SAMSAT', 'SİNCİK', 'TUT'],
    'AFYONKARAHİSAR': ['BAŞMAKÇI', 'BAYAT', 'BOLVADİN', 'ÇAY', 'ÇOBANLAR', 'DAZKIRI', 'DİNAR', 'EMİRDAĞ', 'EVCİLER', 'HOCALAR', 'İHSANİYE', 'İSCEHİSAR', 'KIZILÖREN', 'SANDIKLI', 'SİNANPAŞA', 'SULTANDAĞI', 'ŞUHUT'],
    'AĞRI': ['DİYADİN', 'DOĞUBAYAZIT', 'ELEŞKİRT', 'HAMUR', 'DOĞUBEYAZIT', 'PATNOS', 'TAŞLIÇAY', 'TUTAK'],
    'AKSARAY': ['AĞAÇÖREN', 'ESKİL', 'GÜLAĞAÇ', 'GÜZELYURT', 'ORTAKÖY', 'SARIYAHŞİ', 'SULTANHANI'],
    'AMASYA': ['GÖYNÜCEK', 'GÜMÜŞHACIKÖY', 'HAMAMÖZÜ', 'MERZİFON', 'SULUOVA', 'TAŞOVA'],
    'ANKARA': ['AKYURT', 'ALTINDAĞ', 'AYAŞ', 'BALA', 'BEYPAZARI', 'ÇAMLIDERE', 'ÇANKAYA', 'ÇUBUK', 'ELMADAĞ', 'ETİMESGUT', 'EVREN', 'GÖLBAŞI', 'GÜDÜL', 'HAYMANA', 'KAHRAMANKAZAN', 'KALECİK', 'KAZAN', 'KEÇİÖREN', 'KIZILCAHAMAM', 'MAMAK', 'NALLIHAN', 'POLATLI', 'PURSAKLAR', 'SİNCAN', 'ŞEREFLİKOÇHİSAR', 'YENİMAHALLE'],
    'ANTALYA': ['AKSEKİ', 'AKSU', 'ALANYA', 'DEMRE', 'DÖŞEMEALTI', 'ELMALI', 'FİNİKE', 'GAZİPAŞA', 'GÜNDOĞMUŞ', 'İBRADI', 'KAŞ', 'KEMER', 'KEPEZ', 'KONYAALTI', 'KORKUTELİ', 'KUMLUCA', 'MANAVGAT', 'MURATPAŞA', 'SERİK'],
    'ARDAHAN': ['ÇILDIR', 'DAMAL', 'GÖLE', 'HANAK', 'POSOF'],
    'ARTVİN': ['ARDANUÇ', 'ARHAVİ', 'BORÇKA', 'HOPA', 'KEMALPAŞA', 'MURGUL', 'ŞAVŞAT', 'YUSUFELİ'],
    'AYDIN': ['BOZDOĞAN', 'BUHARKENT', 'ÇİNE', 'DİDİM', 'EFELER', 'GERMENCİK', 'İNCİRLİOVA', 'KARACASU', 'KARPUZLU', 'KOÇARLI', 'KÖŞK', 'KUŞADASI', 'KUYUCAK', 'NAZİLLİ', 'SÖKE', 'SULTANHİSAR', 'YENİPAZAR'],
    'BALIKESİR': ['ALTIEYLÜL', 'AYVALIK', 'BALYA', 'BANDIRMA', 'BİGADİÇ', 'BURHANİYE', 'DURSUNBEY', 'EDREMİT', 'ERDEK', 'GÖMEÇ', 'GÖNEN', 'HAVRAN', 'İVRİNDİ', 'KARESİ', 'KEPSUT', 'MANYAS', 'MARMARA', 'SAVAŞTEPE', 'SINDIRGI', 'SUSURLUK'],
    'BARTIN': ['AMASRA', 'KURUCAŞİLE', 'ULUS'],
    'BATMAN': ['BEŞİRİ', 'GERCÜŞ', 'HASANKEYF', 'KOZLUK', 'SASON'],
    'BAYBURT': ['AYDINTEPE', 'DEMİRÖZÜ'],
    'BİLECİK': ['BOZÜYÜK', 'GÖLPAZARI', 'İNHİSAR', 'OSMANELİ', 'PAZARYERİ', 'SÖĞÜT', 'YENİPAZAR'],
    'BİNGÖL': ['ADAKLI', 'GENÇ', 'KARLIOVA', 'KİĞI', 'SOLHAN', 'YAYLADERE', 'YEDİSU'],
    'BİTLİS': ['ADİLCEVAZ', 'AHLAT', 'GÜROYMAK', 'HİZAN', 'MUTKİ', 'TATVAN'],
    'BOLU': ['DÖRTDİVAN', 'GEREDE', 'GÖYNÜK', 'KIBRISCIK', 'MENGEN', 'MUDURNU', 'SEBEN', 'YENİÇAĞA'],
    'BURDUR': ['AĞLASUN', 'ALTINYAYLA', 'BUCAK', 'ÇAVDIR', 'ÇELTİKÇİ', 'GÖLHİSAR', 'KARAMANLI', 'KEMER', 'TEFENNİ', 'YEŞİLOVA'],
    'BURSA': ['BÜYÜKORHAN', 'GEMLİK', 'GÜRSU', 'HARMANCIK', 'İNEGÖL', 'İZNİK', 'KARACABEY', 'KELES', 'KESTEL', 'MUDANYA', 'MUSTAFAKEMALPAŞA', 'NİLÜFER', 'ORHANELİ', 'ORHANGAZİ', 'OSMANGAZİ', 'YENİŞEHİR', 'YILDIRIM'],
    'ÇANAKKALE': ['AYVACIK', 'BAYRAMİÇ', 'BİGA', 'BOZCAADA', 'ÇAN', 'ECEABAT', 'EZİNE', 'GELİBOLU', 'GÖKÇEADA', 'LAPSEKİ', 'YENİCE'],
    'ÇANKIRI': ['ATKARACALAR', 'BAYRAMÖREN', 'ÇERKEŞ', 'ELDİVAN', 'ILGAZ', 'KIZILIRMAK', 'KORGUN', 'KURŞUNLU', 'ORTA', 'ŞABANÖZÜ', 'YAPRAKLI'],
    'ÇORUM': ['ALACA', 'BAYAT', 'BOĞAZKALE', 'DODURGA', 'İSKİLİP', 'KARGI', 'LAÇİN', 'MECİTÖZÜ', 'OĞUZLAR', 'ORTAKÖY', 'OSMANCIK', 'SUNGURLU', 'UĞURLUDAĞ'],
    'DENİZLİ': ['ACIPAYAM', 'BABADAĞ', 'BAKLAN', 'BEKİLLİ', 'BEYAĞAÇ', 'BOZKURT', 'BULDAN', 'ÇAL', 'ÇAMELİ', 'ÇARDAK', 'ÇİVRİL', 'GÜNEY', 'HONAZ', 'KALE', 'MERKEZEFENDİ', 'PAMUKKALE', 'SARAYKÖY', 'SERİNHİSAR', 'TAVAS'],
    'DİYARBAKIR': ['BAĞLAR', 'BİSMİL', 'ÇERMİK', 'ÇINAR', 'ÇÜNGÜŞ', 'DİCLE', 'EĞİL', 'ERGANİ', 'HANİ', 'HAZRO', 'KAYAPINAR', 'KOCAKÖY', 'KULP', 'LİCE', 'SİLVAN', 'SUR', 'YENİŞEHİR'],
    'DÜZCE': ['AKÇAKOCA', 'CUMAYERİ', 'ÇİLİMLİ', 'GÖLYAKA', 'GÜMÜŞOVA', 'KAYNAŞLI', 'YIĞILCA'],
    'EDİRNE': ['ENEZ', 'HAVSA', 'İPSALA', 'KEŞAN', 'LALAPAŞA', 'MERİÇ', 'SÜLOĞLU', 'UZUNKÖPRÜ'],
    'ELAZIĞ': ['AĞIN', 'ALACAKAYA', 'ARICAK', 'BASKİL', 'KARAKOÇAN', 'KEBAN', 'KOVANCILAR', 'MADEN', 'PALU', 'SİVRİCE'],
    'ERZİNCAN': ['ÇAYIRLI', 'İLİÇ', 'KEMAH', 'KEMALİYE', 'OTLUKBELİ', 'REFAHİYE', 'TERCAN', 'ÜZÜMLÜ'],
    'ERZURUM': ['AŞKALE', 'AZİZİYE', 'ÇAT', 'HINIS', 'HORASAN', 'İSPİR', 'KARAÇOBAN', 'KARAYAZI', 'KÖPRÜKÖY', 'NARMAN', 'OLTU', 'OLUR', 'PALANDÖKEN', 'PASİNLER', 'PAZARYOLU', 'ŞENKAYA', 'TEKMAN', 'TORTUM', 'UZUNDERE', 'YAKUTİYE'],
    'ESKİŞEHİR': ['ALPU', 'BEYLİKOVA', 'ÇİFTELER', 'GÜNYÜZÜ', 'HAN', 'İNÖNÜ', 'MAHMUDİYE', 'MİHALGAZİ', 'MİHALIÇÇIK', 'ODUNPAZARI', 'SARICAKAYA', 'SEYİTGAZİ', 'SİVRİHİSAR', 'TEPEBAŞI'],
    'GAZİANTEP': ['ARABAN', 'İSLAHİYE', 'KARKAMIŞ', 'NİZİP', 'NURDAĞI', 'OĞUZELİ', 'ŞAHİNBEY', 'ŞEHİTKAMİL', 'YAVUZELİ'],
    'GİRESUN': ['ALUCRA', 'BULANCAK', 'ÇAMOLUK', 'ÇANAKÇI', 'DERELİ', 'DOĞANKENT', 'ESPİYE', 'EYNESİL', 'GÖRELE', 'GÜCE', 'KEŞAP', 'PİRDEVLET', 'PİRVALİ', 'PİRASİZ', 'PİRAZİZ', 'ŞEBİNKARAHİSAR', 'TİREBOLU', 'YAĞLIDERE'],
    'GÜMÜŞHANE': ['KELKİT', 'KÖSE', 'KÜRTÜN', 'ŞİRAN', 'TORUL'],
    'HAKKARİ': ['ÇUKURCA', 'DERECİK', 'ŞEMDİNLİ', 'YÜKSEKOVA'],
    'HATAY': ['ALTINÖZÜ', 'ANTAKYA', 'ARSUZ', 'BELEN', 'DEFNE', 'DÖRTYOL', 'ERZİN', 'HASSA', 'İSKENDERUN', 'KIRIKHAN', 'KUMLU', 'PAYAS', 'REYHANLI', 'SAMANDAĞ', 'YAYLADAĞI'],
    'IĞDIR': ['ARALIK', 'KARAKOYUNLU', 'TUZLUCA'],
    'ISPARTA': ['AKSU', 'ATABEY', 'EĞİRDİR', 'GELENDOST', 'GÖNEN', 'KEÇİBORLU', 'SENİRKENT', 'SÜTÇÜLER', 'ŞARKİKARAAĞAÇ', 'ULUBORLU', 'YALVAÇ', 'YENİŞARBADEMLİ'],
    'İSTANBUL': ['ADALAR', 'ARNAVUTKÖY', 'ATAŞEHİR', 'AVCILAR', 'BAĞCILAR', 'BAHÇELİEVLER', 'BAKIRKÖY', 'BAŞAKŞEHİR', 'BAYRAMPAŞA', 'BEŞİKTAŞ', 'BEYKOZ', 'BEYLİKDÜZÜ', 'BEYOĞLU', 'BÜYÜKÇEKMECE', 'ÇATALCA', 'ÇEKMEKÖY', 'ESENLER', 'ESENYURT', 'EYÜPSULTAN', 'FATİH', 'GAZİOSMANPAŞA', 'GÜNGÖREN', 'KADIKÖY', 'KAĞITHANE', 'KARTAL', 'KÜÇÜKÇEKMECE', 'MALTEPE', 'PENDİK', 'SANCAKTEPE', 'SARIYER', 'SİLİVRİ', 'SULTANBEYLİ', 'SULTANGAZİ', 'ŞİLE', 'ŞİŞLİ', 'TUZLA', 'ÜMRANİYE', 'ÜSKÜDAR', 'ZEYTİNBURNU'],
    'İZMİR': ['ALİAĞA', 'BALÇOVA', 'BAYINDIR', 'BAYRAKLI', 'BERGAMA', 'BEYDAĞ', 'BORNOVA', 'BUCA', 'ÇEŞME', 'ÇİĞLİ', 'DİKİLİ', 'FOÇA', 'GAZİEMİR', 'GÜZELBAHÇE', 'KARABAĞLAR', 'KARABURUN', 'KARŞIYAKA', 'KEMALPAŞA', 'KINIK', 'KİRAZ', 'KONAK', 'MENDERES', 'MENEMEN', 'NARLIDERE', 'ÖDEMİŞ', 'SEFERİHİSAR', 'SELÇUK', 'TİRE', 'TORBALI', 'URLA'],
    'KAHRAMANMARAŞ': ['AFŞİN', 'ANDIRIN', 'ÇAĞLAYANCERİT', 'DULKADİROĞLU', 'EKİNÖZÜ', 'ELBİSTAN', 'GÖKSUN', 'NURHAK', 'ONİKİŞUBAT', 'PAZARCIK', 'TÜRKOĞLU'],
    'KARABÜK': ['EFLANİ', 'ESKİPAZAR', 'OVACIK', 'SAFRANBOLU', 'YENİCE'],
    'KARAMAN': ['AYRANCI', 'BAŞYAYLA', 'ERMENEK', 'KAZIMKARABEKİR', 'SARIVELİLER'],
    'KARS': ['AKYAKA', 'ARPAÇAY', 'DİGOR', 'KAĞIZMAN', 'SARIKAMIŞ', 'SELİM', 'SUSUZ'],
    'KASTAMONU': ['ABANA', 'AĞLI', 'ARAÇ', 'AZDAVAY', 'BOZKURT', 'CİDE', 'ÇATALZEYTİN', 'DADAY', 'DEVREKANİ', 'DOĞANYURT', 'HANÖNÜ', 'İHSANGAZİ', 'İNEBOLU', 'KÜRE', 'PINARBAŞI', 'SEYDİLER', 'ŞENPAZAR', 'TAŞKÖPRÜ', 'TOSYA'],
    'KAYSERİ': ['AKKIŞLA', 'BÜNYAN', 'DEVELİ', 'FELAHİYE', 'HACILAR', 'İNCESU', 'KOCASİNAN', 'MELİKGAZİ', 'ÖZVATAN', 'PINARBAŞI', 'SARIOĞLAN', 'SARIZ', 'TALAS', 'TOMARZA', 'YAHYALI', 'YEŞİLHİSAR'],
    'KİLİS': ['ELBEYLİ', 'MUSABEYLİ', 'POLATELİ'],
    'KIRIKKALE': ['BAHŞILI', 'BALIŞEYH', 'ÇELEBİ', 'DELİCE', 'KARAKEÇİLİ', 'KESKİN', 'SULAKYURT', 'YAHŞİHAN'],
    'KIRKLARELİ': ['BABAESKİ', 'DEMİRKÖY', 'KOFÇAZ', 'LÜLEBURGAZ', 'PEHLİVANKÖY', 'PINARHİSAR', 'VİZE'],
    'KIRŞEHİR': ['AKÇAKENT', 'AKPINAR', 'BOZTEPE', 'ÇİÇEKDAĞI', 'KAMAN', 'MUCUR'],
    'KOCAELİ': ['BAŞİSKELE', 'ÇAYIROVA', 'DARICA', 'DERİNCE', 'DİLOVASI', 'GEBZE', 'GÖLCÜK', 'İZMİT', 'KANDIRA', 'KARAMÜRSEL', 'KARTEPE', 'KÖRFEZ'],
    'KONYA': ['AHIRLI', 'AKÖREN', 'AKŞEHİR', 'ALTINEKİN', 'BEYŞEHİR', 'BOZKIR', 'CİHANBEYLİ', 'ÇELTİK', 'ÇUMRA', 'DERBENT', 'DEREBUCAK', 'DOĞANHİSAR', 'EMİRGAZİ', 'EREĞLİ', 'GÜNEYSINIR', 'HADİM', 'HALKAPINAR', 'HÜYÜK', 'ILGIN', 'KADINHANI', 'KARAPINAR', 'KARATAY', 'KULU', 'MERAM', 'SARAYÖNÜ', 'SELÇUKLU', 'SEYDİŞEHİR', 'TAŞKENT', 'TUZLUKÇU', 'YALIHÜYÜK', 'YUNAK'],
    'KÜTAHYA': ['ALTINTAŞ', 'ASLANAPA', 'ÇAVDARHİSAR', 'DOMANİÇ', 'DUMLUPINAR', 'EMET', 'GEDİZ', 'HİSARCIK', 'PAZARLAR', 'ŞAPHANE', 'SİMAV', 'TAVŞANLI'],
    'MALATYA': ['AKÇADAĞ', 'ARAPGİR', 'ARGUVAN', 'BATTALGAZİ', 'DARENDE', 'DOĞANŞEHİR', 'DOĞANYOL', 'HEKİMHAN', 'KALE', 'KULUNCAK', 'PÜTÜRGE', 'YAZIHAN', 'YEŞİLYURT'],
    'MANİSA': ['AHMETLİ', 'AKHİSAR', 'ALAŞEHİR', 'DEMİRCİ', 'GÖLMARMARA', 'GÖRDES', 'KIRKAĞAÇ', 'KÖPRÜBAŞI', 'KULA', 'SALİHLİ', 'SARIGÖL', 'SARUHANLI', 'SELENDİ', 'SOMA', 'ŞEHZADELER', 'TURGUTLU', 'YUNUSEMRE'],
    'MARDİN': ['ARTUKLU', 'DARGEÇİT', 'DERİK', 'KIZILTEPE', 'MAZIDAĞI', 'MİDYAT', 'NUSAYBİN', 'ÖMERLİ', 'SAVUR', 'YEŞİLLİ'],
    'MERSİN': ['AKDENİZ', 'ANAMUR', 'AYDINCIK', 'BOZYAZI', 'ÇAMLIYAYLA', 'ERDEMLİ', 'GÜLNAR', 'MEZİTLİ', 'MUT', 'SİLİFKE', 'TARSUS', 'TOROSLAR', 'YENİŞEHİR'],
    'MUĞLA': ['BODRUM', 'DALAMAN', 'DATÇA', 'FETHİYE', 'KAVAKLIDERE', 'KÖYCEĞİZ', 'MARMARİS', 'MENTEŞE', 'MİLAS', 'ORTACA', 'SEYDİKEMER', 'ULA', 'YATAĞAN'],
    'MUŞ': ['BULANIK', 'HASKÖY', 'KORKUT', 'MALAZGİRT', 'VARTO'],
    'NEVŞEHİR': ['ACIGÖL', 'AVANOS', 'DERİNKUYU', 'GÜLŞEHİR', 'HACIBEKTAŞ', 'KOZAKLI', 'ÜRGÜP'],
    'NİĞDE': ['ALTUNHİSAR', 'BOR', 'ÇAMARDI', 'ÇİFTLİK', 'ULUKIŞLA'],
    'ORDU': ['AKKUŞ', 'ALTINORDU', 'AYBASTI', 'ÇAMAŞ', 'ÇATALPINAR', 'ÇAYBAŞI', 'FATSA', 'GÖLKÖY', 'GÜLYALI', 'GÜRGENTEPE', 'İKİZCE', 'KABADÜZ', 'KABATAŞ', 'KORGAN', 'KUMRU', 'MESUDİYE', 'PERŞEMBE', 'ULUBEY', 'ÜNYE'],
    'OSMANİYE': ['BAHÇE', 'DÜZİÇİ', 'HASANBEYLİ', 'KADİRLİ', 'SUMBAS', 'TOPRAKKALE'],
    'RİZE': ['ARDEŞEN', 'ÇAMLIHEMŞİN', 'ÇAYELİ', 'DEREPAZARI', 'FINDIKLI', 'GÜNEYSU', 'HEMŞİN', 'İKİZDERE', 'İYİDERE', 'KALKANDERE', 'PAZAR'],
    'SAKARYA': ['ADAPAZARI', 'AKYAZI', 'ARİFİYE', 'ERENLER', 'FERİZLİ', 'GEYVE', 'HENDEK', 'KARAPÜRÇEK', 'KARASU', 'KAYNARCA', 'KOCAALİ', 'PAMUKOVA', 'SAPANCA', 'SERDİVAN', 'SÖĞÜTLÜ', 'TARAKLI'],
    'SAMSUN': ['ALAÇAM', 'ASARCIK', 'ATAKUM', 'AYVACIK', 'BAFRA', 'CANİK', 'ÇARŞAMBA', 'HAVZA', 'İLKADIM', 'KAVAK', 'LADİK', 'ONMAYIS', '19 MAYIS', 'SALIPAZARI', 'TEKKEKÖY', 'TERME', 'VEZİRKÖPRÜ', 'YAKAKENT'],
    'ŞANLIURFA': ['AKÇAKALE', 'BİRECİK', 'BOZOVA', 'CEYLANPINAR', 'EYYÜBİYE', 'HALFETİ', 'HALİLİYE', 'HARRAN', 'HİLVAN', 'KARAKÖPRÜ', 'SİVEREK', 'SURUÇ', 'VİRANŞEHİR'],
    'SİİRT': ['BAYKAN', 'ERUH', 'KURTALAN', 'PERVARİ', 'ŞİRVAN', 'TİLLO'],
    'SİNOP': ['AYANCIK', 'BOYABAT', 'DİKMEN', 'DURAĞAN', 'ERFELEK', 'GERZE', 'SARAYDÜZÜ', 'TÜRKELİ'],
    'ŞIRNAK': ['BEYTÜŞŞEBAP', 'CİZRE', 'GÜÇLÜKONAK', 'İDİL', 'SİLOPİ', 'ULUDERE'],
    'SİVAS': ['AKINCILAR', 'ALTINYAYLA', 'DOĞANŞAR', 'GEMEREK', 'GÖLOVA', 'GÜRÜN', 'HAFİK', 'İMRANLI', 'KANGAL', 'KOYULHİSAR', 'SUŞEHRİ', 'ŞARKIŞLA', 'ULAŞ', 'YILDIZELİ', 'ZARA'],
    'TEKİRDAĞ': ['ÇERKEZKÖY', 'ÇORLU', 'ERGENE', 'HAYRABOLU', 'KAPAKLI', 'MALKARA', 'MARMARAEREĞLİSİ', 'MURATLI', 'SARAY', 'SÜLEYMANPAŞA', 'ŞARKÖY'],
    'TOKAT': ['ALMUS', 'ARTOVA', 'BAŞÇİFTLİK', 'ERBAA', 'NİKSAR', 'PAZAR', 'REŞADİYE', 'SULUSARAY', 'TURHAL', 'YEŞİLYURT', 'ZİLE'],
    'TRABZON': ['AKÇAABAT', 'ARAKLI', 'ARSİN', 'BEŞİKDÜZÜ', 'ÇARŞIBAŞI', 'ÇAYKARA', 'DERNEKPAZARI', 'DÜZKÖY', 'HAYRAT', 'KÖPRÜBAŞI', 'MAÇKA', 'OF', 'ORTAHİSAR', 'SÜRMENE', 'ŞALPAZARI', 'TONYA', 'VAKFIKEBİR', 'YOMRA'],
    'TUNCELİ': ['ÇEMİŞGEZEK', 'HOZAT', 'MAZGİRT', 'NAZIMİYE', 'OVACIK', 'PERTEK', 'PÜLÜMÜR'],
    'UŞAK': ['BANAZ', 'EŞME', 'KARAHALLI', 'SİVASLI', 'ULUBEY'],
    'VAN': ['BAHÇESARAY', 'BAŞKALE', 'ÇALDIRAN', 'ÇATAK', 'EDREMİT', 'ERCİŞ', 'GEVAŞ', 'GÜRPINAR', 'İPEKYOLU', 'MURADİYE', 'ÖZALP', 'SARAY', 'TUŞBA'],
    'YALOVA': ['ALTINOVA', 'ARMUTLU', 'ÇINARCIK', 'ÇİFTLİKKÖY', 'TERMAL'],
    'YOZGAT': ['AKDAĞMADENİ', 'AYDINCIK', 'BOĞAZLIYAN', 'ÇANDIR', 'ÇAYIRALAN', 'ÇEKEREK', 'KADIŞEHRİ', 'SARAYKENT', 'SARIKAYA', 'SORGUN', 'ŞEFAATLİ', 'YENİFAKILI', 'YERKÖY'],
    'ZONGULDAK': ['ALAPLI', 'ÇAYCUMA', 'DEVREK', 'EREĞLİ', 'GÖKÇEBEY', 'KİLİMLİ', 'KOZLU']
}

def tr_upper(text):
    if not text: return ""
    tr_map = {'i': 'İ', 'ı': 'I', 'ç': 'Ç', 'ğ': 'Ğ', 'ö': 'Ö', 'ş': 'Ş', 'ü': 'Ü'}
    res = []
    for c in text:
        res.append(tr_map.get(c, c.upper()))
    return "".join(res)

def normalize_tr_ascii(text):
    """Türkçe karakterleri ASCII eşdeğerine çevirir (arama toleransı için)."""
    if not text: return ""
    u = tr_upper(text)
    rep = {'İ': 'I', 'Ç': 'C', 'Ğ': 'G', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'}
    for k, v in rep.items():
        u = u.replace(k, v)
    return u

# İl ve İlçe arama haritasını oluştur
ILLER = list(TURKEY_DISTRICTS.keys())
DISTRICT_TO_PROVINCE = {}

for il, ilceler in TURKEY_DISTRICTS.items():
    for ilce in ilceler:
        DISTRICT_TO_PROVINCE[ilce] = il
        DISTRICT_TO_PROVINCE[normalize_tr_ascii(ilce)] = il

# Özel Vergi Daireleri Haritası (İl/İlçe adıyla birebir uyuşmayan meşhur vergi daireleri)
SPECIAL_TAX_OFFICES = {
    'ARDA': 'EDİRNE',
    'KIRKPINAR': 'EDİRNE',
    'HIZIRBEY': 'KIRKLARELİ',
    'NAMIK KEMAL': 'TEKİRDAĞ',
    'YAKUP ÇELEBİ': 'BURSA',
    'ÇEKİRGE': 'BURSA',
    'ULUDAĞ': 'BURSA',
    'YILDIRIM BEYAZIT': 'BURSA',
    'HASAN TAHSİN': 'İZMİR',
    'DOKUZ EYLÜL': 'İZMİR',
    'KORDON': 'İZMİR',
    'BELKIZ': 'İZMİR',
    'SEĞMENLER': 'ANKARA',
    'KAVAKLIDERE': 'ANKARA',
    'DİĞLE': 'DİYARBAKIR',
    'GÖKSU': 'İSTANBUL',
    'MARMARA': 'İSTANBUL',
    'HALİÇ': 'İSTANBUL',
    'BOĞAZİÇİ': 'İSTANBUL',
    'VERASET': 'İSTANBUL',
    'RUMELİ': 'İSTANBUL',
}

# Cadde / Sokak / Mahalle ekleri (bu eklerden önceki kelimeler ilçe olarak algılanmamalı)
STREET_SUFFIXES = [
    'CAD', 'CAD.', 'CADDESI', 'CADDESİ',
    'SK', 'SK.', 'SOK', 'SOK.', 'SOKAK', 'SOKAGI', 'SOKAĞI',
    'MAH', 'MAH.', 'MAHALLE', 'MAHALLESI', 'MAHALLESİ',
    'BULV', 'BULV.', 'BULVAR', 'BULVARI',
    'KOY', 'KOY.', 'KOYU', 'KÖY', 'KÖYÜ',
    'MEVKI', 'MEVKII', 'MEVKİ', 'MEVKİİ',
    'SIT', 'SITESI', 'SİTE', 'SİTESİ',
    'APT', 'APARTMAN', 'APARTMANI',
    'HAN', 'HANI', 'PASAJ', 'PASAJI',
    'IS MERKEZI', 'İŞ MERKEZİ', 'SANAYI', 'SANAYİ', 'KOOP', 'KOOPERATIF'
]

import re

def enrich_address_with_city(address, vergi_dairesi="", full_text=""):
    """
    Fatura adresinde şehir/il ismi eksikse otomatik olarak:
    1. Muayene adresindeki il/ilçe bilgisinden,
    2. Fatura adresinin sonundaki ilçe bilgisinden (Cadde/Sokak filtreli),
    3. Vergi dairesi adından (özel VD haritası dahil),
    4. Belge metninden
    ili tespit edip fatura adresinin sonuna ' / İL' ekler.
    """
    if not address or not address.strip():
        return address
        
    addr_clean = address.strip()
    addr_upper = tr_upper(addr_clean)
    addr_ascii = normalize_tr_ascii(addr_clean)
    vd_upper = tr_upper(vergi_dairesi or "")
    vd_ascii = normalize_tr_ascii(vergi_dairesi or "")
    text_upper = tr_upper(full_text or "")
    
    # 1. Adreste zaten 81 ilden biri açıkça yazıyor mu?
    for il in ILLER:
        il_ascii = normalize_tr_ascii(il)
        if re.search(rf'\b{re.escape(il)}\b', addr_upper) or re.search(rf'\b{re.escape(il_ascii)}\b', addr_ascii):
            return addr_clean  # İl zaten mevcut, dokunma
            
    bulunan_il = None

    # 2. PDF içindeki "Muayene Adresi" alanından il tespiti (en güvenilir kaynak)
    if text_upper:
        m_muayene = re.search(r'Muayene Adresi[:\s]+([^\n\r]+)', text_upper)
        if m_muayene:
            muayene_txt = m_muayene.group(1)
            # Muayene adresinde il var mı?
            for il in ILLER:
                if re.search(rf'\b{re.escape(il)}\b', muayene_txt):
                    bulunan_il = il
                    break

    # 3. Vergi Dairesi adından il/ilçe tespiti
    if not bulunan_il and (vd_upper or vd_ascii):
        # Özel vergi daireleri (Örn: Arda -> Edirne, Kırkpınar -> Edirne)
        for vd_key, vd_il in SPECIAL_TAX_OFFICES.items():
            if vd_key in vd_upper or normalize_tr_ascii(vd_key) in vd_ascii:
                bulunan_il = vd_il
                break
        # Doğrudan il adı geçen vergi daireleri (Örn: Edirne Vergi Dairesi)
        if not bulunan_il:
            for il in ILLER:
                il_ascii = normalize_tr_ascii(il)
                if re.search(rf'\b{re.escape(il)}\b', vd_upper) or re.search(rf'\b{re.escape(il_ascii)}\b', vd_ascii):
                    bulunan_il = il
                    break
        # İlçe adı geçen vergi daireleri (Örn: Keşan Vergi Dairesi -> Edirne, Çorlu VD -> Tekirdağ)
        if not bulunan_il:
            sorted_districts = sorted(DISTRICT_TO_PROVINCE.keys(), key=len, reverse=True)
            for ilce in sorted_districts:
                if re.search(rf'\b{re.escape(ilce)}\b', vd_upper) or re.search(rf'\b{re.escape(ilce)}\b', vd_ascii):
                    bulunan_il = DISTRICT_TO_PROVINCE[ilce]
                    break

    # 4. Adres metninden ilçe tespiti (Cadde/Sokak/Mahalle eklerini hariç tutarak)
    if not bulunan_il:
        # Adresteki son kelimeleri önceliklendir (Türkiye'de ilçe adresin en sonunda yer alır: örn: "... NO:80 KEŞAN")
        tokens = [t.strip(' ,.-/') for t in addr_upper.split() if t.strip(' ,.-/')]
        
        # Sondan başa doğru ilçeleri kontrol et
        for idx in range(len(tokens) - 1, -1, -1):
            tok = tokens[idx]
            # Eğer bu token'dan sonra CAD, SK, MAH vb. geliyorsa bu ilçe değil sokak adıdır (Örn: "NİLÜFER CAD.")
            if idx + 1 < len(tokens):
                next_tok = tokens[idx + 1]
                if next_tok in STREET_SUFFIXES:
                    continue
            
            if tok in DISTRICT_TO_PROVINCE:
                bulunan_il = DISTRICT_TO_PROVINCE[tok]
                break
            tok_ascii = normalize_tr_ascii(tok)
            if tok_ascii in DISTRICT_TO_PROVINCE:
                bulunan_il = DISTRICT_TO_PROVINCE[tok_ascii]
                break

    # 5. Tespit edilen ili adresin sonuna ekle
    if bulunan_il:
        # Eğer adreste son karakter '/' veya '-' ise
        if addr_clean.endswith('/') or addr_clean.endswith('-'):
            return f"{addr_clean} {bulunan_il}"
        else:
            return f"{addr_clean} / {bulunan_il}"
            
    return addr_clean
