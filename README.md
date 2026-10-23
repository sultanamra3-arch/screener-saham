# Screener Saham S&P 500 + Nasdaq-100

Website screener dengan 7 metode (Value, Growth, Quality, Dividen, Momentum, CAN SLIM, Swing), tab Ringkasan gabungan per saham, dan perbandingan ETF VOO / SPY / QQQ.

Data diperbarui otomatis setiap **Selasa–Sabtu pukul 06.00 WIB** oleh GitHub Actions.

| Data | Sumber |
|---|---|
| Fundamental (P/E, ROE, margin, pertumbuhan, dividen) | Finnhub, paket gratis |
| Harga harian (SMA, RSI, kinerja, 52W high) | Yahoo Finance lewat `yfinance` |
| Daftar anggota indeks (diperbarui tiap 30 hari) | Wikipedia |

## Harga beli / tunggu / jual

- **Investor**: nilai wajar = P/E median sektor (dibatasi 10–30) × EPS, dirata-rata dengan angka Graham bila relevan. Beli di bawah nilai wajar dikurangi *margin of safety* (default 25%), jual di atas nilai wajar ditambah premi (default 20%). Saham dengan EPS negatif tidak dinilai.
- **Trader**: area masuk di SMA20 (pullback) atau 52W high (breakout), stop loss 8%, target 25%. Jual bila harga di bawah SMA50/SMA200 atau target tercapai.
- Persentase bisa diubah di website dan tersimpan di browser.
- **Kapan beli / jual**: sinyal trader diuji mundur hari demi hari selama setahun dari harga harian (tanggal, harga, alasan jual, hasil). Status investor dicatat setiap pembaruan ke `data/signals.json`, sehingga terlihat sejak kapan dan di harga berapa status berubah.

## Langkah pemasangan (sekali saja)

1. **Simpan API key Finnhub**
   Settings → Secrets and variables → Actions → **New repository secret**
   - Name: `FINNHUB_API_KEY`
   - Secret: API key dari dashboard finnhub.io

2. **Aktifkan GitHub Pages**
   Settings → Pages → Build and deployment
   - Source: **Deploy from a branch**
   - Branch: **main**, folder **/ (root)** → Save

3. **Jalankan pengambilan data pertama**
   Tab **Actions** → **Update data saham** → **Run workflow**. Tunggu sekitar 15 menit sampai centang hijau.

4. **Buka website**: `https://sultanamra3-arch.github.io/screener-saham/`

## Notifikasi Telegram (opsional)

Setiap selesai pembaruan, bot mengirim sinyal BELI/JUAL baru (trader dan investor) lengkap dengan harga beli, stop loss/jual, dan target, plus saham yang lolos ≥4 metode. Jika pembaruan gagal, bot mengirim peringatan.

1. Di Telegram buka **@BotFather** → `/newbot` → salin token.
2. Kirim pesan apa saja ke bot Anda.
3. Buka `https://api.telegram.org/bot<TOKEN>/getUpdates` di browser, catat angka `"chat":{"id": ...}`.
4. Simpan secret `TELEGRAM_BOT_TOKEN` dan `TELEGRAM_CHAT_ID` di Settings → Secrets and variables → Actions.

## Struktur

```
index.html                     website
data/stocks.json               data terbaru (ditulis otomatis)
data/constituents.json         daftar anggota indeks (ditulis otomatis)
scripts/fetch_data.py          skrip pengambil data
.github/workflows/update-data.yml  jadwal otomatis
```

## Catatan

- Data kepemilikan institusi dan estimasi laba tahun depan tidak tersedia di paket gratis Finnhub, jadi kriteria CAN SLIM dan Growth disesuaikan.
- `yfinance` adalah pustaka tidak resmi. Jika Yahoo menolak permintaan, SMA, RSI, dan 52W high kosong untuk hari itu dan halaman menampilkan peringatan.
- Ini alat penyaring, bukan rekomendasi investasi.
