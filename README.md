# Screener Saham S&P 500 + Nasdaq-100

Website screener dengan 7 metode (Value, Growth, Quality, Dividen, Momentum, CAN SLIM, Swing), tab Ringkasan gabungan per saham, dan perbandingan ETF VOO / SPY / QQQ.

Data diperbarui otomatis **Selasa–Sabtu sekitar pukul 05.45 WIB** oleh GitHub Actions. Pengingat order dikirim ke Telegram **Senin–Jumat pukul 19.30 WIB** bila ada sinyal beli.

| Data | Sumber |
|---|---|
| Fundamental (P/E, ROE, margin, pertumbuhan, dividen) | Finnhub, paket gratis |
| Harga harian (SMA, RSI, kinerja, 52W high) | Yahoo Finance lewat `yfinance` |
| Daftar anggota indeks (diperbarui tiap 30 hari) | Wikipedia |

## Tujuh metode (aturan asli)

| Metode | Kapan beli | Kapan jual | Stop loss |
|---|---|---|---|
| Value (Graham) | 7 syarat investor defensif, P/E laba 3 tahun ≤ 15, P/E × P/B ≤ 22,5 | +50% atau setelah 2 tahun, atau dividen dihentikan | Tidak ada |
| Growth (Lynch) | Laba tumbuh 20–50%/thn, PEG plus dividen ≤ 1, neraca kuat | PEG ≥ 2 atau pertumbuhan melambat drastis | Tidak ada |
| Quality (Terry Smith) | ROIC ≥ 15%, margin kotor ≥ 40%, konversi kas ≥ 80%, FCF yield ≥ 2,5% | Kualitas memburuk atau FCF yield < 1,5% | Tidak ada |
| Dividen | Yield ≥ 2,5%, dividen naik 5 tahun, Chowder rule, payout ≤ 70% | Dividen dipotong atau payout > 100% | Tidak ada |
| CAN SLIM (O'Neil, Minervini) | C, A, ROE ≥ 17%, trend template, breakout base dengan volume ≥ 1,4×, pasar naik | Target +20% (aturan 8 minggu bila +20% dalam 3 minggu) | −7%, naik ke harga beli setelah +10% |
| Momentum (Jegadeesh & Titman) | Peringkat 12-1 bulan ≥ 90, dicek awal bulan | Peringkat turun di bawah 80 | Tidak ada |
| Swing (Connors RSI-2) | Di atas SMA200 dan RSI(2) < 10 | Menutup di atas SMA5 | Tidak ada |

- Metode trader diuji mundur setahun dari harga harian; metode investor dicatat maju di `data/signals.json` sejak hari pertama.
- Setiap sinyal menyertakan alasan dan harga patokan di website dan Telegram.

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

## Siklus & Fibonacci (tab "Siklus")

Analisis waktu dan harga dari teknik yang terbuka untuk umum: titik balik ZigZag, zona konfluensi Fibonacci (retracement, proyeksi, SMA50/200, angka bulat), kalender fase bulan, stasiun planet (Merkurius, Venus, Mars), Fibonacci time zone dan pola musiman, tanggal rawan pembalikan, rentang pergerakan mingguan, dan kesehatan pasar (breadth). Setiap unsur diuji terhadap tanggal acak pada riwayat indeks sejak 2005, dan setiap ramalan dicatat di papan skor sebelum terjadi. Kalender mingguan dikirim ke Telegram setiap Senin pagi.

## Struktur

```
index.html                     website
data/stocks.json               data terbaru (ditulis otomatis)
data/constituents.json         daftar anggota indeks (ditulis otomatis)
scripts/fetch_data.py          skrip pengambil data
scripts/strategies.py          aturan 7 metode
scripts/notify_telegram.py     pesan Telegram
.github/workflows/update-data.yml  jadwal otomatis
```

## Catatan

- Data kepemilikan institusi dan estimasi laba tahun depan tidak tersedia di paket gratis Finnhub, jadi kriteria CAN SLIM dan Growth disesuaikan.
- `yfinance` adalah pustaka tidak resmi. Jika Yahoo menolak permintaan, SMA, RSI, dan 52W high kosong untuk hari itu dan halaman menampilkan peringatan.
- Ini alat penyaring, bukan rekomendasi investasi.
