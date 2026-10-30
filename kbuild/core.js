(function(){
"use strict";
const $ = id => document.getElementById(id);
const esc = s => String(s==null?"":s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const store = {
  get(k){try{return localStorage.getItem(k)}catch(e){return null}},
  set(k,v){try{localStorage.setItem(k,v)}catch(e){}}
};
const IS_ID = true, IS_CR = true; // harga dalam Rupiah
const WP = "kr.";
const M = [
 {id:"mom90",abbr:"M",name:"Momentum 90 hari",title:"Momentum 90 hari (rotasi mingguan)",who:"Time-series & cross-sectional momentum kripto (Liu & Tsyvinski, 2021)",kind:"tr",
  desc:"Memegang 5 koin dengan kenaikan 90 hari terkuat yang lebih kuat dari Bitcoin, dicek seminggu sekali, dan hanya saat Lampu BTC hijau.",
  entry:["Lampu BTC hijau: BTC ditutup di atas rata-rata 50 harinya.","Setiap Senin (candle harian ditutup Selasa 07.00 WIB), semua koin diurutkan menurut kenaikan 90 hari.","Beli yang masuk 5 teratas, kenaikannya lebih besar dari BTC, dan harganya di atas rata-rata 50 hari. Dana dibagi rata ke 5 slot."],
  exit:["Saat cek Senin: jual bila keluar dari 8 teratas, turun di bawah rata-rata 50 hari, atau Lampu BTC merah.","Di hari lain: jual bila Lampu BTC merah DAN harga koin di bawah rata-rata 50 hari.","Tidak ada target harga: koin yang terus kuat dibiarkan berlari."],
  why:"Riset kripto (antara lain Liu & Tsyvinski, 2021) menemukan koin yang naik kencang beberapa minggu cenderung masih kuat beberapa minggu berikutnya. Di uji mundur kita (Jan 2021–Okt 2026) metode ini satu-satunya yang konsisten di atas pilihan koin acak. Filter Lampu BTC paling penting: tanpa itu, membeli altcoin rata-rata rugi. Batas 8 teratas (bukan 5) mencegah jual-beli bolak-balik yang menggerus modal lewat biaya.",
  cols:[["rk90","Peringkat"],["perf90","90 hari",1],["sma50","vs MA50",1],["perf1m","30 hari",1]]},
];
const MID = Object.fromEntries(M.map(m=>[m.id,m]));
const TABS = [{id:"summary",name:"Beranda",k:"Ringkasan"},{id:"lamp",name:"Lampu BTC",k:"Arah pasar"},{id:"mom90",name:"Momentum 90 hari",k:"Metode"},
  {id:"watch",name:"Watchlist",k:"Area support"},{id:"porto",name:"Portofolio",k:"Posisi Anda"},
  {id:"cycles",name:"Siklus",k:"Grafik · Fibonacci"},{id:"calc",name:"Kalkulator",k:"Risiko & jumlah"},{id:"hot",name:"Ramai hari ini",k:"Volume"}];
const ST = {buy:"Layak beli",hold:"Tahan",sell:"Jual",late:"Terlambat",wait:"Tunggu",na:"Tidak dinilai"};
const PRI = {buy:0,sell:1,hold:2,late:3,wait:4,na:5};
let DATA=null, rows=[];
let DET=null, DET_P=null; const detNeed=()=>false; function mergeDet(){} function loadDetail(){ return Promise.resolve(); }
function critStates(st){ return st.c||[]; }
let tab=(location.hash||"").slice(1);
if(!TABS.some(t=>t.id===tab)) tab=store.get(WP+"tab")||"summary";
if(!TABS.some(t=>t.id===tab)) tab="summary";
let ixFilter=store.get(WP+"ix")||"ALL";
let openTicker=null;

// ---------- format ----------
const NFC={};
const nf = (v,d=2) => (NFC[d]||(NFC[d]=new Intl.NumberFormat("id-ID",{minimumFractionDigits:d,maximumFractionDigits:d}))).format(Number(v));
const MORE={}; const moreRow=()=>"";
const decOf = v => { v=Math.abs(v); if(!v) return 0; return v>=1000?0:v>=1?2:Math.min(8,3-Math.floor(Math.log10(v||1e-9))); };
const usd = v => v==null||!isFinite(v) ? "–" : "Rp"+nf(v, decOf(v));
const rpM = v => v==null||!isFinite(v) ? "–" : "Rp"+nf(v, v&&Math.abs(v)<10?2:0);
const rpBig = v => v==null||!isFinite(v) ? "–" : v>=1e12?"Rp"+nf(v/1e12,v>=1e13?0:1)+" T":v>=1e9?"Rp"+nf(v/1e9,v>=1e10?0:1)+" M":v>=1e6?"Rp"+nf(v/1e6,0)+" jt":"Rp"+nf(v,0);
const usdx = v => v==null||!isFinite(v) ? "–" : "$"+nf(v, v>=1000?0:v>=1?2:Math.min(8,3-Math.floor(Math.log10(v))));
const qtyTx = q => q==null||!isFinite(q) ? "–" : nf(q, q>=1000?0:q>=1?4:Math.min(8,4-Math.floor(Math.log10(q||1e-9))));
const pct = (v,d=1,sign=true) => v==null||!isFinite(v) ? "–" : (sign&&v>0?"+":"")+nf(v,d)+"%";
const BLN=["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"];
function tgl(d,year){ if(!d) return "–"; const [y,m,dd]=d.split("-"); return `${+dd} ${BLN[+m-1]}${year?" "+y:""}` }
function fmtCol(k,v,isPct){
  if(v==null||!isFinite(v)) return '<span class="na">–</span>';
  if(isPct) return `<span class="${v>0?"ok":v<0?"no":""}">${pct(v,1)}</span>`;
  if(k==="rk90") return "#"+nf(v,0);
  return nf(v, Math.abs(v)>=100?0:2);
}
const chgCell = v => `<td class="num"><span class="${v>0?"ok":v<0?"no":""}">${pct(v,1)}</span></td>`;
const MEME="Meme";
const ixBadges = o => o.sector===MEME?'<span class="ix" title="Koin meme: sangat spekulatif">meme</span>':"";
const flowBadges = () => "";
const stockCell = o => `<td>${starBtn(o.ticker)}<span class="tk">${esc(o.ticker)}</span>${ixBadges(o)}<span class="nm">${esc(o.company||"")}${o.sector?" · "+esc(o.sector):""}</span></td>`;
const chip = s => `<span class="st ${s}">${ST[s]||s}</span>`;
function levels(mid, st){
  const lv=st.lv||{}, p=[];
  if(st.s==="sell") return st.sp!=null ? `jual ${usd(st.sp)} · ${pct(st.ret)}` : "";
  if(st.bp!=null&&(st.s==="hold"||st.s==="buy")) p.push("masuk "+usd(st.bp));
  if(lv.exit) p.push("batas MA50 "+usd(lv.exit));
  if(st.s==="hold"&&st.ret!=null) p.push(pct(st.ret));
  return p.join(" · ");
}

// ---------- filter ----------
function filtered(){
  const q=$("q").value.trim().toLowerCase(), sec=$("sector").value;
  return rows.filter(o=>(ixFilter==="ALL"||(ixFilter==="TOP20"&&(o.rank||999)<=Math.max(20,(rows[19]||{}).rank||20))||(ixFilter==="NOMEME"&&o.sector!==MEME)) && (!sec||o.sector===sec) &&
    (!q||(o.ticker+" "+(o.company||"")).toLowerCase().includes(q)));
}
const mget = (o,mid) => (o.m||{})[mid] || {s:"na",c:[],k:0,n:0};
function rk90(o){ return o.rk90; }

// ---------- status dari sudut pandang Anda ----------
let OWN_C=null;
function owned(t){ if(!OWN_C){ OWN_C={}; try{ porto().open.forEach(ps=>{ (OWN_C[ps.code]=OWN_C[ps.code]||[]).push(ps); }); }catch(e){} } return OWN_C[t]; }
const lamp = () => (DATA&&DATA.lamp)||{};
function uv(o,mid){
  const st=mget(o,mid), lv=st.lv||{};
  const r=Object.assign({},st,{raw:st.s,fresh:st.s==="buy",own:!!owned(o.ticker),why:"",sim:""});
  if((st.s==="hold"||st.s==="buy")&&st.b&&st.bp!=null) r.sim=`Simulasi metode: masuk ${tgl(st.b)} di ${usd(st.bp)}${st.ret!=null?` (${pct(st.ret)})`:""}. Bukan pembelian Anda.`;
  if(r.own){ if(st.s==="buy"||st.s==="hold") r.s="hold"; return r; }
  if(st.s==="na"||st.s==="wait"||st.s==="sell") return r;
  const L=lamp(), above=lv.exit==null||o.price>lv.exit, top=(o.rk90||99)<=8;
  const ok=L.g50!==false&&above&&top;
  r.why=ok?(st.s==="buy"?"baru masuk pada cek terakhir":`masih dipegang metode (peringkat #${o.rk90})`)
    :L.g50===false?"Lampu BTC sedang merah: jangan menambah posisi baru":!above?"harga sudah di bawah rata-rata 50 hari":"peringkatnya sudah di luar 8 besar";
  r.s=ok?"buy":"late"; return r;
}
const uchip=u=>`<span class="st ${u.s}">${u.s==="sell"?(u.own?"Jual":"Hindari"):ST[u.s]||u.s}</span>${u.s==="buy"&&u.fresh?' <span class="st new">baru</span>':""}${u.own?' <span class="st own" title="Ada di Portofolio Anda">💼</span>':""}`;
const ureason=u=>{ const base=String(u.r||"").replace(/^Masuk .*?sekarang [+\-−]?[\d.,]+%\.\s*/,"");
  return u.own?`💼 Koin ini ada di Portofolio Anda. ${base}`:u.s==="buy"||u.s==="late"?`${u.why?u.why.charAt(0).toUpperCase()+u.why.slice(1)+". ":""}${base}`:String(u.r||""); };
function summaryOf(o){ const by={buy:[],hold:[],sell:[]}; let pass=0; M.forEach(m=>{ const st=uv(o,m.id); if(by[st.s]) by[st.s].push(m.name); if(st.p) pass++; }); return {by,pass}; }

// ---------- status bar ----------
function renderStatus(){
  const el=$("status");
  if(!DATA){ el.innerHTML=`<span><span class="dot none"></span><b>Data belum tersedia.</b> Jalankan workflow "Update data kripto" di tab Actions GitHub, lalu muat ulang halaman ini.</span>`; return; }
  const d=new Date(DATA.updatedAt), ageH=(Date.now()-d)/36e5;
  const wib=d.toLocaleString("id-ID",{timeZone:"Asia/Jakarta",weekday:"long",day:"numeric",month:"long",hour:"2-digit",minute:"2-digit"});
  const L=lamp();
  el.innerHTML=`<span><span class="dot ${ageH>3?"old":""}"></span>Harga terakhir <b>${esc(wib)} WIB</b> · <span class="note">diperbarui tiap jam; sinyal metode dari candle harian yang ditutup 07.00 WIB</span></span>
    <span class="num">${rows.length} koin</span>
    <span>Lampu BTC: <b class="${L.g50?"ok":"no"}">${L.g50?"🟢 hijau":"🔴 merah"}</b></span>
    ${DATA.fx?`<span class="note">Kurs $1 = Rp${nf(DATA.fx,0)}</span>`:""}`;
}
function tabCount(t,list){
  let c="";
  if(t.id==="summary"){ const n=list.filter(o=>uv(o,"mom90").s==="buy").length; c=`<b>${n}</b> layak beli`; }
  else if(t.id==="lamp"){ const L=lamp(); c=L.g50==null?"–":L.g50?"🟢 hijau":"🔴 merah"; }
  else if(t.id==="mom90"){ const n=((DATA&&DATA.mom&&DATA.mom.pos)||[]).length; c=`<b>${n}</b> dipegang`; }
  else if(t.id==="hot"){ const n=hotLists(list).spike.length; c=n?`<b>${n}</b> volume melonjak`:"Volume & momentum"; }
  else if(t.id==="calc") c="Jumlah koin, untung, rugi";
  else if(t.id==="porto"){ const P=porto(); if(!P.open.length) c="Catat & pantau"; else { const nd=P.open.filter(ps=>posEval(ps).acts.some(a=>a.lv<=1)).length; c=`<b>${P.open.length}</b> posisi${nd?` · ⚠ ${nd} perlu tindakan`:""}`; } }
  else if(t.id==="watch"){ if(CYC&&CYC.watch){ const pl=planList(Object.fromEntries(list.map(o=>[o.ticker,o]))).list, n=pl.filter(x=>x.pl.kind==="now").length; c=SAFE?`<b>${n}</b> di area beli · ${pl.length-n} menunggu`:`<b>${n}</b> beli sekarang · ${pl.length-n} antrean`; } else c="★ dan area support"; }
  else if(t.id==="cycles"){ const f=CYC&&Object.values(CYC.indices)[0]; c=f?`<b>${(f.rawan||[]).length}</b> tanggal rawan`:"Grafik"; }
  return c;
}
function renderTabs(){
  OWN_C=null;
  const list=filtered();
  renderNav(); const grp=groupOf(tab); store.set(WP+"g."+grp.id,tab);
  $("tabs").innerHTML=grp.tabs.length<2?"":TABS.filter(t=>grp.tabs.includes(t.id)).map(t=>{
    const c=tabCount(t,list);
    return `<button class="tab" role="tab" type="button" aria-selected="${t.id===tab}" data-id="${t.id}"><span class="k">${esc(t.k)}</span><span class="n">${esc(t.name)}</span><span class="c">${c}</span></button>`;
  }).join("");
}
function statBlock(){
  const s=DATA&&DATA.mom; if(!s||!s.n) return "";
  return `<div class="rules"><h3>Uji mundur sejak ${tgl(s.from,1)}</h3><div class="statgrid">
    <div>Untung/tahun<b class="${s.cagr>=0?"ok":"no"}">${pct(s.cagr,1)}</b></div><div>Turun terdalam<b class="no">${pct(s.dd,0)}</b></div>
    <div>Transaksi<b>${nf(s.n,0)}</b></div><div>Menang<b>${nf(s.win,0)}%</b></div>
    <div>Rata-rata<b class="${s.avg>=0?"ok":"no"}">${pct(s.avg,1)}</b></div><div>Lama dipegang<b>${s.med} hari</b></div></div>
    <p class="note">Sudah dipotong biaya ${nf(s.fee||0.3,1)}% per transaksi. Daftar koin = 50 koin terbesar hari ini, jadi hasil masa lalu terlihat lebih bagus dari kenyataan (koin yang sudah mati tidak ikut).</p></div>`;
}
function renderRail(){
  const m=MID[tab], rail=$("rail");
  $("main").classList.toggle("full",!m); rail.hidden=!m;
  if(!m) return;
  rail.innerHTML=`<div style="display:flex;flex-direction:column;gap:6px"><h3>Metode kripto</h3><h2>${esc(m.title)}</h2><p class="who">${esc(m.who)}</p></div>
    <p style="font-size:14px">${esc(m.desc)}</p>
    <div class="rules"><h3>Kapan beli</h3><ul>${m.entry.map(x=>`<li>${esc(x)}</li>`).join("")}</ul></div>
    <div class="rules"><h3>Kapan jual</h3><ul>${m.exit.map(x=>`<li>${esc(x)}</li>`).join("")}</ul></div>
    <div class="rules"><h3>Kenapa aturan ini</h3><p class="note" style="font-size:13.5px">${esc(m.why)}</p></div>
    ${statBlock()}
    ${DATA&&DATA.mom&&DATA.mom.next?`<p class="note">Cek berikutnya: candle Senin ${tgl(DATA.mom.next,1)} (hasilnya muncul Selasa sekitar 07.30 WIB).</p>`:""}`;
}

// ---------- detail ----------
function critList(cs){
  return `<div class="cl">${(cs||[]).map(c=>{ const s=c[2]; const icon=s===1?'<span class="ok">✓</span>':s===0?'<span class="no">✗</span>':s===2?'<span class="na">·</span>':'<span class="na">?</span>';
    return `<div>${icon}<span>${esc(c[0])}</span><span class="v">${esc(c[1])}</span></div>` }).join("")}</div>`;
}
function tradeList(h){
  if(!h||!h.length) return "";
  return `<div class="trades">${h.slice().reverse().map(x=>`<div><span>Masuk ${tgl(x.b)} ${usd(x.bp)} → ${x.s?`jual ${tgl(x.s)} ${usd(x.sp)} <span class="na">(${esc(x.r)})</span>`:"<b>masih dipegang</b>"}</span><span class="num ${x.ret>=0?"ok":"no"}">${pct(x.ret)}</span></div>`).join("")}</div>`;
}
function methodCard(o,mid){
  const m=MID[mid], st=uv(o,mid), lv=levels(mid,st);
  return `<div class="mcard"><h4><span>${esc(m.name)} <span class="na" style="font-weight:400">${st.k}/${st.n}</span></span><span>${uchip(st)}</span></h4>
    <p style="font-size:13px">${esc(ureason(st))}</p>${lv?`<span class="lvl">${lv}</span>`:""}${st.sim?`<p class="note" style="font-size:12px">📊 ${esc(st.sim)}</p>`:""}
    ${critList(st.c)}${st.h&&st.h.length?`<div><h3 style="margin-bottom:4px">Riwayat simulasi</h3>${tradeList(st.h)}</div>`:""}</div>`;
}
function factCard(o){
  const gap=o.idx&&o.price?(o.idx/o.price-1)*100:null;
  return `<div class="mcard"><h4><span>Data koin</span></h4><div class="dl">
    <div><span>Peringkat kapitalisasi</span><span class="num">#${o.rank||"–"}${o.mcap?" · "+rpBig(o.mcap*1e9):""}</span></div>
    <div><span>Harga dunia (Binance)</span><span class="num">${usd(o.price)} · ${usdx(o.usd)}</span></div>
    ${o.idx?`<div><span>Harga di Indodax</span><span class="num">${usd(o.idx)}${gap!=null?` <span class="note">(${pct(gap,1)})</span>`:""}</span></div>`:""}
    <div><span>Hari ini (sejak 07.00 WIB)</span><span class="num ${o.chg1d>0?"ok":o.chg1d<0?"no":""}">${pct(o.chg1d)}</span></div>
    <div><span>7 · 30 · 90 hari</span><span class="num">${pct(o.perf1w,0)} · ${pct(o.perf1m,0)} · ${pct(o.perf90,0)}</span></div>
    <div><span>1 tahun · dari puncak 1 tahun</span><span class="num">${pct(o.perf1y,0)} · ${pct(o.hi52,0)}</span></div>
    <div><span>Jarak dari MA50 · MA200</span><span class="num">${pct(o.sma50,1)} · ${pct(o.sma200,1)}</span></div>
    <div><span>RSI (14)</span><span class="num">${o.rsi14!=null?nf(o.rsi14,0):"–"}</span></div>
    <div><span>Volume hari ini vs biasa</span><span class="num">${o.volR!=null?nf(o.volR,1)+"×":"–"}</span></div>
    <div><span>Nilai transaksi rata-rata (Binance)</span><span class="num">${o.adv!=null?rpBig(o.adv*1e9)+"/hari":"–"}</span></div></div>
    ${gap!=null&&Math.abs(gap)>=1.5?`<p class="note">Harga Indodax ${gap>0?"lebih mahal":"lebih murah"} ${nf(Math.abs(gap),1)}% dari harga dunia. Selisih besar biasanya karena Indodax sepi atau kurs USDT lokal.</p>`:""}</div>`;
}
function detail(o){
  return `${saranBox(`${saranStock(o)}<p style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">${chartBtn(o.ticker,"📈 Lihat grafik, support & RSI")}${calcBtn(o.ticker,"🧮 Hitung jumlah & risiko")}</p>`)}<div style="height:10px"></div><div class="dgrid">${factCard(o)}${M.map(m=>methodCard(o,m.id)).join("")}</div>`;
}
