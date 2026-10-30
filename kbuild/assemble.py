# Menyusun kripto/index.html dari index.html (bagian bersama) + kbuild/*.js. Jalankan: python3 kbuild/assemble.py
import re, sys
import os
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent  # kbuild/ di dalam repo screener-saham
US = open(ROOT / "index.html", encoding="utf-8").read()
def between(a, b, inc_a=True):
    i = US.index(a); j = US.index(b, i + len(a))
    return US[i if inc_a else i + len(a): j]
def R(s, a, b, cnt=1):
    assert s.count(a) >= 1, ("missing", a[:80])
    if cnt == 1: assert s.count(a) == 1, ("multi", a[:80], s.count(a))
    return s.replace(a, b)
K = lambda f: open(HERE / f, encoding="utf-8").read()

head = US[:US.index("</style>")]
head = R(head, "<title>Screener Saham S&amp;P 500 + Nasdaq-100</title>", "<title>Screener Kripto · 50 koin terbesar di Indodax</title>")
head = R(head, '<meta name="description" content="Saring saham S&P 500 dan Nasdaq-100 dengan 7 metode investor dan trader, plus ringkasan gabungan per saham.">',
         '<meta name="description" content="50 koin kripto terbesar yang ada di Indodax, harga dalam Rupiah, Lampu BTC, metode Momentum 90 hari, area support, dan portofolio.">')
head = head.replace('href="icons/', 'href="../icons/')
head = re.sub(r'<script>try\{const q=new URLSearchParams\(location.search\);.*?</script>', '<script>try{localStorage.setItem("lastMarket","kripto");}catch(e){}</script>', head, count=1, flags=re.S)
css_add = """
.lampgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin-top:10px}
.lampx{display:flex;gap:10px;align-items:flex-start;padding:10px 12px;border-radius:14px;border:1px solid var(--line);background:var(--sunk)}
.lampx .bulb{font-size:26px;line-height:1}
.lampx.on{border-color:var(--good)}.lampx.off{border-color:var(--bad)}
#sellDlg{border:none;border-radius:18px;padding:0;width:min(460px,calc(100% - 24px));background:var(--surface);color:var(--fg);box-shadow:0 30px 80px rgba(0,0,0,.3)}
#sellDlg::backdrop{background:rgba(15,23,42,.45)}
#sellDlg .qsb{padding:16px}
@media (max-width:600px){.topbar{flex-wrap:wrap;row-gap:8px}.topbar .brand{margin-right:auto}.topbar .tb-r{display:contents}.topbar .mkt{order:9;width:100%;display:flex}.topbar .mkt a{flex:1;text-align:center;padding:6px 8px;font-size:13px}}
"""
body = """</style>
</head>
<body>
<aside class="sidenav" id="sidenav" aria-label="Menu samping"></aside>
<div class="wrap">
  <header class="topbar">
    <div class="brand"><img class="logo" src="../icons/icon-192.png" alt="" width="34" height="34"><div><b>Screener Kripto</b><span class="sub">50 koin terbesar di Indodax</span></div></div>
    <div class="tb-r"><nav class="mkt" aria-label="Pasar"><a href="https://sultanamra3-arch.github.io/screener-saham/">🇺🇸<span class="mt"> US</span></a><a href="https://sultanamra3-arch.github.io/screener-saham-indonesia/">🇮🇩<span class="mt"> ID</span></a><a href="https://sultanamra3-arch.github.io/screener-saham/kripto/" aria-current="page">₿<span class="mt"> Kripto</span></a></nav>
      <button type="button" id="install" hidden>📲 Pasang<span class="lg"> aplikasi</span></button>
      <button type="button" class="iconbtn" id="theme" aria-label="Ganti tema terang/gelap">🌙</button></div>
  </header>
  <nav class="mainnav" id="mainnav" aria-label="Menu utama"></nav>

  <section class="status" id="status" aria-live="polite"><span><span class="dot none"></span>Memuat data…</span></section>

  <div class="filters" id="filters">
    <div class="seg" role="group" aria-label="Pilihan koin">
      <button type="button" data-ix="ALL" aria-pressed="true">Semua</button>
      <button type="button" data-ix="TOP20" aria-pressed="false">20 terbesar</button>
      <button type="button" data-ix="NOMEME" aria-pressed="false">Tanpa meme</button>
    </div>
    <select id="sector" aria-label="Kategori"><option value="">Semua kategori</option></select>
    <input type="search" id="q" placeholder="Cari kode atau nama koin" aria-label="Cari kode atau nama koin">
  </div>

  <nav class="tabs" role="tablist" id="tabs" aria-label="Menu"></nav>

  <section class="main" id="main">
    <aside class="rail" id="rail"></aside>
    <div class="results" id="results"></div>
  </section>

  <footer>
    <p>Daftar koin dari CoinGecko (50 terbesar yang bisa dibeli di Indodax, tanpa stablecoin), harga harian dari Binance (USDT) dikonversi ke Rupiah dengan kurs Yahoo Finance, harga lokal dari Indodax. Diperbarui setiap jam. Candle harian ditutup pukul 07.00 WIB.</p>
    <p>Sinyal di sini adalah hitungan mekanis dari aturan metode, bukan saran investasi. Kripto sangat fluktuatif: harga bisa turun puluhan persen dalam hitungan hari. Uji mundur memakai data masa lalu dan tidak menjamin hasil berikutnya. Hanya transaksi spot (tanpa pinjaman/leverage).</p>
  </footer>
</div>

<script>
"""
cyc = between("// ---------- Siklus & Fibonacci ----------", "// ---------- Saran otomatis ----------")
cyc = R(cyc, 'placeholder="Kode saham" aria-label="Pilih saham"', 'placeholder="Kode koin" aria-label="Pilih koin"')
cyc = R(cyc, """const tvSym=IS_ID?(isIdx?"IDX:COMPOSITE":"IDX:"+sel):({"S&P 500":"SP:SPX","Nasdaq-100":"NASDAQ:NDX"}[sel]||sel);""", """const tvSym="BINANCE:"+sel+"USDT";""")
cyc = R(cyc, '<span class="note">· harga BEI tertunda ±15 menit</span>', '<span class="note">· harga real-time Binance (dalam USDT)</span>')
cyc = R(cyc, 'title="Grafik TradingView: harga lebih baru (tertunda ±15 menit), alat gambar dan indikator lengkap"', 'title="Grafik TradingView: harga real-time Binance dalam USDT, alat gambar dan indikator lengkap"')
cyc = R(cyc, "<div class=\"mcard\"><h4><span>Kesehatan pasar (${b.n} saham)</span></h4>", "<div class=\"mcard\"><h4><span>Kesehatan pasar (${b.n} koin)</span></h4>")
cyc = R(cyc, "% saham di atas SMA200 setahun terakhir. Di bawah 50% = mayoritas saham dalam tren turun.", "% koin di atas SMA200 setahun terakhir. Di bawah 50% = mayoritas koin dalam tren turun.")
cyc = R(cyc, "<h4><span>Status di 7 metode</span></h4>", "<h4><span>Status metode</span></h4>")
cyc = R(cyc, "${isIdx?nf(a.price,isIdx&&a.price>1000?0:2):usd(a.price)}", "${usd(isIdx&&o==null?(rows.find(x=>x.ticker===sel)||{}).price||a.price:(o?o.price:a.price))}")
cyc = R(cyc, "const pf=idr?{type:\"price\",precision:0,minMove:1}:{type:\"price\",precision:2,minMove:0.01};",
        "const pdec=decOf(C[C.length-1]||1), pf={type:\"price\",precision:pdec,minMove:Math.pow(10,-pdec)};")
cyc = R(cyc, 'crosshair:{mode:0},localization:{locale:"id-ID"}};', 'crosshair:{mode:0},localization:{locale:"id-ID",priceFormatter:v=>nf(v,pdec)}};')
cyc = R(cyc, "rightPriceScale:{borderColor:line,minimumWidth:78},timeScale", "rightPriceScale:{borderColor:line,minimumWidth:96},timeScale")
cyc = R(cyc, "const mf=idr?{type:\"price\",precision:0,minMove:1}:{type:\"price\",precision:2,minMove:0.01};", "const mf=pf;")
cyc = R(cyc, "lab.textContent=m!=null?`${nf(m,idr?0:2)} / ${nf(sg,idr?0:2)}`:\"\";", "lab.textContent=m!=null?`${nf(m,pdec)} / ${nf(sg,pdec)}`:\"\";")
cyc = R(cyc, "const fmtP=v=>idr?usd(Math.round(v)):usd(v);", "const fmtP=v=>usd(v);")
cyc = R(cyc, "Volume</b>: jumlah saham yang ditransaksikan.", "Volume</b>: jumlah koin yang ditransaksikan (di Binance).")
cyc = R(cyc, "<p class=\"note\" style=\"margin-top:8px\">Uji ketepatan dan papan skor tersedia di tampilan indeks.</p>", "<p class=\"note\" style=\"margin-top:8px\">Uji ketepatan dan papan skor tersedia di tampilan BTC.</p>")
cyc = cyc.replace("hari bursa", "hari")
saranh = between("const SAFE=!!window.CF_SAFE;", "function saranMarket(opt){")
saranh = saranh.replace('if(SAFE){ ST.buy="Memenuhi syarat"; }', 'if(SAFE){ ST.buy="Memenuhi syarat"; }')
star = between("const STAR_KEY", "function allowedMethods(){")
lad = between("function ladder(t,w){", "const rrTxt")
plan = between("function planOf(x){", "function planList(byT){")
nav = between("const groupOf=", "function renderDrawer(box){")
expl = between("// ---------- Penjelasan Siklus ----------", "// ---------- Peta sektor ----------").replace("hari bursa", "hari")
qs = between("// ---------- Pencarian cepat ----------", "function renderResults(){")
qs = R(qs, 'b.setAttribute("aria-label","Cari saham")', 'b.setAttribute("aria-label","Cari koin")')
qs = R(qs, 'placeholder="Ketik kode atau nama saham…"', 'placeholder="Ketik kode atau nama koin…"')
tail = between('(function(){ const b=$("theme");', "// ---------- boot ----------")
tail = R(tail, 'navigator.serviceWorker.register("sw.js")', 'navigator.serviceWorker.register("../sw.js")')
tail = R(tail, "const HOT_MIN = IS_ID ? 1e9 : 20e6; // nilai transaksi minimal hari ini: Rp1 miliar / $20 juta", "const HOT_MIN = 20e9; // nilai transaksi (Binance) sejak 07.00 WIB minimal Rp20 miliar")
i = tail.index("function renderHot(box){"); j = tail.index("// ---------- harga otomatis", i)
hot = tail[i:j]
hot = hot.replace("const minTx=IS_ID?\"Rp1 miliar\":\"$20 juta\";", "const minTx=\"Rp20 miliar\";")
hot = hot.replace("Di sini kelihatan saham yang lagi <b>diserbu</b> hari ini.", "Di sini kelihatan koin yang lagi <b>diserbu</b> hari ini.")
hot = hot.replace("Daftar saham dengan aktivitas transaksi paling menonjol hari ini.", "Daftar koin dengan aktivitas transaksi paling menonjol hari ini.")
hot = hot.replace("Volume <b>2×</b> artinya transaksinya dua kali lipat dari biasanya (rata-rata 20 hari).", "Volume <b>2×</b> artinya transaksinya dua kali lipat dari biasanya (rata-rata 20 hari, disesuaikan dengan jam yang sudah berjalan sejak 07.00 WIB).")
hot = hot.replace("`Harga sementara pukul ${jam}. Volume baru sebagian hari, jadi angka ×-nya masih akan bertambah sampai bursa tutup.`:`Data penutupan ${tgl(d.priceDate,1)}.`", "`Harga pukul ${jam}. Hari kripto dihitung sejak 07.00 WIB.`:`Data ${tgl(d.priceDate,1)}.`")
hot = hot.replace("Hanya saham dengan nilai transaksi hari ini minimal", "Hanya koin dengan nilai transaksi (Binance) hari ini minimal")
hot = hot.replace('<th>Saham</th>', '<th>Koin</th>').replace("10 kenaikan terbesar dari penutupan kemarin.", "10 kenaikan terbesar sejak 07.00 WIB.")
hot = hot.replace("Belum ada saham yang naik.", "Belum ada koin yang naik.").replace("Belum ada saham yang turun.", "Belum ada koin yang turun.")
hot = hot.replace("Tidak ada saham naik yang dekat resistance saat ini.", "Tidak ada koin naik yang dekat resistance saat ini.").replace("Berguna untuk mengecek saham di portofolio", "Berguna untuk mengecek koin di portofolio")
hot = hot.replace("Kalau ditutup di atas zona dengan volume besar, itu tanda tembus.", "Kalau candle harian ditutup di atas zona dengan volume besar, itu tanda tembus.")
tail = tail[:i] + hot + tail[j:]
boot = """// ---------- boot ----------
renderAll();
fetch("data/longtest.json",{cache:"no-cache"}).then(r=>r.ok?r.json():null).then(j=>{ if(j){ LT=j; if(DATA) renderAll(); } }).catch(()=>{});
fetch("data/stocks.json",{cache:"no-cache"}).then(r=>{ if(!r.ok) throw new Error(r.status); return r.json() }).then(d=>{
  DATA=d; rows=(d.stocks||[]).filter(s=>s&&s.ticker);
  const secs=[...new Set(rows.map(r=>r.sector).filter(Boolean))].sort();
  $("sector").insertAdjacentHTML("beforeend",secs.map(s=>`<option>${esc(s)}</option>`).join(""));
  renderAll();
}).catch(()=>{ DATA=null; renderAll(); });
})();
</script>
</body>
</html>
"""
core = K("core.js").replace("let openTicker=null;", "let openTicker=null;\nlet RSI14=null;")
out = head + css_add + body + core + "\n" + cyc + "\n// ---------- Saran: helper ----------\n" + saranh + "\n" + K("pages.js") + "\n// ---------- Watchlist: tanda bintang ----------\n" + star + "\n" + lad + "\n" + plan + "\n" + K("pages2.js") + "\n" + nav + "\n" + expl + "\n" + K("pages3.js") + "\n" + qs + "\n" + tail + boot
import os
os.makedirs(ROOT / "kripto", exist_ok=True)
open(ROOT / "kripto" / "index.html", "w", encoding="utf-8").write(out)
print(len(out.splitlines()), "baris")
