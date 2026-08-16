// ─── İLERLEME ÇUBUĞU ANİMASYON MOTORU ─────────────────────────────────────
let _progressTimer = null;
let _currentProgress = 0;

function startProgressSimulation(fileCount) {
  // Her PDF için ~4 saniye tahmini; 87%'e kadar smooth ilerler, son %13 sunucuya bırakılır
  const estimatedMs = Math.max(5000, fileCount * 4000);
  _currentProgress = 0;
  setProgress(5); // anında küçük bir hareket

  const startTime = Date.now();
  clearInterval(_progressTimer);
  _progressTimer = setInterval(() => {
    const elapsed = Date.now() - startTime;
    const ratio = elapsed / estimatedMs;
    // easeOutQuad: hızlı başlar yavaşlar (gerçekçi his)
    const eased = 1 - Math.pow(1 - Math.min(ratio, 1), 2);
    const target = 5 + eased * 82; // 5% → 87% arası
    if (target > _currentProgress) {
      _currentProgress = target;
      setProgress(_currentProgress);
    }
    if (_currentProgress >= 87) clearInterval(_progressTimer);
  }, 120);
}

function setProgress(pct) {
  const bar = document.getElementById('webProgressBar');
  if (bar) bar.style.width = Math.min(100, pct).toFixed(1) + '%';
}

function finishProgress() {
  clearInterval(_progressTimer);
  setProgress(100);
}

function resetProgress() {
  clearInterval(_progressTimer);
  _currentProgress = 0;
  setProgress(0);
}

document.addEventListener('DOMContentLoaded', () => {

  const pdfFileInput    = document.getElementById('pdfFileInput');
  const pdfFileLabel    = document.getElementById('pdfFileLabel');
  const dropzonePdf     = document.getElementById('dropzonePdf');

  const excelFileInput  = document.getElementById('excelFileInput');
  const excelFileLabel  = document.getElementById('excelFileLabel');

  const outFolderBtn       = document.getElementById('outFolderBtn');
  const outputStatusLabel  = document.getElementById('outputStatusLabel');

  const webStartBtn    = document.getElementById('webStartBtn');
  const webProgressBar = document.getElementById('webProgressBar');
  const webTerminal    = document.getElementById('webTerminal');
  const logStatusText  = document.getElementById('logStatusText');

  let selectedFiles     = [];
  let selectedExcelFile = null;
  let currentJobId      = null;
  let outputDirHandle   = null;

  // ─── Kota sayacını güncelle ───────────────────────────────────────────────
  function updateQuotaUI(remaining) {
    serverRemaining = remaining;
    const bar = document.getElementById('quotaBar');
    if (!bar) return;

    const textEl = bar.querySelector('.quota-text');
    if (textEl) {
      if (remaining > 0) {
        textEl.innerHTML = `📄 Günlük <strong>${remaining}</strong> PDF işleme hakkınız kaldı`;
      } else {
        textEl.innerHTML = `🚫 Günlük limitiniz doldu`;
      }
    }

    bar.className = 'quota-bar ' + (remaining >= 3 ? 'quota-ok' : remaining > 0 ? 'quota-low' : 'quota-out');

    // "Reklam İzle" butonu her zaman aktif ve görünür kalsın
    let watchBtn = document.getElementById('watchAdBtn');
    if (!watchBtn) {
      watchBtn = document.createElement('button');
      watchBtn.className = 'btn-watch-ad';
      watchBtn.id = 'watchAdBtn';
      watchBtn.innerHTML = `📺 Reklam İzle +${adRewardCount} Hak Kazan`;
      watchBtn.onclick = openAdModal;
      bar.appendChild(watchBtn);
    }

    // Başlat butonu
    if (webStartBtn) webStartBtn.disabled = remaining <= 0;
  }

  // ─── 1. PDF Klasörü Seçme ─────────────────────────────────────────────────
  if (dropzonePdf && pdfFileInput) {
    dropzonePdf.addEventListener('click', () => pdfFileInput.click());
    pdfFileInput.addEventListener('change', () => {
      if (pdfFileInput.files.length > 0) {
        selectedFiles = Array.from(pdfFileInput.files);
        pdfFileLabel.innerText = `${selectedFiles.length} adet PDF seçildi`;
        logTerm(`${selectedFiles.length} adet PDF dosyası yüklendi.`);
      }
    });
  }

  // ─── 2. Excel Şablonu Seçme ───────────────────────────────────────────────
  if (excelFileInput) {
    excelFileInput.addEventListener('change', () => {
      if (excelFileInput.files.length > 0) {
        selectedExcelFile = excelFileInput.files[0];
        excelFileLabel.innerText = selectedExcelFile.name;
        logTerm(`Excel şablonu seçildi: ${selectedExcelFile.name}`);
      }
    });
  }

  // ─── 3. Çıktı Klasörü Seçme ───────────────────────────────────────────────
  if (outFolderBtn) {
    outFolderBtn.addEventListener('click', async () => {
      if (!window.showDirectoryPicker) {
        alert("Tarayıcınız klasör seçme özelliğini desteklemiyor. Dosyalar İndirilenler klasörüne kaydedilecek.");
        return;
      }
      try {
        outputDirHandle = await window.showDirectoryPicker({ mode: 'readwrite' });
        outputStatusLabel.innerText = `📁 ${outputDirHandle.name} (Seçildi)`;
        logTerm(`Çıktı klasörü seçildi: ${outputDirHandle.name}`);
      } catch (err) {
        if (err.name !== 'AbortError') alert("Klasör seçilirken bir hata oluştu.");
      }
    });
  }

  // ─── Terminal log ─────────────────────────────────────────────────────────
  function logTerm(msg) {
    if (!webTerminal) return;
    const now  = new Date().toLocaleTimeString('tr-TR');
    const line = document.createElement('div');
    line.className = 'term-line';
    line.innerText = `${now}: ${msg}`;
    webTerminal.appendChild(line);
    webTerminal.scrollTop = webTerminal.scrollHeight;
  }

  // ─── 4. İşlemi Başlat ────────────────────────────────────────────────────
  if (webStartBtn) {
    webStartBtn.addEventListener('click', async () => {
      if (selectedFiles.length === 0) {
        alert('Lütfen önce Başvuru PDF dosyalarını seçin!');
        return;
      }
      if (!selectedExcelFile) {
        alert('Lütfen Excel Şablonu dosyasını seçin!');
        return;
      }
      if (serverRemaining <= 0) {
        openAdModal();
        return;
      }

      // Çıktı klasörü seçilmediyse otomatik sor
      if (!outputDirHandle && window.showDirectoryPicker) {
        try {
          outputDirHandle = await window.showDirectoryPicker({ mode: 'readwrite' });
          outputStatusLabel.innerText = `📁 ${outputDirHandle.name} (Seçildi)`;
          logTerm(`Çıktı klasörü seçildi: ${outputDirHandle.name}`);
        } catch (err) {
          if (err.name === 'AbortError') {
            logTerm('Klasör seçimi iptal edildi. Dosyalar otomatik indirilecek.');
          }
        }
      }

      const formData = new FormData();
      selectedFiles.forEach(f => formData.append('pdf_files', f));
      if (selectedExcelFile) formData.append('excel_template', selectedExcelFile);

      webStartBtn.disabled = true;
      webStartBtn.style.opacity = '0.7';
      if (logStatusText) logStatusText.innerText = 'İşleniyor...';

      logTerm('Fatura Aktarım İşlemi başlatıldı...');
      logTerm(`Excel Şablonu (${selectedExcelFile.name}) okunuyor...`);
      logTerm(`${selectedFiles.length} PDF dosyası işlenecek, lütfen bekleyin...`);

      // Dosya sayısına göre tahmini ilerleme animasyonu başlat
      startProgressSimulation(selectedFiles.length);

      try {
        logTerm('PDF tabloları analiz ediliyor...');

        const response = await fetch('/api/process', { method: 'POST', body: formData });
        let data;
        try {
          data = await response.json();
        } catch (jsonErr) {
          logTerm('HATA: Sunucu yanıtı okunamadı.');
          alert('Sunucu hatası oluştu. Lütfen sayfayı yenileyip tekrar deneyin.');
          resetState();
          return;
        }

        if (response.status === 429 || data.error === 'limit_exceeded') {
          logTerm('HATA: Günlük PDF limitiniz doldu!');
          resetState();
          openAdModal();
          return;
        }

        if (!response.ok) {
          logTerm(`HATA: ${data.error || 'İşlem başarısız.'}`);
          alert('Hata: ' + (data.error || 'İşlem başarısız.'));
          resetState();
          return;
        }

        if (data.errors && data.errors.length > 0) {
          data.errors.forEach(err => logTerm(`Uyarı: ${err}`));
          if (!data.results || data.results.length === 0) {
            logTerm('HATA: Hiçbir dosya işlenemedi.');
            alert('Hata: Dosyalar işlenirken bir sorun oluştu.');
            resetState();
            return;
          }
        }

        logTerm('İşlem tamamlandı! Çıktı dosyaları hazır.');

        // Kota göstergesini güncelle
        if (typeof data.remaining !== 'undefined') updateQuotaUI(data.remaining);

        currentJobId = data.job_id;

        if (outputDirHandle && window.showDirectoryPicker) {
          logTerm(`Dosyalar ${outputDirHandle.name} klasörüne kaydediliyor...`);
          for (const item of data.results) {
            await downloadAndSave(currentJobId, item.pdf, outputDirHandle);
            await downloadAndSave(currentJobId, item.excel, outputDirHandle);
          }
          logTerm('Tüm dosyalar başarıyla klasöre kaydedildi! 🎉');
          alert('Dosyalar seçtiğiniz klasöre başarıyla kaydedildi!');
        } else {
          logTerm('Dosyalar İndirilenler klasörüne indiriliyor...');
          for (const item of data.results) {
            triggerDirectDownload(`/download/${currentJobId}/${encodeURIComponent(item.pdf)}`, item.pdf);
            await new Promise(r => setTimeout(r, 300));
            triggerDirectDownload(`/download/${currentJobId}/${encodeURIComponent(item.excel)}`, item.excel);
            await new Promise(r => setTimeout(r, 300));
          }
          logTerm('Tüm dosyalar indirildi! 🎉');
          alert('Tüm dosyalar başarıyla indirildi!');
        }

        finishProgress();
        if (logStatusText) logStatusText.innerText = 'Tamamlandı ✔';
        resetState();

      } catch (err) {
        logTerm(`Sunucu Hatası: ${err.message}`);
        alert('Sunucu hatası: ' + err.message);
        resetState();
      }
    });
  }

  // ─── Dosya kaydet ────────────────────────────────────────────────────────
  async function downloadAndSave(jobId, filename, dirHandle) {
    try {
      logTerm(`${filename} indiriliyor...`);
      const resp = await fetch(`/download/${jobId}/${encodeURIComponent(filename)}`);
      if (!resp.ok) { logTerm(`Hata: ${filename} indirilemedi (${resp.status}).`); return; }
      const blob       = await resp.blob();
      const fileHandle = await dirHandle.getFileHandle(filename, { create: true });
      const writable   = await fileHandle.createWritable();
      await writable.write(blob);
      await writable.close();
      logTerm(`✓ ${filename} kaydedildi.`);
    } catch (err) {
      console.error(err);
      logTerm(`Hata: ${filename} kaydedilemedi.`);
    }
  }

  function triggerDirectDownload(url, filename) {
    const a = document.createElement('a');
    a.href = url; a.download = filename;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  }

  function resetState() {
    webStartBtn.disabled = serverRemaining <= 0;
    webStartBtn.style.opacity = '1';
    setTimeout(() => resetProgress(), 1500); // 1.5sn sonra sıfırla (100% görünsün)
    if (logStatusText)  logStatusText.innerText = '● Hazır — Dosyaları seçip İşlemi Başlatın';
  }

  // ilk yükleme
  updateQuotaUI(serverRemaining);
});

// ─── REKLAM İZLE / SMARTLINK MODAL ───────────────────────────────────────────
let adTimerInterval = null;
window.isAdBlocked = false;

function openAdModal() {
  const modal = document.getElementById('rewardModalOverlay') || document.getElementById('adModalOverlay');
  if (modal) modal.classList.add('active');

  // Eğer AdBlock veya kurumsal ağ reklamları engelliyorsa otomatik Smartlink göster
  if (window.isAdBlocked) {
    switchToSmartlink();
  } else {
    switchToBannerAd();
  }
}

function switchToSmartlink() {
  const normalView = document.getElementById('rewardNormalView');
  const smartView  = document.getElementById('rewardSmartlinkView');
  if (normalView) normalView.style.display = 'none';
  if (smartView)  smartView.style.display  = 'block';
  clearInterval(adTimerInterval);
}

function loadModalBannerAd() {
  const container = document.getElementById('rewardAdContainer');
  if (!container) return;
  container.innerHTML = '';

  const iframe = document.createElement('iframe');
  iframe.id = 'modalAdIframe';
  iframe.style.width = '300px';
  iframe.style.height = '250px';
  iframe.style.border = 'none';
  iframe.style.overflow = 'hidden';
  iframe.scrolling = 'no';

  const adHtml = `<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <style>body{margin:0;padding:0;overflow:hidden;background:#fff;display:flex;align-items:center;justify-content:center;}</style>
  </head>
  <body>
    <script type="text/javascript">
      atOptions = {
        'key' : '5c72484b3cd463087eca96182a5ca135',
        'format' : 'iframe',
        'height' : 250,
        'width' : 300,
        'params' : {}
      };
    <\/script>
    <script type="text/javascript" src="https://consistinvention.com/5c72484b3cd463087eca96182a5ca135/invoke.js"><\/script>
  </body>
</html>`;

  container.appendChild(iframe);
  iframe.srcdoc = adHtml;
}

function switchToBannerAd() {
  const normalView = document.getElementById('rewardNormalView');
  const smartView  = document.getElementById('rewardSmartlinkView');
  if (normalView) normalView.style.display = 'block';
  if (smartView)  smartView.style.display  = 'none';
  loadModalBannerAd();
  startAdTimer(5);
}

function closeAdModal() {
  const modal = document.getElementById('rewardModalOverlay') || document.getElementById('adModalOverlay');
  if (modal) modal.classList.remove('active');
  clearInterval(adTimerInterval);
  const container = document.getElementById('rewardAdContainer');
  if (container) container.innerHTML = '';
}

function isBannerActuallyLoaded() {
  if (window.isAdBlocked) return false;
  const iframe = document.getElementById('modalAdIframe');
  if (!iframe) return false;
  try {
    const doc = iframe.contentDocument || iframe.contentWindow.document;
    if (!doc || !doc.body) return false;
    // Reklam yüklendiyse body içinde invoke.js tarafından oluşturulan bir iframe, a veya img olmalıdır
    const hasAdElements = doc.body.querySelector('iframe, a, img, div[id*="container-5c72484b"]');
    return !!hasAdElements;
  } catch (e) {
    // Cross-origin kısıtlaması oluştuysa reklam harici bir kaynaktan yüklenmiştir (başarılı)
    return true;
  }
}

function startAdTimer(seconds) {
  const timerEl  = document.getElementById('rewardTimerDisplay') || document.getElementById('adTimerDisplay');
  const claimBtn = document.getElementById('btnClaimReward');
  if (!claimBtn) return;
  claimBtn.disabled = true;
  claimBtn.innerText = `⏳ Lütfen bekleyin...`;
  claimBtn.onclick = claimReward;

  let remaining = seconds;
  if (timerEl) timerEl.innerText = remaining;

  clearInterval(adTimerInterval);
  adTimerInterval = setInterval(() => {
    remaining--;
    if (timerEl) timerEl.innerText = remaining;
    if (remaining <= 0) {
      clearInterval(adTimerInterval);

      // Reklamın gerçekten yüklenip yüklenmediğini doğrula
      if (isBannerActuallyLoaded()) {
        claimBtn.disabled = false;
        claimBtn.innerText = `🎁 Hakkı Al (+${adRewardCount} PDF)`;
        claimBtn.onclick = claimReward;
        if (timerEl) timerEl.innerText = '✓';
      } else {
        // Reklam yüklenmemiş veya ağ engellemiş -> Bedava hak verme, Smartlink'e yönlendir!
        claimBtn.disabled = false;
        claimBtn.style.background = '#2563EB';
        claimBtn.innerText = `⚡ Reklam Yüklenemedi ➔ Sponsor Linkiyle Hak Kazan`;
        claimBtn.onclick = switchToSmartlink;
        if (timerEl) timerEl.innerText = '⚠️';
      }
    }
  }, 1000);
}

async function claimReward() {
  // Ek güvenlik: Eğer reklam yüklenmediyse ve smartlink kullanılmadıysa hak verme
  if (!isBannerActuallyLoaded() && !window.isAdBlocked) {
    switchToSmartlink();
    return;
  }

  try {
    const resp = await fetch('/api/ad_reward', { method: 'POST' });
    const data = await resp.json();
    closeAdModal();

    // Kota güncelle
    if (typeof data.remaining !== 'undefined') {
      serverRemaining = data.remaining;
      updateQuotaUI(data.remaining);
    }
    alert(`✅ +${data.added} PDF hakkı eklendi! Artık ${data.remaining} hakkınız var.`);
  } catch (err) {
    alert('Hak eklenirken bir hata oluştu.');
  }
}

// Smartlink tıklandığında anında hakkı tanımla
async function handleSmartlinkClick() {
  const btn = document.getElementById('btnSmartlinkClaim');
  if (btn) {
    btn.innerHTML = '⏳ Hak Tanımlanıyor...';
    btn.style.pointerEvents = 'none';
    btn.style.opacity = '0.7';
  }

  // Kullanıcı yeni sekmede reklamı açarken sunucuya ödülü işle
  setTimeout(async () => {
    try {
      const resp = await fetch('/api/ad_reward', { method: 'POST' });
      const data = await resp.json();
      closeAdModal();

      if (typeof data.remaining !== 'undefined') {
        serverRemaining = data.remaining;
        updateQuotaUI(data.remaining);
      }
      alert(`🎉 Sponsor ziyareti için teşekkürler! +${data.added} PDF hakkı eklendi (Toplam: ${data.remaining} hak).`);
    } catch (e) {
      alert('Hak eklenirken bir sorun oluştu.');
    } finally {
      if (btn) {
        btn.innerHTML = `🚀 Sponsor Bağlantısını Aç (+${adRewardCount} Hak Al)`;
        btn.style.pointerEvents = 'auto';
        btn.style.opacity = '1';
      }
    }
  }, 1200);
}

// updateQuotaUI'yi global erişilebilir yap
function updateQuotaUI(remaining) {
  serverRemaining = remaining;
  const bar = document.getElementById('quotaBar');
  if (!bar) return;

  const textEl = bar.querySelector('.quota-text');
  if (textEl) {
    if (remaining > 0) {
      textEl.innerHTML = `📄 Günlük <strong>${remaining}</strong> PDF işleme hakkınız kaldı`;
    } else {
      textEl.innerHTML = `🚫 Günlük limitiniz doldu`;
    }
  }

  bar.className = 'quota-bar ' + (remaining >= 3 ? 'quota-ok' : remaining > 0 ? 'quota-low' : 'quota-out');

  let watchBtn = document.getElementById('watchAdBtn');
  if (!watchBtn) {
    watchBtn = document.createElement('button');
    watchBtn.className = 'btn-watch-ad';
    watchBtn.id = 'watchAdBtn';
    watchBtn.innerHTML = `📺 Reklam İzle +${adRewardCount} Hak Kazan`;
    watchBtn.onclick = openAdModal;
    bar.appendChild(watchBtn);
  }

  const startBtn = document.getElementById('webStartBtn');
  if (startBtn) startBtn.disabled = remaining <= 0;
}

// ─── ADBLOCK / KURUMSAL AĞ TESPİT SİSTEMİ ───────────────────────────────────────
function checkAdBlocker() {
  // Kullanıcı bu oturumda daha önce uyarışı kapattıysa modalı tekrar açma
  if (sessionStorage.getItem('ab_dismissed') === '1') {
    window.isAdBlocked = true;
    return;
  }

  let isBlocked = false;

  // 1. Yöntem: Tuzak (Bait) DOM Element Testi
  const bait = document.createElement('div');
  bait.innerHTML = '&nbsp;';
  bait.className = 'adsbox ad-placement ad-unit adsbygoogle doubleclick';
  bait.style.cssText = 'position: absolute !important; left: -9999px !important; top: -9999px !important; width: 1px !important; height: 1px !important; pointer-events: none;';
  document.body.appendChild(bait);

  window.setTimeout(() => {
    try {
      const baitStyle = window.getComputedStyle(bait);
      if (
        !bait ||
        bait.offsetParent === null ||
        bait.offsetHeight === 0 ||
        bait.offsetLeft === 0 ||
        baitStyle.getPropertyValue('display') === 'none' ||
        baitStyle.getPropertyValue('visibility') === 'hidden'
      ) {
        isBlocked = true;
      }
      bait.remove();
    } catch (e) {
      isBlocked = true;
    }

    // 2. Yöntem: Reklam Ağı İstek Testi
    fetch('https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js', {
      method: 'HEAD',
      mode: 'no-cors'
    }).catch(() => {
      isBlocked = true;
      markBlocked();
    }).then(() => {
      if (isBlocked) markBlocked();
    });

    if (isBlocked) markBlocked();
  }, 400);
}

function markBlocked() {
  window.isAdBlocked = true;
  if (sessionStorage.getItem('ab_dismissed') !== '1') {
    showAbNotice();
  }
}

function showAbNotice() {
  const overlay = document.getElementById('abNoticeOverlay');
  if (overlay) {
    overlay.classList.add('active');
  }
}

function dismissAbNotice() {
  const overlay = document.getElementById('abNoticeOverlay');
  if (overlay) {
    overlay.classList.remove('active');
  }
  sessionStorage.setItem('ab_dismissed', '1');
  window.isAdBlocked = true;
}

// Sayfa tamamen yüklendiğinde AdBlock kontrolü yap
window.addEventListener('load', () => {
  setTimeout(checkAdBlocker, 500);
});
