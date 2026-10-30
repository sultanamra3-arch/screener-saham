// ---------- Saran: bahasa sehari-hari (kripto) ----------
function momRisk(){ const R=LT&&LT.mom; if(!R) return "";
  const ym=x=>{ const [y,m]=x.split("-"); return ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"][+m-1]+" "+y; };
  return `<div class="mcard" style="margin-top:12px;border-left:4px solid var(--bad);gap:6px"><h4><span>⚠️ Risiko: uji ${R.from.slice(0,4)}–${R.to.slice(0,4)} (${LT.trend?nf(LT.trend.n,0):"±120"} koin)</span></h4>
    <div class="tablebox"><table class="nocard"><thead><tr><th>Saat Bitcoin jatuh</th><th class="num">Bitcoin</th><th class="num">Momentum 90 hari</th></tr></thead><tbody>
    ${R.crash.map(c=>`<tr><td>${ym(c.a)} – ${ym(c.b)}</td><td class="num no">${pct(c.btc,0)}</td><td class="num ${c.mom>=0?"ok":"no"}">${pct(c.mom,0)}</td></tr>`).join("")}</tbody></table></div>
    <p style="margin:0;font-size:14px">Lampu BTC menolong saat Bitcoin jatuh. Tapi penurunan <b>terdalam justru ${pct(R.dd,0)}</b>, terjadi di ${Object.entries(R.bad).map(([y,v])=>`${y} (${pct(v,0)})`).join(" dan ")} ketika Bitcoin naik tetapi koin lain melemah. Rata-rata ${pct(R.cagr,1)}/tahun, dibanding simpan Bitcoin ${pct(R.btc_cagr,1)}/tahun (turun terdalam ${pct(R.btc_dd,0)}).</p>
    <p class="note">${T("Artinya: dari Rp10 juta, pernah tinggal sekitar Rp1,3 juta, dan sampai sekarang belum kembali ke puncaknya. Hanya pakai uang yang benar-benar siap hilang sebagian besar.","Kripto berisiko sangat tinggi; nilai dapat turun sebagian besar. Hasil masa lalu tidak menjamin hasil berikutnya.")} Uji memakai koin yang masih ada hari ini, jadi hasil sebenarnya lebih rendah.</p></div>`; }
function regime(){ const L=lamp(); return {k:L.g50==null?"campuran":L.g50?"naik":"tertekan", L}; }
function lampSince(L){ if(!L.since) return ""; const d=Math.round((Date.now()-new Date(L.since))/864e5); return d<=1?"sejak kemarin":`sejak ${tgl(L.since)} (${d} hari)`; }
function saranMarket(opt){
  const L=lamp(), g=!!L.g50, g2=!!L.g200, mo=(DATA&&DATA.mom)||{};
  let c,title,why,Ln=[],foot="";
  if(SAFE){ c=g?"g":"r"; title=`Lampu BTC: ${g?"hijau":"merah"}.`;
    why=`Bitcoin ${nf(Math.abs(L.d50),1)}% ${g?"di atas":"di bawah"} rata-rata 50 harinya ${lampSince(L)}.`;
    Ln.push(g?"ℹ️ Secara historis, membeli altcoin saat lampu hijau jauh lebih baik daripada saat merah.":"ℹ️ Secara historis, membeli altcoin saat lampu merah rata-rata merugi. Metode Momentum tidak membeli apa pun di kondisi ini.");
  } else if(g){ c="g"; title=pick(["Lampu BTC hijau. Pasar kripto lagi bersahabat.","Bitcoin lagi kuat. Boleh mulai berburu altcoin.","Angin lagi bagus di kripto. Silakan aktif, tapi tetap disiplin."],"m");
    why=`Bitcoin ${nf(Math.abs(L.d50),1)}% di atas rata-rata 50 harinya ${lampSince(L)}. Saat begini, kebanyakan koin ikut terangkat.`;
    Ln.push("✔️ Fokus ke koin yang lagi paling kuat (lihat Momentum 90 hari), jangan ke koin yang tertinggal.","✔️ Bagi modal ke beberapa koin, jangan semua di satu koin.",`✔️ Kalau lampu berubah merah, kurangi posisi altcoin. Jangan menunggu “nanti juga naik lagi”.`);
  } else { c="r"; title=pick(["Lampu BTC merah. Tahan diri dulu.","Bitcoin lagi lemah. Altcoin biasanya ikut jatuh lebih dalam.","Cuaca kripto lagi mendung. Utamakan menjaga modal."],"m");
    why=`Bitcoin ${nf(Math.abs(L.d50),1)}% di bawah rata-rata 50 harinya ${lampSince(L)}. Di kondisi begini, altcoin rata-rata turun lebih dalam dari BTC.`;
    Ln.push("✔️ Jangan beli altcoin baru dulu. Di uji mundur, beli asal saat lampu merah rata-rata rugi.","✔️ Kalau sudah punya, pertimbangkan jual yang harganya di bawah rata-rata 50 hari.",
      g2?"ℹ️ Tren besar BTC (rata-rata 200 hari) masih naik, jadi ini bisa jadi koreksi biasa.":"⚠️ BTC juga di bawah rata-rata 200 hari: tren besar sedang turun. Ini fase paling berbahaya.");
    foot=`Lampu kembali hijau kalau BTC ditutup di atas ${usd(L.s50)} (rata-rata 50 hari).`; }
  const html=`<div class="sv"><div class="svh sv-${c}">${SV[c]} ₿ ${title}</div><p style="margin:4px 0 0">${why}</p>${Ln.length?`<ul class="sl">${Ln.map(l=>`<li>${l}</li>`).join("")}</ul>`:""}${foot?`<p class="note" style="margin:6px 0 0">${foot}</p>`:""}</div>`;
  return {r:regime(),html,head:`<div class="sv"><div class="svh sv-${c}">${SV[c]} ₿ ${title}</div><p style="margin:4px 0 0">${why}</p></div>`};
}
let PLAN_MEMO=null;
function planFor(t){ if(!CYC||!CYC.watch) return null; if(!PLAN_MEMO||PLAN_MEMO.k!==CYC){ PLAN_MEMO={k:CYC,m:new Map(planList(Object.fromEntries(rows.map(o=>[o.ticker,o]))).list.map(x=>[x.t,x.pl]))}; } return PLAN_MEMO.m.get(t)||null; }
function nearZones(t){ const a=CYC&&CYC.stocks&&CYC.stocks[t]; if(!a) return null; return {s:(a.sup||[])[0], r:strongRes(a), a}; }
function zr(z){ return z.hi!==z.lo?`${usd(z.lo)}–${usd(z.hi)}`:usd(z.lo); }
function saranStock(o){
  const u=uv(o,"mom90"), own=owned(o.ticker), z=nearZones(o.ticker), p=o.price, L=lamp(), pl=planFor(o.ticker), Ln=[];
  const sup=z&&z.s, res=z&&z.r, pc=(a,b)=>nf(Math.abs((a/b-1)*100),1)+"%";
  let c,title;
  if(o.ticker==="BTC"){
    c=L.g200?"g":"r"; title=SAFE?`BTC ${L.g200?"di atas":"di bawah"} rata-rata 200 hari.`:L.g200?pick(["Tren besar BTC masih naik.","BTC masih di jalur naik jangka panjang."],"b"):pick(["Tren besar BTC sedang turun.","BTC lagi di bawah tren jangka panjangnya."],"b");
    Ln.push(`📏 Rata-rata 50 hari ${usd(L.s50)} (${pct(L.d50,1)}) · rata-rata 200 hari ${usd(L.s200)} (${pct(L.d200,1)}).`);
    Ln.push(L.g200?(SAFE?"ℹ️ Aturan BTC Tren 200: simpan BTC selama ditutup di atas rata-rata 200 hari.":"✔️ Untuk simpan BTC jangka panjang: tahan selama masih di atas rata-rata 200 hari."):(SAFE?"ℹ️ Aturan BTC Tren 200: di luar pasar sampai BTC kembali di atas rata-rata 200 hari.":"✖️ Untuk simpan BTC: tunggu dulu sampai kembali di atas rata-rata 200 hari. Di uji mundur, aturan ini memotong kejatuhan terdalam dari −77% jadi −37%."));
  } else if(own){
    const P=porto().open.find(x=>x.code===o.ticker), e=P?posEval(P):null, hot=e?e.acts.filter(a=>a.lv<=1):[];
    c="o"; title=hot.length?(SAFE?"Ada aturan jual yang terpenuhi.":pick(["Waktunya mempertimbangkan jual.","Ada tanda untuk menjual."],o.ticker)):(SAFE?"Belum ada aturan jual yang terpenuhi.":pick(["Tahan dulu, belum ada alasan jual.","Masih aman, tahan saja."],o.ticker));
    if(e&&e.plp!=null) Ln.push(`💰 Posisi Anda ${e.plp>=0?"untung":"rugi"} ${nf(Math.abs(e.plp),1)}% (${e.pl>=0?"+":"−"}${usd(Math.abs(e.pl))}).`);
    hot.forEach(a=>Ln.push(`${a.ic} ${esc(a.t[0].toUpperCase()+a.t.slice(1))}.`));
    if(!hot.length&&sup) Ln.push(`🛑 Waspada kalau harga ditutup di bawah ${usd(floorTick(sup.lo*0.99))}: ${tip("lantai harga","support")} terdekat jebol.`);
    if(res) Ln.push(`📈 Kenaikan mungkin tertahan di sekitar ${usd(res.lo)} (${pc(res.lo,p)} lagi).`);
  } else if(u.s==="sell"){ c="r"; title=SAFE?"Baru keluar dari metode Momentum.":pick(["Baru dijual metode Momentum. Lewati dulu.","Momentumnya sudah habis. Jangan dikejar."],o.ticker);
    Ln.push(`👎 ${esc(u.r||"")}`);
  } else if(u.s==="buy"){ c=L.g50?"g":"y"; title=SAFE?"Memenuhi syarat metode Momentum 90 hari.":pick(["Lagi jadi pilihan metode Momentum.","Termasuk koin paling kuat saat ini."],o.ticker);
    Ln.push(`👍 Kenaikan 90 harinya ${pct(o.perf90,0)}, peringkat #${o.rk90} dan lebih kuat dari BTC.`);
    Ln.push(SAFE?`ℹ️ Aturan metode: dipegang selama masih 8 teratas, di atas rata-rata 50 hari (${usd(u.lv&&u.lv.exit)}), dan Lampu BTC hijau.`:`✔️ Kalau ikut, porsinya cukup 1/5 dari dana kripto Anda. Jual kalau ditutup di bawah ${usd(u.lv&&u.lv.exit)} (rata-rata 50 hari) atau saat cek Senin keluar dari 8 besar.`);
    if(pl&&pl.kind==="queue") Ln.push(`🎯 Lebih hemat kalau menunggu turun ke sekitar ${usd(pl.e)} (${tip("lantai harga","support")}).`);
    if(o.rsi14>=75) Ln.push(SAFE?`ℹ️ RSI ${nf(o.rsi14,0)}: sudah panas.`:`⚠️ RSI ${nf(o.rsi14,0)}: sudah panas, jangan beli sekaligus. Cicil.`);
  } else if(pl){ c=L.g50?"y":"n"; title=SAFE?"Harga di area support.":L.g50?pick(["Lagi di lantai harga. Boleh dilirik.","Harga sedang di area support."],o.ticker):pick(["Di area support, tapi lampu BTC merah.","Murah, tapi pasarnya lagi lemah."],o.ticker);
    Ln.push(pl.kind==="now"?`🎯 Area beli sekitar <b>${usd(pl.e)}</b>, batas rugi <b>${usd(pl.stop)}</b> (harga penutupan).`:`🎯 Area beli di <b>${usd(pl.e)}</b> (${pc(pl.e,p)} di bawah harga sekarang). Batal kalau tembus ${usd(pl.stop)}.`);
    if(pl.tgt) Ln.push(`📈 Target wajar sekitar <b>${usd(pl.tgt)}</b> (+${nf((pl.tgt/pl.e-1)*100,1)}%).`);
    if(!L.g50) Ln.push(SAFE?"⚠️ Lampu BTC merah: support lebih sering jebol.":"⚠️ Lampu BTC merah: support lebih gampang jebol. Kalau tetap mau, beli kecil saja.");
  } else { c="n"; title=SAFE?"Belum memenuhi syarat metode.":pick(["Belum menarik. Pantau saja.","Belum ada alasan untuk membeli."],o.ticker);
    Ln.push(`🔎 ${esc(u.r||"Belum masuk kriteria Momentum 90 hari.")}`);
    if(sup&&p) Ln.push(`📌 ${tip("Lantai harga","support")} terdekat: ${zr(sup)} (${pc(sup.hi,p)} di bawah).`); }
  if(o.sector===MEME) Ln.push(SAFE?"ℹ️ Koin meme: tanpa kegunaan nyata, harganya digerakkan sentimen.":"⚠️ Koin meme: naik-turunnya liar dan murni sentimen. Kalau ikut, pakai uang yang siap hilang.");
  if(o.idx&&o.price&&Math.abs(o.idx/o.price-1)>=0.02) Ln.push(`ℹ️ Harga di Indodax ${usd(o.idx)}, beda ${pct((o.idx/o.price-1)*100,1)} dari harga dunia.`);
  return svBox(c,`<b>${title}</b>`,Ln,"");
}
function saranBox(inner){
  return `<div class="mcard" style="border-left:4px solid var(--accent);gap:6px;font-size:14px"><h4><span>${SAFE?"💡 Keterangan":"💡 Saran"}</span><span class="note" style="font-weight:400">${SAFE?"informasi edukasi, bukan ajakan membeli atau menjual":"hitungan otomatis, bukan nasihat keuangan pribadi"}</span></h4>${inner}${SAFE?'<p class="note" style="margin:8px 0 0">Hitungan otomatis dari aturan metode publik. Keputusan dan risiko sepenuhnya di tangan Anda.</p>':""}</div>`;
}
let SARAN_LOADED=false;

// ---------- Beranda ----------
function lampCard(big){
  const L=lamp(); if(L.g50==null) return "";
  const one=(on,lbl,d,ma,txt)=>`<div class="lampx ${on?"on":"off"}"><span class="bulb" aria-hidden="true">${on?"🟢":"🔴"}</span><span><b>${lbl}</b><br><span class="note">BTC ${pct(d,1)} dari rata-rata ${ma} hari (${usd(ma==="50"?L.s50:L.s200)})</span><br><span style="font-size:13px">${txt}</span></span></div>`;
  return `<div class="lampgrid">${one(L.g50,"Trading altcoin",L.d50,"50",L.g50?"Boleh aktif, ikuti metode Momentum.":"Jangan beli altcoin baru.")}${one(L.g200,"Simpan BTC jangka panjang",L.d200,"200",L.g200?"Tren besar naik: aman menyimpan BTC.":"Tren besar turun: tunggu dulu.")}</div>`;
}
function renderSummary(box){
  if(!CYC&&!CYC_ERR&&!SARAN_LOADED){ SARAN_LOADED=true; loadCycles().then(()=>{ if(tab==="summary") renderResults(); }); }
  const list=filtered(), mo=(DATA&&DATA.mom)||{}, sm=saranMarket();
  const held=rows.filter(o=>["buy","hold"].includes(mget(o,"mom90").s)).map(o=>({o,st:mget(o,"mom90")}));
  const H=hotLists(list);
  const heldHtml=held.length?`<div class="dl">${held.map(x=>`<div class="row" data-t="${esc(x.o.ticker)}" style="cursor:pointer"><span><b class="tk">${esc(x.o.ticker)}</b> ${usd(x.o.price)}<br><span class="note">masuk ${tgl(x.st.b)} · peringkat #${x.o.rk90||"–"}</span></span><span class="num ${x.st.ret>=0?"ok":"no"}">${pct(x.st.ret)}</span></div>`).join("")}</div>`
    :`<p class="note" style="margin:4px 0">${lamp().g50?"Belum ada koin yang memenuhi syarat. Cek berikutnya "+tgl(mo.next,1)+".":"Kosong: metode tidak membeli saat Lampu BTC merah. Dana disimpan dulu."}</p>`;
  const sel=store.get(WP+"sort")||"rank";
  const sorted=list.slice().sort((a,b)=>sel==="rank"?(a.rank||999)-(b.rank||999):sel==="d1"?(b.chg1d??-1e9)-(a.chg1d??-1e9):sel==="m90"?(b.perf90??-1e9)-(a.perf90??-1e9):(b.volR??-1)-(a.volR??-1));
  box.innerHTML=saranBox(sm.html+lampCard()+`<p style="margin-top:12px"><b>${T("📈 Dipegang metode Momentum 90 hari","📈 Koin dalam simulasi metode Momentum 90 hari")}</b></p>${heldHtml}`
      +(H.spike.length?`<p class="note" style="margin-top:8px">🔥 Volume melonjak hari ini: ${H.spike.slice(0,4).map(o=>`<b>${esc(o.ticker)}</b> ${nf(o.volR,1)}×`).join(" · ")} (lihat Alat → Ramai hari ini).</p>`:""))
    +`<div class="rhead"><div class="l"><h2>${list.length} koin terbesar di Indodax</h2><p class="note">Harga dunia (Binance) dalam Rupiah. “Hari ini” dihitung sejak 07.00 WIB. Klik baris untuk penjelasan lengkap.</p></div>
      <label for="kSort">Urutkan <select id="kSort">${[["rank","Kapitalisasi"],["d1","Naik hari ini"],["m90","Kenaikan 90 hari"],["vol","Volume vs biasa"]].map(([v,t])=>`<option value="${v}" ${v===sel?"selected":""}>${t}</option>`).join("")}</select></label></div>
    <div class="tablebox"><table><thead><tr><th>Koin</th><th class="num">Harga</th><th class="num">Hari ini</th><th class="num">7 hari</th><th class="num">30 hari</th><th class="num">90 hari</th><th class="num">vs MA50</th><th>Momentum</th></tr></thead><tbody>
    ${sorted.length?sorted.map(o=>{ const u=uv(o,"mom90"); return `<tr class="row" data-t="${esc(o.ticker)}" tabindex="0">${stockCell(o)}<td class="num">${usd(o.price)}${o.idx?`<br><span class="note">Indodax ${usd(o.idx)}</span>`:""}</td>${chgCell(o.chg1d)}${chgCell(o.perf1w)}${chgCell(o.perf1m)}${chgCell(o.perf90)}${chgCell(o.sma50)}<td>${uchip(u)}${o.rk90&&u.s!=="na"?` <span class="note">#${o.rk90}</span>`:""}</td></tr>`; }).join("")
      :`<tr><td colspan="8" class="empty">Tidak ada koin yang cocok dengan filter ini.</td></tr>`}</tbody></table></div>`;
  $("kSort").addEventListener("change",ev=>{ store.set(WP+"sort",ev.target.value); renderResults(); });
}
// ---------- Lampu BTC ----------
function renderLamp(box){
  const L=lamp(), b=rows.find(o=>o.ticker==="BTC")||{};
  box.innerHTML=saranBox(saranMarket().html+lampCard(true))+`
    <div class="dgrid" style="margin-top:12px">
      <div class="mcard"><h4><span>₿ Bitcoin sekarang</span></h4><div class="dl">
        <div><span>Harga</span><span class="num">${usd(b.price)} · ${usdx(b.usd)}</span></div>
        <div><span>Penutupan candle terakhir (${tgl(L.date)})</span><span class="num">${usd(L.close)}</span></div>
        <div><span>Rata-rata 50 hari</span><span class="num">${usd(L.s50)} <span class="${L.g50?"ok":"no"}">(${pct(L.d50,1)})</span></span></div>
        <div><span>Rata-rata 200 hari</span><span class="num">${usd(L.s200)} <span class="${L.g200?"ok":"no"}">(${pct(L.d200,1)})</span></span></div>
        <div><span>Warna lampu 50 hari ${L.g50?"hijau":"merah"}</span><span class="num">${L.since?lampSince(L):"–"}</span></div></div>
        <p class="note">Lampu dinilai dari harga penutupan candle harian (ditutup 07.00 WIB), bukan harga sesaat, supaya tidak berkedip-kedip.</p>
        <p style="margin-top:6px">${chartBtn("BTC","📈 Grafik BTC")}</p></div>
      <div class="mcard"><h4><span>Kenapa lampu ini paling penting</span></h4>
        <p style="font-size:14px">Hampir semua koin bergerak mengikuti Bitcoin. Di uji mundur (Jan 2021–Okt 2026, 50 koin terbesar di Indodax, biaya 0,3% per transaksi):</p>
        <div class="tablebox"><table class="nocard" style="min-width:0"><thead><tr><th>Cara</th><th class="num">Untung/tahun</th><th class="num">Turun terdalam</th></tr></thead><tbody>
          <tr><td>Beli koin acak, lihat lampu 50 hari</td><td class="num ok">+19%</td><td class="num no">−66%</td></tr>
          <tr><td>Beli koin acak, abaikan lampu</td><td class="num no">−6%</td><td class="num no">−86%</td></tr>
          <tr><td>Beli-tahan BTC</td><td class="num ok">+19%</td><td class="num no">−77%</td></tr>
          <tr><td><b>BTC Tren 200</b> (simpan BTC hanya di atas rata-rata 200 hari)</td><td class="num ok">+13%</td><td class="num no">−37%</td></tr>
        </tbody></table></div>
        <p class="note">Lampu tidak membuat untung lebih besar di setiap tahun; gunanya menghindari kejatuhan besar seperti 2022. Hasil masa lalu tidak menjamin masa depan.</p></div>
      <div class="mcard"><h4><span>Aturan BTC Tren 200 (untuk simpan jangka panjang)</span></h4><ul class="sl">
        <li>Beli/simpan BTC saat ditutup <b>di atas</b> rata-rata 200 hari.</li><li>Jual saat ditutup <b>di bawah</b> rata-rata 200 hari, tunggu sampai kembali di atasnya.</li>
        <li>Paling sedikit transaksi (beberapa kali setahun), cocok untuk yang tidak sempat memantau.</li></ul>
        <p>Status sekarang: ${L.g200?'<span class="st buy">✅ boleh simpan BTC</span>':'<span class="st wait">⏸ di luar pasar</span>'}</p></div>
    </div>`;
}
// ---------- Momentum 90 hari ----------
function renderMethod(box,m){
  const mo=(DATA&&DATA.mom)||{}, list=filtered();
  const U=new Map(list.map(o=>[o.ticker,uv(o,m.id)])), gu=o=>U.get(o.ticker);
  const held=list.filter(o=>["buy","hold"].includes(mget(o,m.id).s)), cand=list.filter(o=>mget(o,m.id).s==="wait"&&mget(o,m.id).p), sold=list.filter(o=>mget(o,m.id).s==="sell");
  const rest=list.filter(o=>!held.includes(o)&&!cand.includes(o)&&!sold.includes(o)).sort((a,b)=>(a.rk90||999)-(b.rk90||999));
  const row=o=>{ const st=gu(o), lv=levels(m.id,st);
    return `<tr class="row" data-t="${esc(o.ticker)}" tabindex="0" aria-expanded="${openTicker===o.ticker}">${stockCell(o)}<td class="num">${usd(o.price)}</td>
      <td>${uchip(st)}${lv?`<span class="lvl">${lv}</span>`:""}</td><td class="why">${esc(st.why&&st.s!=="buy"?st.why:st.rs||"")}</td>
      <td><div class="pips">${critStates(st).filter(c=>c[2]!==2).map(c=>`<span class="pip ${c[2]===1?"y":""}" title="${esc(c[0])}"></span>`).join("")}</div></td>
      ${m.cols.map(c=>`<td class="num">${fmtCol(c[0],o[c[0]],c[2])}</td>`).join("")}</tr>`; };
  const head=`<tr><th>Koin</th><th class="num">Harga</th><th>Status</th><th>Alasan</th><th>Syarat</th>${m.cols.map(c=>`<th class="num">${esc(c[1])}</th>`).join("")}</tr>`;
  const sec=(t,n,L,empty)=>`<div class="rhead" style="margin-top:14px"><div class="l"><h2>${t}</h2>${n?`<p class="note">${n}</p>`:""}</div></div><div class="tablebox"><table><thead>${head}</thead><tbody>${L.length?L.map(row).join(""):`<tr><td colspan="9" class="empty">${empty}</td></tr>`}</tbody></table></div>`;
  const yr=mo.yearly||{};
  box.innerHTML=saranBox(saranMarket().head+`<ul class="sl"><li>📅 Dicek seminggu sekali: candle <b>Senin</b>, hasilnya muncul <b>Selasa sekitar 07.30 WIB</b>. Berikutnya: ${tgl(mo.next,1)}.</li>
      <li>⚖️ ${T("Bagi dana kripto jadi 5 bagian sama besar, satu bagian per koin.","Aturan metode: dana dibagi 5 bagian sama besar, satu per koin.")}</li>
      <li>⚠️ Metode ini bisa turun sangat dalam (terdalam ${pct(mo.dd,0)}) dan 2024–2025 hasilnya jelek. ${T("Pakai uang yang siap ditinggal lama.","Risikonya tinggi.")}</li></ul>`)
    +momRisk()
    +`<div class="mcard" style="margin-top:12px"><h4><span>📊 Hasil simulasi per tahun</span><span class="note" style="font-weight:400">sejak ${tgl(mo.from,1)}, setelah biaya</span></h4>
      <div class="statgrid">${Object.entries(yr).map(([y,v])=>`<div>${esc(y)}${(+y===new Date().getFullYear())?" (berjalan)":""}<b class="${v>=0?"ok":"no"}">${pct(v,0)}</b></div>`).join("")}</div>
      <div id="momEq" style="width:100%;height:180px;margin-top:8px"></div>
      <p class="note">Garis: nilai Rp1 yang diputar dengan metode ini (skala log). ${mo.cagr!=null?`Rata-rata ${pct(mo.cagr,1)}/tahun, turun terdalam ${pct(mo.dd,0)}, ${mo.n} transaksi, ${nf(mo.win,0)}% untung.`:""}</p></div>`
    +sec(`📈 Dipegang sekarang (${held.length})`,"Simulasi metode. Pembeli baru boleh ikut selama statusnya masih Layak beli.",held,lamp().g50?"Belum ada koin yang dipegang.":"Kosong karena Lampu BTC merah: metode menunggu di luar pasar.")
    +(cand.length?sec(`⏳ Calon pada cek berikutnya (${cand.length})`,"Sudah memenuhi semua syarat; dibeli pada cek Senin bila masih 5 teratas dan ada slot.",cand,""):"")
    +(sold.length?sec(`👋 Baru dijual (${sold.length})`,"Dijual dalam 7 hari terakhir.",sold,""):"")
    +sec("Koin lain, urut peringkat kenaikan 90 hari","",rest,"–");
  if(mo.eq&&mo.eq.length) loadLWC().then(()=>{ if(tab!==m.id) return; const el=$("momEq"); if(!el||!window.LightweightCharts) return; cyObs.forEach(o=>o.disconnect()); cyObs=[]; cyCharts.forEach(c=>{try{c.remove()}catch(e){}}); cyCharts=[];
    const line=cssVar("--line"), muted=cssVar("--muted"), acc=cssVar("--accent");
    const ch=LightweightCharts.createChart(el,{height:180,layout:{background:{type:"solid",color:"transparent"},textColor:muted},grid:{vertLines:{visible:false},horzLines:{color:line}},rightPriceScale:{borderColor:line,mode:1},timeScale:{borderColor:line},handleScroll:false,handleScale:false});
    cyCharts.push(ch); const s=ch.addAreaSeries({lineColor:acc,topColor:acc+"44",bottomColor:acc+"05",lineWidth:2,priceLineVisible:false,priceFormat:{type:"price",precision:2,minMove:0.01}});
    s.setData(mo.eq.map(([d,v])=>({time:d,value:v}))); ch.timeScale().fitContent(); watchSize(ch,el); }).catch(()=>{});
}
