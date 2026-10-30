function renderDrawer(box){
  const old=document.getElementById("drawer"); if(old) old.remove(); const os=document.getElementById("scrim"); if(os) os.remove();
  if(!openTicker) { document.body.style.overflow=""; return; }
  const o=rows.find(x=>x.ticker===openTicker); if(!o) return;
  const sc=document.createElement("div"); sc.className="scrim"; sc.id="scrim";
  const d=document.createElement("div"); d.className="drawer"; d.id="drawer"; d.setAttribute("role","dialog"); d.setAttribute("aria-label","Detail "+o.ticker);
  d.innerHTML=`<div class="dr-h"><div>${starBtn(o.ticker)} <b>${esc(o.ticker)}</b> <span class="num">${usd(o.price)}</span> <span class="num ${o.chg1d>0?"ok":o.chg1d<0?"no":""}">${pct(o.chg1d)}</span><br><span class="note">${esc(o.company||"")} · ${esc(o.sector||"")}</span></div><div style="display:flex;gap:6px">${chartBtn(o.ticker)}${calcBtn(o.ticker)}<button type="button" class="iconbtn" id="drClose" aria-label="Tutup">✕</button></div></div><div class="dr-b">${detail(o)}</div>`;
  box.appendChild(sc); box.appendChild(d); document.body.style.overflow="hidden";
  const close=()=>{ openTicker=null; renderResults(); };
  sc.addEventListener("click",close); d.querySelector("#drClose").addEventListener("click",close);
}
document.addEventListener("keydown",ev=>{ if(ev.key==="Escape"&&openTicker){ openTicker=null; renderResults(); } });
function renderResults(){
  const box=$("results");
  if(!DATA){ box.innerHTML=`<div class="tablebox"><div class="empty">Belum ada data. Setelah workflow kripto selesai, daftar koin muncul di sini.</div></div>`; return; }
  if(tab==="summary") renderSummary(box); else if(tab==="lamp") renderLamp(box); else if(tab==="hot") renderHot(box); else if(tab==="cycles") renderCycles(box); else if(tab==="watch") renderWatch(box); else if(tab==="calc") renderCalc(box); else if(tab==="porto") renderPorto(box); else renderMethod(box,MID[tab]||M[0]);
  renderDrawer(box);
}
function renderAll(){ renderStatus(); renderTabs(); renderRail(); renderResults(); }

// ---------- events ----------
$("tabs").addEventListener("click",ev=>{ const b=ev.target.closest(".tab"); if(!b) return; goTab(b.dataset.id); });
function toggleRow(tr){ openTicker=openTicker===tr.dataset.t?null:tr.dataset.t; renderResults(); const again=document.querySelector(`tr.row[data-t="${CSS.escape(tr.dataset.t)}"]`); if(again) again.focus({preventScroll:true}); }
$("results").addEventListener("click",ev=>{
  const sl=ev.target.closest("[data-sell]"); if(sl){ ev.stopPropagation(); sellDialog(+sl.dataset.sell); return; }
  const chb=ev.target.closest(".chartbtn"); if(chb){ ev.stopPropagation(); openChart(chb.dataset.chart); return; }
  const cb=ev.target.closest(".calcbtn[data-calc]"); if(cb){ ev.stopPropagation(); openCalc(cb.dataset.calc,cb.dataset.e?{entry:+cb.dataset.e,stop:+cb.dataset.s,target:+cb.dataset.tg||null}:null); return; }
  const sb=ev.target.closest(".star"); if(sb){ ev.stopPropagation(); toggleStar(sb.dataset.star); renderTabs(); renderResults(); return; }
  if(ev.target.closest("form,input,select,label,button")) return;
  const wr=ev.target.closest("tr.wrow"); if(wr){ store.set(WP+"cy.sel",wr.dataset.go); goTab("cycles"); window.scrollTo({top:0}); return; }
  const dr=ev.target.closest("div.row[data-t]"); if(dr){ openTicker=dr.dataset.t; renderResults(); return; }
  const tr=ev.target.closest("tr.row"); if(tr) toggleRow(tr); });
$("results").addEventListener("keydown",ev=>{ if(ev.key!=="Enter"&&ev.key!==" ") return; if(ev.target.closest("input,select,textarea,button")) return; const tr=ev.target.closest("tr.row"); if(!tr) return; ev.preventDefault(); if(tr.classList.contains("wrow")){ store.set(WP+"cy.sel",tr.dataset.go); goTab("cycles"); return; } toggleRow(tr); });
$("q").addEventListener("input",()=>{ renderTabs(); renderResults(); });
$("sector").addEventListener("change",()=>{ renderTabs(); renderResults(); });
document.querySelectorAll("#filters .seg button").forEach(b=>{
  b.setAttribute("aria-pressed",String(b.dataset.ix===ixFilter));
  b.addEventListener("click",()=>{ ixFilter=b.dataset.ix; store.set(WP+"ix",ixFilter); document.querySelectorAll("#filters .seg button").forEach(x=>x.setAttribute("aria-pressed",String(x===b))); renderTabs(); renderResults(); });
});
$("mainnav").addEventListener("click",ev=>{ const b=ev.target.closest("[data-g]"); if(!b) return; const g=GROUPS.find(x=>x.id===b.dataset.g); const last=store.get(WP+"g."+g.id); goTab(g.tabs.includes(last)?last:g.tabs[0]); window.scrollTo({top:0}); });
