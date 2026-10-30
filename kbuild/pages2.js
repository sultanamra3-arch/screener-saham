// ---------- Watchlist ----------
const RR_MIN=2, UP_MIN=5;
function floorTick(v){ if(!v||!isFinite(v)) return v; const d=decOf(v)+(v>=1000?0:1), f=10**Math.max(0,d), s=v>=1000?10**Math.max(0,Math.floor(Math.log10(v))-3):0; return s?Math.floor(v/s)*s:Math.floor(v*f)/f; }
function strongRes(a){ return (a&&a.res||[]).find(z=>z.strength!=="lemah")||null; }
function planList(byT){
  const W=CYC.watch;
  const mk=(src,near)=>Object.entries(src||{}).filter(([t,w])=>byT[t]&&w.strength!=="lemah").map(([t,w])=>{ const x={t,w,o:byT[t],near}; x.rm=roomOf(t,w); return x; });
  const all=[...mk(W.in,false),...mk(W.near,true)]; let skip=0; const out=[];
  all.forEach(x=>{ x.pl=planOf(x); if(x.pl) out.push(x); else skip++; });
  out.sort((a,b)=>(a.pl.kind==="now"?0:1)-(b.pl.kind==="now"?0:1)||(a.pl.kind==="now"?(b.pl.rr??9)-(a.pl.rr??9):b.pl.dist-a.pl.dist));
  return {list:out,skip};
}
function renderWatch(box){
  if(!CYC&&!CYC_ERR){ box.innerHTML=`<div class="tablebox"><div class="empty">Memuat data area support…</div></div>`; loadCycles().then(()=>{ if(tab==="watch"){ renderTabs(); renderResults(); } }); return; }
  if(CYC_ERR||!CYC.watch){ box.innerHTML=`<div class="tablebox"><div class="empty">Data area support belum tersedia. Akan terisi setelah pembaruan data berikutnya.</div></div>`; return; }
  const W=CYC.watch, L=lamp();
  const byT=Object.fromEntries(filtered().map(o=>[o.ticker,o]));
  const newSet=new Set(W.new||[]), lowSet=new Set(W.lower||[]);
  const {list,skip}=planList(byT), nNow=list.filter(x=>x.pl.kind==="now").length, nQ=list.length-nNow;
  const own=new Set(porto().open.map(p=>p.code));
  const rrS=pl=>pl.rr==null?'<span class="ok">terbuka</span>':`<span class="${pl.rr>=3?"ok":""}">1 : ${nf(pl.rr,1)}</span>`;
  const row=x=>{ const pl=x.pl, now=pl.kind==="now", u=uv(x.o,"mom90");
    return `<tr class="row wrow" data-go="${esc(x.t)}" tabindex="0">${stockCell(x.o)}
      <td class="num">${usd(x.o.price)}</td>
      <td>${now?`<span class="st buy">${T("✅ Beli sekarang","✅ Di area beli")}</span>`:`<span class="st hold">${T("⏳ Pasang antrean","⏳ Menunggu area beli")}</span>`}${own.has(x.t)?' <span class="note">💼 sudah punya</span>':""}${newSet.has(x.t)||lowSet.has(x.t)?' <span class="st buy">baru</span>':""}
        <br><span class="note">${now?`di zona S${pl.n} ${zr(pl.z)} (${pl.z.strength})`:`menunggu turun ${nf(-pl.dist,1)}% ke S${pl.n} (${pl.z.strength})`}</span></td>
      <td class="num"><b>${now?"≤ ":""}${usd(pl.e)}</b></td>
      <td class="num no" style="white-space:nowrap">&lt;&nbsp;${usd(pl.stop)}<br><span class="note">${nf(pl.loss,1)}%</span></td>
      <td class="num">${pl.tgt?`<span class="ok">${usd(pl.tgt)}</span><br><span class="note">+${nf(pl.up,1)}%</span>`:'<span class="note">tak ada resistance<br>kuat ≤30%</span>'}</td>
      <td class="num">${rrS(pl)}</td>
      <td style="font-size:13px">${["buy","hold","late"].includes(u.s)?uchip(u)+'<br><span class="note">Momentum</span>':(x.o.sma200!=null?(x.o.sma200>=0?'<span class="ok">di atas MA200</span>':'<span class="no">di bawah MA200</span>'):"–")}</td>
      <td><button type="button" class="calcbtn" data-calc="${esc(x.t)}" data-e="${pl.e}" data-s="${pl.stop}" data-tg="${pl.tgt||""}">🧮</button></td></tr>`; };
  const st=stars(), starred=[...st].map(t=>({t,o:rows.find(x=>x.ticker===t),z:nearZones(t)})).filter(x=>x.o);
  const broken=(W.broken||[]).filter(b=>byT[b.t]);
  box.innerHTML=saranBox(`${saranMarket().head}<ul class="sl">
      <li>📋 Daftar di bawah: koin yang harganya sedang di (atau dekat) ${tip("lantai harga","support")} kuat/sedang.</li>
      <li>⚖️ Syaratnya: masih bisa naik minimal ${UP_MIN}% dan calon untungnya minimal ${RR_MIN}× calon rugi.</li>
      ${L.g50===false?`<li>🔴 <b>Lampu BTC merah:</b> ${T("support kripto lebih sering jebol saat begini. Kalau tetap beli, kecilkan jumlahnya.","support lebih sering jebol di kondisi ini.")}</li>`:""}
      <li>🛑 ${T("Kalau harga ditutup di bawah angka <b>Stop</b>, jual atau batalkan antrean.","<b>Stop</b> = batas rugi menurut aturan (harga penutupan).")}</li></ul>`)+`
    <div class="rhead" style="margin-top:12px"><div class="l"><h2>${T(`Rencana beli: ${nNow} beli sekarang · ${nQ} antrean`,`Area beli: ${nNow} di area · ${nQ} menunggu`)}</h2>
      <p class="note">${skip?`${skip} koin lain di area support dilewati karena ruang naiknya sempit. `:""}Klik baris untuk membuka grafik.</p></div></div>
    <div class="tablebox"><table><thead><tr><th>Koin</th><th class="num">Harga</th><th>${T("Aksi","Status")}</th><th class="num">${T("Beli di","Area beli")}</th><th class="num">Stop</th><th class="num">Target</th><th class="num">R:R</th><th>Tren</th><th></th></tr></thead><tbody>
    ${list.length?list.slice(0,60).map(row).join(""):`<tr><td colspan="9" class="empty">Belum ada koin di area support yang hitungannya layak. Menunggu juga keputusan yang bagus.</td></tr>`}</tbody></table></div>
    <details class="mcard" style="margin-top:10px"><summary><b>Cara membaca rencana beli</b></summary><div class="dl" style="font-size:14px;margin-top:6px">
      <div><span><b>Beli di</b>: untuk “beli sekarang”, beli di harga sekarang atau lebih rendah. Untuk antrean, pasang order beli (limit) di harga ini di Indodax/Tokocrypto.</span></div>
      <div><span><b>Stop</b>: bila harga candle harian <b>ditutup</b> di bawah angka ini, support dianggap jebol; jual atau batalkan antrean.</span></div>
      <div><span><b>Target</b>: resistance kuat/sedang terdekat. <b>R:R</b> = potensi untung dibagi potensi rugi.</span></div>
      <div><span>🧮 membuka Kalkulator dengan harga beli, stop, dan target terisi, untuk menghitung berapa Rupiah yang aman dibelikan.</span></div></div></details>
    <div class="rhead" style="margin-top:16px"><div class="l"><h2>★ Koin yang Anda tandai</h2><p class="note">Klik ☆ di tabel mana pun untuk menandai.</p></div></div>
    <div class="tablebox"><table><thead><tr><th>Koin</th><th class="num">Harga</th><th class="num">Support terdekat</th><th class="num">Jarak</th><th class="num">R1</th><th>Status</th></tr></thead><tbody>
    ${starred.length?starred.map(x=>{ const z=x.z&&x.z.s, w=W.in[x.t], r1=x.z?strongRes(x.z.a):null, pl=list.find(y=>y.t===x.t); return `<tr class="row wrow" data-go="${esc(x.t)}" tabindex="0">${stockCell(x.o)}<td class="num">${usd(x.o.price)}</td>
      <td class="num">${z?zr(z)+" ("+z.strength+")":"–"}</td><td class="num">${w?(w.dist<=0?"di zona":"+"+nf(w.dist,1)+"%"):z?"+"+nf((x.o.price/z.hi-1)*100,1)+"%":"–"}</td>
      <td class="num">${r1?usd(r1.lo)+" ("+pct(r1.dist)+")":"–"}</td>
      <td style="font-size:13px">${pl?(pl.pl.kind==="now"?`<span class="st buy">${T("✅ beli sekarang","✅ di area beli")}</span> `:`<span class="st hold">${T("⏳ antre","⏳ area beli")} ${usd(pl.pl.e)}</span> `):""}${uchip(uv(x.o,"mom90"))}</td></tr>`}).join("")
      :`<tr><td colspan="6" class="empty">Belum ada koin yang Anda tandai.</td></tr>`}</tbody></table></div>
    ${broken.length?`<div class="rhead" style="margin-top:16px"><div class="l"><h2>⚠️ Support jebol</h2><p class="note">Kemarin di area support, sekarang di bawah batas jebol. Batalkan antrean dan evaluasi ulang.</p></div></div>
      <div class="tablebox"><table><thead><tr><th>Koin</th><th class="num">Harga</th><th class="num">Zona yang jebol</th><th class="num">Di bawah zona</th></tr></thead><tbody>
      ${broken.map(b=>`<tr class="row wrow" data-go="${esc(b.t)}" tabindex="0">${stockCell(byT[b.t])}<td class="num">${usd(b.price)}</td><td class="num">${zr(b)} (${b.strength})</td><td class="num no">${pct(b.drop)}</td></tr>`).join("")}</tbody></table></div>`:""}
    <p class="note" style="margin-top:8px">Zona support dan resistance adalah area kemungkinan, bukan jaminan. Di kripto, support lebih sering ditembus daripada di saham.</p>`;
  warmCharts(list.map(x=>x.t));
}

// ---------- Portofolio ----------
const PKEY=WP+"porto";
function porto(){ try{ const p=JSON.parse(store.get(PKEY)||"{}"); return {open:p.open||[],closed:p.closed||[]}; }catch(e){ return {open:[],closed:[]}; } }
function savePorto(p){ store.set(PKEY,JSON.stringify(p)); OWN_C=null; }
const PMETH=[["mom90","Momentum 90 hari"],["btc200","BTC Tren 200"],["support","Beli di support (Watchlist)"],["lain","Aturan sendiri"]];
const PMN=Object.fromEntries(PMETH);
const todayISO=()=>new Date().toISOString().slice(0,10);
function fee(){ const v=parseFloat(String(store.get(WP+"fee")||"0.3").replace(",",".")); return isFinite(v)&&v>=0&&v<5?v/100:0.003; }
function posEval(ps){
  const o=rows.find(x=>x.ticker===ps.code), p=o?o.price:null, L=lamp(), acts=[];
  const cost=ps.qty*ps.price, val=p!=null?ps.qty*p:null, net=val!=null?val*(1-fee()):null;
  const pl=net!=null?net-cost:null, plp=pl!=null&&cost?pl/cost*100:null;
  if(o&&p!=null){
    const st=mget(o,"mom90"), ma50=(st.lv||{}).exit;
    if(ps.stop&&p<ps.stop) acts.push({lv:0,ic:"🛑",t:`harga ${usd(p)} di bawah batas rugi Anda ${usd(ps.stop)}`});
    if(ps.target&&p>=ps.target) acts.push({lv:1,ic:"🎯",t:`target Anda ${usd(ps.target)} tercapai`});
    if(ps.method==="btc200"&&ps.code==="BTC"&&L.g200===false) acts.push({lv:0,ic:"🔴",t:"BTC ditutup di bawah rata-rata 200 hari: aturan BTC Tren 200 menjual"});
    if(ps.method==="mom90"){ if(st.s==="sell") acts.push({lv:0,ic:"👋",t:`metode Momentum sudah menjual: ${st.why||st.rs||""}`});
      else if(!["buy","hold"].includes(st.s)&&ma50&&p<ma50) acts.push({lv:1,ic:"📉",t:`tidak lagi dipegang metode dan harga di bawah rata-rata 50 hari (${usd(ma50)})`}); }
    if(ps.code!=="BTC"&&L.g50===false&&ma50&&p<ma50&&ps.method!=="mom90") acts.push({lv:1,ic:"🔴",t:`Lampu BTC merah dan harga di bawah rata-rata 50 hari (${usd(ma50)})`});
    else if(ps.code!=="BTC"&&L.g50===false) acts.push({lv:2,ic:"🔴",t:"Lampu BTC merah: jangan menambah posisi"});
    if(CYC&&CYC.watch&&(CYC.watch.broken||[]).some(b=>b.t===ps.code)) acts.push({lv:1,ic:"🧱",t:"support yang tadinya menahan harga sudah jebol"});
  }
  acts.sort((a,b)=>a.lv-b.lv);
  return {o,p,cost,val,pl,plp,acts};
}
function journalStats(C){ if(!C.length) return null; const r=C.map(x=>x.ret); const w=r.filter(x=>x>0);
  return {n:C.length,win:w.length,avg:r.reduce((a,b)=>a+b,0)/C.length,pl:C.reduce((a,x)=>a+(x.pl||0),0)}; }
function renderPorto(box){
  const P=porto(), E=P.open.map(ps=>({ps,e:posEval(ps)}));
  const tot=E.reduce((a,x)=>({c:a.c+x.e.cost,v:a.v+(x.e.val!=null?x.e.val*(1-fee()):x.e.cost)}),{c:0,v:0});
  const J=journalStats(P.closed), pre=(()=>{ try{ return JSON.parse(store.get(WP+"porto.pre")||"null"); }catch(e){ return null; } })(); if(pre) store.set(WP+"porto.pre","");
  const opts=rows.map(o=>`<option value="${esc(o.ticker)}">${esc(o.company||"")}</option>`).join("");
  const pc0=pre&&pre.code?rows.find(o=>o.ticker===pre.code):null;
  box.innerHTML=`${E.some(x=>x.e.acts.some(a=>a.lv<=1))?saranBox(`<ul class="sl">${E.filter(x=>x.e.acts.some(a=>a.lv<=1)).map(x=>`<li><b>${esc(x.ps.code)}</b>: ${x.e.acts.filter(a=>a.lv<=1).map(a=>a.ic+" "+esc(a.t)).join("; ")}</li>`).join("")}</ul>`):""}
    <div class="mcard" style="margin-top:12px"><h4><span>💼 Ringkasan</span><span class="note" style="font-weight:400">tersimpan di perangkat ini saja</span></h4>
      <div class="statgrid"><div>Modal di posisi<b>${rpM(tot.c)}</b></div><div>Nilai sekarang (setelah biaya jual)<b>${rpM(tot.v)}</b></div>
        <div>Untung/rugi berjalan<b class="${tot.v>=tot.c?"ok":"no"}">${tot.c?pct((tot.v/tot.c-1)*100,1):"–"}</b></div>
        <div>Sudah direalisasi<b class="${J&&J.pl>=0?"ok":"no"}">${J?(J.pl>=0?"+":"−")+rpM(Math.abs(J.pl)):"–"}</b></div></div></div>
    <div class="rhead" style="margin-top:14px"><div class="l"><h2>Posisi terbuka (${E.length})</h2><p class="note">Harga dunia dalam Rupiah. Untung/rugi sudah dipotong perkiraan biaya jual ${nf(fee()*100,2)}%.</p></div></div>
    <div class="tablebox"><table><thead><tr><th>Koin</th><th class="num">Jumlah</th><th class="num">Harga beli</th><th class="num">Harga sekarang</th><th class="num">Nilai</th><th class="num">Untung/rugi</th><th>Status</th><th></th></tr></thead><tbody>
    ${E.length?E.map(({ps,e},i)=>`<tr class="row" data-t="${esc(ps.code)}" tabindex="0"><td><span class="tk">${esc(ps.code)}</span><span class="nm">${tgl(ps.date,1)} · ${esc(PMN[ps.method]||"")}${ps.note?" · "+esc(ps.note):""}</span></td>
      <td class="num">${qtyTx(ps.qty)}</td><td class="num">${usd(ps.price)}<br><span class="note">${rpM(ps.qty*ps.price)}</span></td><td class="num">${usd(e.p)}</td><td class="num">${rpM(e.val)}</td>
      <td class="num ${e.pl>=0?"ok":"no"}">${e.pl!=null?(e.pl>=0?"+":"−")+rpM(Math.abs(e.pl)):"–"}<br>${pct(e.plp)}</td>
      <td style="font-size:13px">${e.acts.length?e.acts.map(a=>`<span class="${a.lv===0?"no":a.lv===1?"":"note"}">${a.ic} ${esc(a.t)}</span>`).join("<br>"):'<span class="st buy">✅ tahan</span>'}</td>
      <td><button type="button" class="calcbtn" data-sell="${i}">Jual</button></td></tr>`).join("")
      :`<tr><td colspan="8" class="empty">Belum ada posisi. Catat pembelian Anda di bawah.</td></tr>`}</tbody></table></div>
    <form class="mcard" id="pForm" style="margin-top:14px"><h4><span>➕ Catat pembelian</span></h4>
      <div class="cgrid">
        <label class="cf"><span>Koin</span><input id="p_code" list="pList" required value="${esc(pc0?pc0.ticker:"")}" placeholder="mis. ETH" style="text-transform:uppercase" autocomplete="off"><datalist id="pList">${opts}</datalist></label>
        <label class="cf"><span>Tanggal</span><input id="p_date" type="date" value="${todayISO()}" required></label>
        <label class="cf"><span>Harga beli per koin (Rp)</span><input id="p_price" inputmode="decimal" required value="${pre&&pre.price?pre.price:pc0?pc0.price:""}"></label>
        <label class="cf"><span>Dana yang dibelikan (Rp)</span><input id="p_amt" inputmode="decimal" value="${pre&&pre.amt?Math.round(pre.amt):""}" placeholder="mis. 500000"></label>
        <label class="cf"><span>…atau jumlah koin</span><input id="p_qty" inputmode="decimal" placeholder="kosongkan bila isi dana"></label>
        <label class="cf"><span>Ikut aturan</span><select id="p_meth">${PMETH.map(([k,n])=>`<option value="${k}" ${(pre&&pre.meth===k)?"selected":""}>${n}</option>`).join("")}</select></label>
        <label class="cf"><span>Batas rugi / stop (opsional)</span><input id="p_stop" inputmode="decimal" value="${pre&&pre.stop?pre.stop:""}"></label>
        <label class="cf"><span>Target (opsional)</span><input id="p_tg" inputmode="decimal" value="${pre&&pre.target?pre.target:""}"></label>
        <label class="cf"><span>Catatan / alasan beli</span><input id="p_note" maxlength="120" placeholder="mis. lampu hijau, peringkat #2"></label>
      </div><p class="note" id="p_prev"></p><p><button type="submit" class="calcbtn" style="font-size:15px;padding:8px 16px">Simpan posisi</button></p></form>
    ${P.closed.length?`<div class="rhead" style="margin-top:16px"><div class="l"><h2>Jurnal transaksi selesai</h2><p class="note">${J.n} transaksi · ${J.win} untung (${nf(J.win/J.n*100,0)}%) · rata-rata ${pct(J.avg,1)} per transaksi.</p></div></div>
      <div class="tablebox"><table><thead><tr><th>Koin</th><th class="num">Beli</th><th class="num">Jual</th><th class="num">Hasil</th><th>Catatan</th></tr></thead><tbody>
      ${P.closed.slice().reverse().slice(0,40).map(c=>`<tr><td><span class="tk">${esc(c.code)}</span><span class="nm">${esc(PMN[c.method]||"")}${c.part?" · sebagian":""}</span></td><td class="num">${usd(c.price)}<br><span class="note">${tgl(c.date,1)}</span></td><td class="num">${usd(c.sprice)}<br><span class="note">${tgl(c.sdate,1)}</span></td>
        <td class="num ${c.ret>=0?"ok":"no"}">${pct(c.ret,1)}<br><span class="note">${(c.pl>=0?"+":"−")+rpM(Math.abs(c.pl))}</span></td><td style="font-size:13px">${esc(c.note||"")}${c.snote?`<br><span class="note">jual: ${esc(c.snote)}</span>`:""}</td></tr>`).join("")}</tbody></table></div>`:""}
    <p class="note" style="margin-top:8px">Data portofolio hanya disimpan di browser ini. Biaya beli dan jual dianggap ${nf(fee()*100,2)}% per transaksi (ubah di Kalkulator).</p>`;
  const f=$("pForm"), prev=()=>{ const pr=num($("p_price").value), a=num($("p_amt").value), q=num($("p_qty").value);
    const qq=q||(a&&pr?a*(1-fee())/pr:null); $("p_prev").textContent=qq?`≈ ${qtyTx(qq)} ${($("p_code").value||"koin").toUpperCase()} senilai ${rpM(qq*pr)} (biaya beli ${nf(fee()*100,2)}% sudah dipotong dari dana).`:""; };
  ["p_price","p_amt","p_qty"].forEach(id=>$(id).addEventListener("input",prev)); prev();
  $("p_code").addEventListener("change",()=>{ const o=rows.find(x=>x.ticker===$("p_code").value.trim().toUpperCase()); if(o&&!$("p_price").value) { $("p_price").value=o.price; prev(); } });
  f.addEventListener("submit",ev=>{ ev.preventDefault(); const code=$("p_code").value.trim().toUpperCase(), pr=num($("p_price").value), a=num($("p_amt").value), q=num($("p_qty").value);
    const qty=q||(a&&pr?a*(1-fee())/pr:null);
    if(!code||!pr||!qty){ alertBox("Isi koin, harga beli, dan dana atau jumlah koin."); return; }
    const P2=porto(); P2.open.push({id:Date.now(),code,date:$("p_date").value||todayISO(),price:pr,qty,method:$("p_meth").value,stop:num($("p_stop").value)||null,target:num($("p_tg").value)||null,note:$("p_note").value.trim()});
    savePorto(P2); renderTabs(); renderResults(); });
}
function num(v){ v=String(v==null?"":v).trim().replace(/\s/g,""); if(!v) return null; if(/,\d{1,8}$/.test(v)) v=v.replace(/\./g,"").replace(",","."); else if(/^\d{1,3}(\.\d{3})+$/.test(v)) v=v.replace(/\./g,""); const n=parseFloat(v); return isFinite(n)?n:null; }
function alertBox(msg){ const b=$("results"); const d=document.createElement("p"); d.className="no"; d.textContent=msg; b.prepend(d); setTimeout(()=>d.remove(),4000); }
function sellDialog(i){
  const P=porto(), ps=P.open[i]; if(!ps) return; const o=rows.find(x=>x.ticker===ps.code);
  let d=$("sellDlg"); if(!d){ d=document.createElement("dialog"); d.id="sellDlg"; document.body.appendChild(d); }
  d.innerHTML=`<form method="dialog" class="qsb" style="display:flex;flex-direction:column;gap:10px;min-width:min(420px,86vw)"><b>Jual ${esc(ps.code)}</b><span class="note">Punya ${qtyTx(ps.qty)} koin, dibeli ${usd(ps.price)}.</span>
    <label class="cf"><span>Harga jual per koin (Rp)</span><input id="s_price" inputmode="decimal" value="${o?o.price:""}"></label>
    <div class="seg" role="group">${[[1,"Semua"],[0.5,"½"],[1/3,"⅓"],[0.25,"¼"]].map(([v,l])=>`<button type="button" data-fr="${v}" aria-pressed="${v===1}">${l}</button>`).join("")}</div>
    <label class="cf"><span>Jumlah koin dijual</span><input id="s_qty" inputmode="decimal" value="${ps.qty}"></label>
    <label class="cf"><span>Catatan (opsional)</span><input id="s_note" maxlength="120" placeholder="mis. lampu merah"></label>
    <p class="note" id="s_prev"></p>
    <div style="display:flex;gap:8px;justify-content:flex-end"><button type="button" class="calcbtn" id="s_cancel">Batal</button><button type="submit" class="calcbtn" id="s_ok" style="background:var(--accent);color:#fff">Simpan penjualan</button></div></form>`;
  const pv=()=>{ const sp=num(d.querySelector("#s_price").value), q=Math.min(num(d.querySelector("#s_qty").value)||0,ps.qty); if(!sp||!q){ d.querySelector("#s_prev").textContent=""; return; }
    const pl=q*sp*(1-fee())-q*ps.price; d.querySelector("#s_prev").textContent=`Hasil: ${pl>=0?"untung":"rugi"} ${rpM(Math.abs(pl))} (${pct((sp*(1-fee())/ps.price-1)*100,1)}) setelah biaya jual.`; };
  d.querySelectorAll("[data-fr]").forEach(b=>b.addEventListener("click",()=>{ d.querySelectorAll("[data-fr]").forEach(x=>x.setAttribute("aria-pressed",x===b)); d.querySelector("#s_qty").value=+(ps.qty*+b.dataset.fr).toPrecision(8); pv(); }));
  d.querySelector("#s_price").addEventListener("input",pv); d.querySelector("#s_qty").addEventListener("input",pv); pv();
  d.querySelector("#s_cancel").addEventListener("click",()=>d.close());
  d.querySelector("form").addEventListener("submit",ev=>{ const sp=num(d.querySelector("#s_price").value), q=Math.min(num(d.querySelector("#s_qty").value)||0,ps.qty); if(!sp||!q){ ev.preventDefault(); return; }
    const P2=porto(), x=P2.open[i]; if(!x) return; const part=q<x.qty-1e-12, pl=q*sp*(1-fee())-q*x.price;
    P2.closed.push({code:x.code,date:x.date,price:x.price,qty:q,method:x.method,note:x.note,sdate:todayISO(),sprice:sp,snote:d.querySelector("#s_note").value.trim(),ret:(sp*(1-fee())/x.price-1)*100,pl,part});
    if(part) x.qty=+(x.qty-q).toPrecision(10); else P2.open.splice(i,1);
    savePorto(P2); setTimeout(()=>{ renderTabs(); renderResults(); },0); });
  d.showModal();
}
function addToPorto(st){ store.set(WP+"porto.pre",JSON.stringify(st)); goTab("porto"); window.scrollTo({top:0}); }

// ---------- Kalkulator ----------
const CALC_DEF={modal:1000000,risk:2,entry:null,stop:null,target:null,code:""};
function calcState(){ try{ return Object.assign({}, CALC_DEF, JSON.parse(store.get(WP+"calc")||"{}")); }catch(e){ return Object.assign({},CALC_DEF); } }
function saveCalc(st){ store.set(WP+"calc", JSON.stringify(st)); }
function openCalc(t,ov){ const s=calcState(), o=rows.find(x=>x.ticker===t); s.code=t;
  if(ov){ s.entry=ov.entry; s.stop=ov.stop; s.target=ov.target; }
  else if(o){ const pl=planFor(t), st=mget(o,"mom90"); s.entry=pl?pl.e:o.price; s.stop=pl?pl.stop:((st.lv||{}).exit&&(st.lv.exit<o.price)?floorTick(st.lv.exit):floorTick(o.price*0.85)); const z=nearZones(t); s.target=pl&&pl.tgt?pl.tgt:z&&z.r?z.r.lo:null; }
  saveCalc(s); const dc=$("drClose"); if(dc) dc.click(); goTab("calc"); window.scrollTo({top:0}); }
const chartBtn = (t,label="📈 Grafik") => `<button type="button" class="calcbtn chartbtn" data-chart="${esc(t)}">${label}</button>`;
function openChart(t){ store.set(WP+"cy.sel",t); const dc=$("drClose"); if(dc) dc.click(); goTab("cycles"); window.scrollTo({top:0}); }
const calcBtn = (t,label="🧮 Hitung") => `<button type="button" class="calcbtn" data-calc="${esc(t)}">${label}</button>`;
const alarmBtn = () => "";
function renderCalc(box){
  const s=calcState(), F=fee();
  const fld=(id,label,val,extra="")=>`<label class="cf" for="${id}"><span>${label}</span><input type="text" inputmode="decimal" id="${id}" value="${val==null?"":val}" ${extra}></label>`;
  box.innerHTML=`<div class="mcard"><h4><span>🧮 Berapa yang aman dibeli?</span></h4>
    <p class="note">Isi modal kripto Anda, harga beli, dan batas rugi. Kalkulator menghitung jumlah Rupiah supaya kalau kena stop, rugi Anda tidak lebih dari persentase risiko yang Anda pilih.</p>
    <div class="cgrid">
      <label class="cf"><span>Koin</span><input id="c_code" list="cList" value="${esc(s.code||"")}" style="text-transform:uppercase" autocomplete="off"><datalist id="cList">${rows.map(o=>`<option value="${esc(o.ticker)}">`).join("")}</datalist></label>
      ${fld("c_modal","Modal kripto total (Rp)",s.modal)}${fld("c_risk","Risiko per transaksi (% modal)",s.risk)}
      ${fld("c_entry","Harga beli per koin (Rp)",s.entry)}${fld("c_stop","Batas rugi / stop (Rp)",s.stop)}${fld("c_tg","Target (Rp, opsional)",s.target)}
      ${fld("c_fee","Biaya per transaksi (%)",nf(F*100,2))}
    </div><div id="c_out" style="margin-top:10px"></div></div>
    <div class="mcard" style="margin-top:12px"><h4><span>Kenapa begini</span></h4><ul class="sl">
      <li>Kripto bisa turun 10–20% dalam sehari. Dengan membatasi rugi per transaksi (umumnya 1–2% modal), satu kesalahan tidak menghapus modal Anda.</li>
      <li>Makin jauh stop dari harga beli, makin kecil jumlah yang boleh dibeli.</li>
      <li>Untuk metode Momentum 90 hari, aturannya lebih sederhana: dana kripto dibagi 5, satu bagian per koin.</li></ul></div>`;
  const calc=()=>{ const st=calcState(); st.code=$("c_code").value.trim().toUpperCase(); st.modal=num($("c_modal").value); st.risk=num($("c_risk").value); st.entry=num($("c_entry").value); st.stop=num($("c_stop").value); st.target=num($("c_tg").value);
    const fv=num($("c_fee").value); if(fv!=null&&fv>=0&&fv<5) store.set(WP+"fee",String(fv)); saveCalc(st);
    const f=fee(), out=$("c_out"), {modal,risk,entry,stop,target}=st;
    if(!modal||!entry){ out.innerHTML='<p class="note">Isi modal dan harga beli.</p>'; return; }
    if(!stop||stop>=entry){ const amt=modal/5; out.innerHTML=`<div class="statgrid"><div>Porsi 1/5 modal<b>${rpM(amt)}</b></div><div>Dapat koin<b>${qtyTx(amt*(1-f)/entry)}</b></div></div><p class="note">Isi stop di bawah harga beli untuk menghitung jumlah berdasarkan risiko.</p>`; return; }
    const lossPer=(entry-stop)/entry+2*f, maxRisk=modal*(risk||2)/100, amt=Math.min(modal,maxRisk/lossPer), q=amt*(1-f)/entry;
    const loss=q*stop*(1-f)-amt, gain=target?q*target*(1-f)-amt:null, rr=gain!=null?gain/Math.abs(loss):null;
    out.innerHTML=`<div class="statgrid"><div>Dana yang dibelikan<b>${rpM(amt)}</b></div><div>Dapat koin<b>${qtyTx(q)}</b></div>
      <div>Bila kena stop<b class="no">−${rpM(Math.abs(loss))}</b></div><div>Bila kena target<b class="ok">${gain!=null?"+"+rpM(gain):"–"}</b></div>
      <div>Untung : rugi<b class="${rr>=2?"ok":rr!=null&&rr<1?"no":""}">${rr!=null?"1 : "+nf(rr,1):"–"}</b></div><div>Porsi dari modal<b>${pct(amt/modal*100,0,false)}</b></div></div>
      ${amt>=modal?'<p class="note">Stop sangat dekat, jadi hitungan risikonya membolehkan seluruh modal. Tetap pertimbangkan membagi ke beberapa koin.</p>':""}
      ${rr!=null&&rr<2?`<p class="no">Untung : rugi di bawah 1 : 2. ${T("Biasanya kurang layak.","Di bawah syarat Watchlist.")}</p>`:""}
      <p><button type="button" class="calcbtn" id="c_toporto">💼 Catat ke Portofolio</button></p>`;
    $("c_toporto").addEventListener("click",()=>{ const o=rows.find(x=>x.ticker===st.code), ms=o?mget(o,"mom90").s:""; addToPorto({code:st.code,price:entry,amt,stop,target,meth:st.code==="BTC"?"btc200":["buy","hold"].includes(ms)?"mom90":"support"}); });
  };
  box.querySelectorAll("input").forEach(i=>i.addEventListener("input",calc));
  $("c_code").addEventListener("change",()=>{ const t=$("c_code").value.trim().toUpperCase(); if(rows.some(o=>o.ticker===t)){ saveCalc(Object.assign(calcState(),{code:t})); openCalc(t); } });
  calc();
}

// ---------- navigasi ----------
const GROUPS=[{id:"home",ic:"🏠",name:"Beranda",tabs:["summary"]},{id:"metode",ic:"🚦",name:"Metode",tabs:["lamp","mom90"]},
  {id:"watch",ic:"📍",name:"Watchlist",tabs:["watch"]},{id:"porto",ic:"💼",name:"Portofolio",tabs:["porto"]},{id:"alat",ic:"🧰",name:"Alat",tabs:["cycles","hot","calc"]}];
