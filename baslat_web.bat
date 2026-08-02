@echo off
title Fatura Web Sunucusu
color 0A
echo ============================================
echo  TSE Fatura Web Uygulamasi Baslatiliyor...
echo ============================================
echo.

:: FATURA2026.xlsx şablonunu Projects\Fatura'dan kopyala
if not exist "FATURA2026.xlsx" (
    if exist "..\Fatura\FATURA2026.xlsx" (
        copy "..\Fatura\FATURA2026.xlsx" "FATURA2026.xlsx" > nul
        echo [OK] Excel sablonu kopyalandi.
    ) else (
        echo [UYARI] FATURA2026.xlsx bulunamadi!
        echo Lutfen sablon dosyasini C:\Projects\FaturaWeb\ klasorune kopyalayin.
    )
)

:: Klasörleri oluştur
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs

echo [OK] Sunucu baslatiliyor... http://localhost:5000 adresini aciniz.
echo.
"C:\Users\omer\AppData\Local\Programs\Python\Python311\python.exe" app.py
pause
