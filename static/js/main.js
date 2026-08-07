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
      if (webProgressBar) webProgressBar.style.width = '20%';
      if (logStatusText) logStatusText.innerText = 'İşleniyor...';

      logTerm('Fatura Aktarım İşlemi başlatıldı...');
      logTerm(`Excel Şablonu (${selectedExcelFile.name}) okunuyor...`);

      try {
        if (webProgressBar) webProgressBar.style.width = '50%';
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

        if (webProgressBar) webProgressBar.style.width = '90%';
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

        if (webProgressBar) webProgressBar.style.width = '100%';
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
    if (webProgressBar) webProgressBar.style.width = '0%';
    if (logStatusText)  logStatusText.innerText = '● Hazır — Dosyaları seçip İşlemi Başlatın';
  }

  // ilk yükleme
  updateQuotaUI(serverRemaining);
});

// ─── REKLAM İZLE MODAL ────────────────────────────────────────────────────────
let adTimerInterval = null;

function openAdModal() {
  document.getElementById('adModalOverlay').classList.add('active');
  startAdTimer(5);
}

function closeAdModal() {
  document.getElementById('adModalOverlay').classList.remove('active');
  clearInterval(adTimerInterval);
}

function startAdTimer(seconds) {
  const timerEl  = document.getElementById('adTimerDisplay');
  const claimBtn = document.getElementById('btnClaimReward');
  claimBtn.disabled = true;
  claimBtn.innerText = `⏳ Lütfen bekleyin...`;

  let remaining = seconds;
  timerEl.innerText = remaining;

  clearInterval(adTimerInterval);
  adTimerInterval = setInterval(() => {
    remaining--;
    timerEl.innerText = remaining;
    if (remaining <= 0) {
      clearInterval(adTimerInterval);
      claimBtn.disabled = false;
      claimBtn.innerText = `🎁 Hakkı Al (+${adRewardCount} PDF)`;
      timerEl.innerText = '✓';
    }
  }, 1000);
}

async function claimReward() {
  try {
    const resp = await fetch('/api/ad_reward', { method: 'POST' });
    const data = await resp.json();
    closeAdModal();

    // Kota güncelle
    if (typeof data.remaining !== 'undefined') {
      serverRemaining = data.remaining;
      updateQuotaUI(data.remaining);
      // updateQuotaUI global erişim için
    }
    alert(`✅ +${data.added} PDF hakkı eklendi! Artık ${data.remaining} hakkınız var.`);
  } catch (err) {
    alert('Hak eklenirken bir hata oluştu.');
  }
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
  if (remaining <= 2) {
    if (!watchBtn) {
      watchBtn = document.createElement('button');
      watchBtn.className = 'btn-watch-ad';
      watchBtn.id = 'watchAdBtn';
      watchBtn.innerHTML = `📺 Reklam İzle +${adRewardCount} Hak Kazan`;
      watchBtn.onclick = openAdModal;
      bar.appendChild(watchBtn);
    }
  } else {
    if (watchBtn) watchBtn.remove();
  }

  const startBtn = document.getElementById('webStartBtn');
  if (startBtn) startBtn.disabled = remaining <= 0;
}
