# Screener Saham S&P 500 + Nasdaq-100

Website screener dengan 7 metode (Value, Growth, Quality, Dividen, Momentum, CAN SLIM, Swing), tab Ringkasan gabungan per saham, dan perbandingan ETF VOO / SPY / QQQ.

Data diperbarui otomatis setiap **Selasa–Sabtu pukul 06.00 WIB** oleh GitHub Actions.

| Data | Sumber |
|---|---|
| Fundamental (P/E, ROE, margin, pertumbuhan, dividen) | Finnhub, paket gratis |
| Harga harian (SMA, RSI, kinerja, 52W high) | Yahoo Finance lewat `yfinance` |
| Daftar anggota indeks (diperbarui tiap 30 hari) | Wikipedia |

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
