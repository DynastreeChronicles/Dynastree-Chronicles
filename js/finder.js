/* Trade finder (market/#finder). Pick your team, say what you are willing to move (specific players and picks, or whole positions), press Find trades,
   and it looks at every other roster for a real need at that position, then builds a few roughly even deals around it.
   "Need" is measured as how much the offered players would raise that team's starting lineup (best value at each starting slot), so a team
   with a hole or an injured starter at a position scores high and a team that is already deep there scores zero. Values are FantasyCalc, as in The Market. */
(()=>{
const NF=n=>Math.round(n).toLocaleString('en-US'),SG=n=>(n>0?'+':n<0?'\u2212':'')+NF(Math.abs(n));
const E=s=>String(s??'').replace(/[&<>"]/g,c=>'&#'+c.charCodeAt(0)+';');
const POS=['QB','RB','WR','TE'];
let DATA=null,root,ST,LAST=[];

/* ---------- pure logic ---------- */
function items(m){
  const t=DATA.managers[m];if(!t)return[];
  const out=t.assets.map(a=>({k:'p:'+a[0],n:a[1],p:a[2],v:a[3],d:a[4],st:a[5],out:!!a[6]}));
  t.picklist.forEach(x=>out.push({k:'k:'+x[0],n:x[0],p:'PICK',v:x[1],d:x[3],via:x[2],out:false}));
  return out.sort((x,y)=>y.v-x.v);
}
/* Fill the starting lineup greedily: fixed slots first, then FLEX, then SUPER_FLEX, each with the best value still available.
   Players who are on IR or out do not start. Returns the starters and their total. */
function lineup(list){
  const L=DATA.lineup,avail=list.filter(x=>x.p!=='PICK'&&!x.out).sort((a,b)=>b.v-a.v),used=new Set(),starters=[];
  const take=elig=>{const x=avail.find(a=>!used.has(a.k)&&elig.includes(a.p));if(x){used.add(x.k);starters.push(x)}};
  POS.forEach(p=>{for(let i=0;i<(L[p]||0);i++)take([p])});
  for(let i=0;i<(L.FLEX||0);i++)take(['RB','WR','TE']);
  for(let i=0;i<(L.SUPER_FLEX||0);i++)take(POS);
  return{starters,total:starters.reduce((s,x)=>s+x.v,0),keys:used};
}
const without=(list,ks)=>list.filter(x=>!ks.has(x.k));
function pairs(pool,max){const out=pool.map(x=>[x]);const top=pool.slice(0,max);for(let i=0;i<top.length;i++)for(let j=i+1;j<top.length;j++)out.push([top[i],top[j]]);return out}
function packages(pool){
  const out=pairs(pool.slice().sort((a,b)=>b.v-a.v),9);
  if(pool.length>=3&&pool.length<=4)out.push(pool.slice());
  return out.slice(0,70);
}
function combos(pool,vO,tol){   // 1 or 2 assets from the other team whose value is within tol of vO
  const out=[];
  for(let i=0;i<pool.length;i++){
    const a=pool[i];if(Math.abs(a.v-vO)/Math.max(a.v,vO)<=tol)out.push([a]);
    for(let j=i+1;j<pool.length;j++){const s=a.v+pool[j].v;if(Math.abs(s-vO)/Math.max(s,vO)<=tol)out.push([a,pool[j]])}
  }
  return out.map(c=>({c,v:c.reduce((s,x)=>s+x.v,0)})).sort((x,y)=>Math.abs(x.v-vO)-Math.abs(y.v-vO)).slice(0,14);
}
function find(me,offerPool,opts){
  const tol=opts.tol,want=new Set(opts.want||[]),mine=items(me),base=lineup(mine),res=[];
  const pk=packages(offerPool);
  Object.keys(DATA.managers).filter(m=>m!==me).forEach(T=>{
    const theirs=items(T),tb=lineup(theirs);
    const returnable=theirs.filter(x=>x.v>0&&!x.out&&(x.p==='PICK'?opts.picks:(!want.size||want.has(x.p))));
    pk.forEach(O=>{
      const vO=O.reduce((s,x)=>s+x.v,0);if(vO<=0)return;
      const ok=new Set(O.map(x=>x.k)),gain=lineup(theirs.concat(O)).total-tb.total;if(gain<=0)return;   // no starting-lineup need for this package
      combos(returnable,vO,tol).forEach(({c,v:vR})=>{
        const rk=new Set(c.map(x=>x.k)),tAfter=lineup(without(theirs,rk).concat(O)),netT=tAfter.total-tb.total;if(netT<=0)return;
        const uAfter=lineup(without(mine,ok).concat(c)),netU=uAfter.total-base.total;
        const fair=1-Math.abs(vR-vO)/Math.max(vR,vO)/tol,needT=Math.min(netT/vO,.6)/.6,uS=Math.max(-.5,Math.min(netU/vO,.5))+.5;
        const bonus=want.size&&c.some(x=>want.has(x.p))?.08:0;
        res.push({team:T,send:O,get:c,vO,vR,netT,netU,tEnter:tAfter.starters.filter(x=>!tb.keys.has(x.k)),tOut:tb.starters.filter(x=>!tAfter.keys.has(x.k)),
                  uEnter:uAfter.starters.filter(x=>!base.keys.has(x.k)),uOut:base.starters.filter(x=>!uAfter.keys.has(x.k)),score:.45*needT+.35*fair+.2*uS+bonus});
      });
    });
  });
  res.sort((a,b)=>b.score-a.score);
  const out=[],per={},seen=new Set();
  for(const r of res){const id=r.team+'|'+r.send.map(x=>x.k).sort()+'|'+r.get.map(x=>x.k).sort();if(seen.has(id))continue;
    if((per[r.team]||0)>=2)continue;
    if(out.some(o=>o.team===r.team&&o.send.some(s=>r.send.some(q=>q.k===s.k))))continue;   // two options for one team should offer different players
    seen.add(id);per[r.team]=(per[r.team]||0)+1;out.push(r);if(out.length>=5)break}
  return out;
}

/* ---------- rendering ---------- */
const q=r=>root.querySelector(`[data-r="${r}"]`);
const names=a=>a.map(x=>x.n).join(' and ');
function why(o){
  const L=[];
  const inn=o.tEnter.filter(x=>o.send.some(s=>s.k===x.k));
  if(inn.length){const out=o.tOut[0];L.push(`<b>${E(o.team)}</b> has the need: ${E(names(inn))} would start for them${out?`, pushing ${E(out.n)} (${E(out.p)}) out of the lineup`:' in an open spot'}, a ${SG(o.netT)} upgrade to their starting lineup.`)}
  const bench=o.get.filter(x=>x.p==='PICK'||!o.tOut.some(y=>y.k===x.k));
  if(bench.length===o.get.length)L.push(`It costs them nothing in their lineup: ${E(names(o.get))} ${o.get.every(x=>x.p==='PICK')?'are picks':'come off their bench'}.`);
  else L.push(`It does cost them ${E(names(o.tOut.filter(x=>o.get.some(g=>g.k===x.k))))} in the lineup, but the upgrade is bigger.`);
  const e=o.uEnter.filter(x=>o.get.some(g=>g.k===x.k));
  L.push(o.netU>0?`For you: ${e.length?E(names(e))+' would start, ':''}your starting lineup ${SG(o.netU)}.`:o.netU<0?`For you: your starting lineup drops ${NF(-o.netU)}, the price of moving ${E(names(o.send))}.`:'For you: your starting lineup does not change.');
  return L.map(x=>`<li>${x}</li>`).join('');
}
function row(i){return `<li><span class="cn"><b>${E(i.n)}</b><small>${E(i.p==='PICK'?'Pick':i.p)}</small></span><span class="cv">${NF(i.v)}</span></li>`}
function card(o,idx){
  const pct=Math.round(100*Math.abs(o.vR-o.vO)/Math.max(o.vR,o.vO)),lab=pct<5?'Even':'Fair';
  return `<article class="fopt"><header><span class="fn">Option ${idx+1}</span><h4>with ${E(o.team)}</h4><em class="cvm even"><em>${lab} &middot; ${pct}% apart</em></em></header>
<div class="fcols"><div><small>You send</small><ul>${o.send.map(row).join('')}</ul><p>${NF(o.vO)}</p></div><div><small>You get</small><ul>${o.get.map(row).join('')}</ul><p>${NF(o.vR)}</p></div></div>
<ul class="fwhy">${why(o)}</ul><p class="fact"><button type="button" class="btn o" data-act="open" data-i="${idx}">Open in calculator</button></p></article>`;
}
function pool(){
  const mine=items(ST.me),out=[],have=new Set();
  mine.forEach(i=>{if((i.p!=='PICK'&&ST.pos.has(i.p))||ST.chk.has(i.k)){if(!have.has(i.k)){have.add(i.k);out.push(i)}}});
  return out.filter(i=>i.v>0);
}
function renderOwn(){
  const own=q('f-own'),box=q('f-ownbox');
  if(!ST.me){box.hidden=true;return}
  box.hidden=false;
  own.innerHTML=items(ST.me).filter(i=>i.v>0).map(i=>`<li><label><input type="checkbox" data-f="chk" data-k="${E(i.k)}"${ST.chk.has(i.k)?' checked':''}><span class="cn"><b>${E(i.n)}</b><small>${E(i.p==='PICK'?'Pick':i.p)}${i.out?' \u00b7 <span class="outt">'+E(i.st||'out')+'</span>':''}</small></span><span class="cv">${NF(i.v)}</span></label></li>`).join('');
}
function renderChips(){
  ['pos','want'].forEach(k=>{q('f-'+k).innerHTML=POS.map(p=>`<button type="button" class="chip" aria-pressed="${ST[k].has(p)}" data-act="chip" data-k="${k}" data-p="${p}">${p}</button>`).join('')});
  const n=pool().length;q('f-count').textContent=ST.me?(n?`${n} ${n===1?'asset is':'assets are'} on the table.`:'Nothing is on the table yet.'):'';
}
function run(){
  if(!ST.me){q('f-msg').textContent='Choose your team first.';return}
  const p=pool();if(!p.length){q('f-msg').textContent='Offer at least one position or player.';return}
  q('f-msg').textContent='';
  LAST=find(ST.me,p,{tol:ST.tol,want:[...ST.want],picks:ST.picks});
  q('f-out').innerHTML=LAST.length?LAST.map(card).join(''):'<p class="key">No team has a lineup need that these assets fill at a close value. Try offering a different position, widening the value tolerance, or including more assets.</p>';
}
function init(el,data){
  root=el;DATA=data;ST={me:'',chk:new Set(),pos:new Set(),want:new Set(),tol:.10,picks:true};
  const mg=Object.keys(DATA.managers).sort((x,y)=>x.toLowerCase()<y.toLowerCase()?-1:1);
  root.innerHTML=`<div class="fnd"><div class="ctool"><label class="cl">Your team<select data-f="me" data-r="f-team"><option value="">Choose&hellip;</option>${mg.map(m=>`<option value="${E(m)}">${E(m)}</option>`).join('')}</select></label>
<label class="cl">How close in value<select data-f="tol" data-r="f-tol"><option value=".05">Very close (within 5%)</option><option value=".10" selected>Fair (within 10%)</option><option value=".20">Flexible (within 20%)</option></select></label>
<label class="chk"><input type="checkbox" data-f="picks" checked> Include draft picks in return</label></div>
<p class="key cap">Offer by position (any player you have there is available)</p><div class="chips" data-r="f-pos"></div>
<p class="key cap">Looking for (optional)</p><div class="chips" data-r="f-want"></div>
<details class="cown" data-r="f-ownbox" open hidden><summary>Or pick the exact players and picks to offer</summary><ul class="cownl" data-r="f-own"></ul></details>
<p class="fgo"><button type="button" class="btn" data-act="find">Find trades</button><span class="key" data-r="f-count"></span><span class="key" data-r="f-msg" aria-live="polite"></span></p>
<div data-r="f-out" aria-live="polite"></div>
<p class="key">A team has a "need" when the players you offer would raise its starting lineup (best value in each starting slot; injured players do not start). Values are FantasyCalc, a plain sum. Suggestions are starting points for a conversation, not offers anyone has agreed to.</p></div>`;
  renderChips();
  root.addEventListener('change',e=>{const f=e.target.closest&&e.target.closest('[data-f]');if(!f)return;const k=f.dataset.f;
    if(k==='me'){ST.me=f.value;ST.chk.clear();renderOwn();renderChips()}
    else if(k==='tol')ST.tol=+f.value;else if(k==='picks')ST.picks=!!f.checked;
    else if(k==='chk'){f.checked?ST.chk.add(f.dataset.k):ST.chk.delete(f.dataset.k);renderChips()}});
  root.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('[data-act]');if(!b)return;const a=b.dataset.act;
    if(a==='chip'){const s=ST[b.dataset.k],p=b.dataset.p;s.has(p)?s.delete(p):s.add(p);renderChips()}
    else if(a==='find')run();
    else if(a==='open'){const o=LAST[+b.dataset.i];if(o&&window.DynCalc)window.DynCalc.load(ST.me,o.team,o.send.map(x=>x.k),o.get.map(x=>x.k))}});
}
if(typeof module!=='undefined')module.exports={init,items,lineup,find,packages,combos,pool,_st:()=>ST,_set:d=>{DATA=d}};
else{const el=document.getElementById('finder-app');if(el&&window.DynCalc)init(el,window.DynCalc.data())}
})();
