/* Trade finder (market/#finder). Pick your team, say what you are willing to move (specific players and picks, or whole positions, or just picks),
   press Find trades, and it looks at every other roster for a deal both sides could like.
   Two ideas drive it:
   1. NEED: how much the offered players would raise a team's starting lineup (best FantasyCalc value in each starting slot; injured players do not start).
   2. WINDOW: every team is read as a Contender, Retooling or Rebuilder from its lineup strength, its record and how old its starters are. A rebuilder values
      picks and young players above market and discounts older players; a contender does the opposite. A deal has to be fair in market value AND make sense
      for the other team's window, so offering only picks finds the rebuilders who would sell veterans for them. */
(()=>{
const NF=n=>Math.round(n).toLocaleString('en-US'),SG=n=>(n>0?'+':n<0?'\u2212':'')+NF(Math.abs(n));
const E=s=>String(s??'').replace(/[&<>"]/g,c=>'&#'+c.charCodeAt(0)+';');
const POS=['QB','RB','WR','TE'],LAB={contend:'Contender',retool:'Retooling',rebuild:'Rebuilder'},ISA={contend:'a contender',retool:'retooling',rebuild:'a rebuilder'};
let DATA=null,root,ST,LAST=[];

/* ---------- pure logic ---------- */
function items(m){
  const t=DATA.managers[m];if(!t)return[];
  const out=t.assets.map(a=>({k:'p:'+a[0],n:a[1],p:a[2],v:a[3],d:a[4],st:a[5],out:!!a[6],age:a[7]||0}));
  t.picklist.forEach(x=>out.push({k:'k:'+x[0],n:x[0],p:'PICK',v:x[1],d:x[3],via:x[2],out:false,age:0}));
  return out.sort((x,y)=>y.v-x.v);
}
/* Fill the starting lineup greedily: fixed slots first, then FLEX, then SUPER_FLEX, each with the best value still available. Injured players do not start. */
function lineup(list){
  const L=DATA.lineup,avail=list.filter(x=>x.p!=='PICK'&&!x.out).sort((a,b)=>b.v-a.v),used=new Set(),starters=[];
  const take=elig=>{const x=avail.find(a=>!used.has(a.k)&&elig.includes(a.p));if(x){used.add(x.k);starters.push(x)}};
  POS.forEach(p=>{for(let i=0;i<(L[p]||0);i++)take([p])});
  for(let i=0;i<(L.FLEX||0);i++)take(['RB','WR','TE']);
  for(let i=0;i<(L.SUPER_FLEX||0);i++)take(POS);
  return{starters,total:starters.reduce((s,x)=>s+x.v,0),keys:used};
}
/* Contender / Retooling / Rebuilder for every team. Score 0 to 1: 50% lineup strength (rank among teams), 30% record, 20% how old the starters are
   (value-weighted age, 24 or younger = 0, 30 or older = 1). 0.60 and up contends, 0.40 and down rebuilds. */
function modes(){
  const ms=Object.keys(DATA.managers),info={};
  ms.forEach(m=>{const l=lineup(items(m)),w=l.starters.reduce((s,x)=>s+x.v,0)||1;
    info[m]={lineup:l.total,age:l.starters.reduce((s,x)=>s+(x.age||26)*x.v,0)/w}});
  const byL=ms.slice().sort((a,b)=>info[b].lineup-info[a].lineup),n=Math.max(ms.length-1,1);
  ms.forEach(m=>{const i=info[m],lr=byL.indexOf(m)+1,st=DATA.managers[m].standing||Math.round((ms.length+1)/2);
    const s=.5*((ms.length-lr)/n)+.3*((ms.length-st)/n)+.2*Math.max(0,Math.min((i.age-24)/6,1));
    Object.assign(i,{lineupRank:lr,standing:st,score:s,mode:s>=.6?'contend':s<=.4?'rebuild':'retool'})});
  return info;
}
/* What a team of that window thinks an asset is worth, as a multiple of market value. */
function factor(mode,x){
  if(x.p==='PICK')return mode==='rebuild'?1.12:mode==='contend'?.9:1;
  const a=x.age||26;
  if(mode==='rebuild')return a<=22?1.15:a<=24?1.08:a<=26?1:a<=27?.95:a<=28?.88:a<=29?.8:.7;
  if(mode==='contend')return a<=22?.9:a<=24?.96:a<=27?1:a<=29?1.04:1.02;
  return 1;
}
const perceived=(list,mode)=>list.reduce((s,x)=>s+x.v*factor(mode,x),0);
const without=(list,ks)=>list.filter(x=>!ks.has(x.k));
function packages(pool){
  const top=pool.slice().sort((a,b)=>b.v-a.v),out=top.map(x=>[x]);const t=top.slice(0,9);
  for(let i=0;i<t.length;i++)for(let j=i+1;j<t.length;j++)out.push([t[i],t[j]]);
  if(top.length>=3&&top.length<=4)out.push(top.slice());
  return out.slice(0,70);
}
function combos(pool,vO,tol){   // 1 or 2 assets from the other team whose market value is within tol of vO
  const out=[];
  for(let i=0;i<pool.length;i++){
    const a=pool[i];if(Math.abs(a.v-vO)/Math.max(a.v,vO)<=tol)out.push([a]);
    for(let j=i+1;j<pool.length;j++){const s=a.v+pool[j].v;if(Math.abs(s-vO)/Math.max(s,vO)<=tol)out.push([a,pool[j]])}
  }
  return out.map(c=>({c,v:c.reduce((s,x)=>s+x.v,0)})).sort((x,y)=>Math.abs(x.v-vO)-Math.abs(y.v-vO)).slice(0,14);
}
const W={contend:[.30,.10],retool:[.20,.20],rebuild:[.10,.30]};   // weight on their lineup gain, on how they value the package
function find(me,offerPool,opts){
  const tol=opts.tol,want=new Set(opts.want||[]),mine=items(me),base=lineup(mine),M=modes(),res=[];
  const meMode=opts.mode&&opts.mode!=='auto'?opts.mode:M[me].mode,picksOnly=offerPool.every(x=>x.p==='PICK');
  const pk=packages(offerPool);
  Object.keys(DATA.managers).filter(m=>m!==me).forEach(T=>{
    const theirs=items(T),tb=lineup(theirs),tm=M[T].mode;
    const returnable=theirs.filter(x=>x.v>0&&!x.out&&(x.p==='PICK'?opts.picks:(!want.size||want.has(x.p))));
    pk.forEach(O=>{
      const vO=O.reduce((s,x)=>s+x.v,0);if(vO<=0)return;
      const ok=new Set(O.map(x=>x.k));
      if(tm==='contend'&&lineup(theirs.concat(O)).total-tb.total<=0)return;   // a contender needs the lineup help
      combos(returnable,vO,tol).forEach(({c,v:vR})=>{
        const rk=new Set(c.map(x=>x.k)),tAfter=lineup(without(theirs,rk).concat(O)),netT=tAfter.total-tb.total;
        const percT=perceived(O,tm)-perceived(c,tm),percU=perceived(c,meMode)-perceived(O,meMode);
        const accept=netT>0||(tm!=='contend'&&percT>=.04*vO);
        if(!accept||percT<-.03*vO)return;
        const uAfter=lineup(without(mine,ok).concat(c)),netU=uAfter.total-base.total;
        if(picksOnly&&meMode==='contend'&&netU<=0)return;   // picks should buy you a better lineup
        const fair=1-Math.abs(vR-vO)/Math.max(vR,vO)/tol,needT=Math.max(0,Math.min(netT/vO,.6))/.6;
        const pT=(Math.max(-.1,Math.min(percT/vO,.25))+.1)/.35,uS=Math.max(-.5,Math.min(netU/vO,.5))+.5,uP=(Math.max(-.1,Math.min(percU/vO,.25))+.1)/.35;
        const bonus=want.size&&c.some(x=>want.has(x.p))?.08:0,[wn,wp]=W[tm];
        res.push({team:T,tm,send:O,get:c,vO,vR,netT,netU,percT,percU,rPerc:perceived(O,tm),gPerc:perceived(c,tm),
                  tEnter:tAfter.starters.filter(x=>!tb.keys.has(x.k)),tOut:tb.starters.filter(x=>!tAfter.keys.has(x.k)),
                  uEnter:uAfter.starters.filter(x=>!base.keys.has(x.k)),uOut:base.starters.filter(x=>!uAfter.keys.has(x.k)),
                  score:.25*fair+wn*needT+wp*pT+.15*uS+.10*uP+bonus});
      });
    });
  });
  res.sort((a,b)=>b.score-a.score);
  const out=[],per={},seen=new Set();
  for(const r of res){const id=r.team+'|'+r.send.map(x=>x.k).sort()+'|'+r.get.map(x=>x.k).sort();if(seen.has(id))continue;
    if((per[r.team]||0)>=2)continue;
    if(out.some(o=>o.team===r.team&&o.send.some(s=>r.send.some(q=>q.k===s.k))))continue;   // two options for one team should offer different assets
    seen.add(id);per[r.team]=(per[r.team]||0)+1;out.push(r);if(out.length>=5)break}
  return out;
}

/* ---------- rendering ---------- */
const q=r=>root.querySelector(`[data-r="${r}"]`);
const names=a=>a.map(x=>x.n).join(' and ');
const agel=x=>x.p==='PICK'?'':x.age?` \u00b7 age ${Math.round(x.age)}`:'';
function why(o){
  const L=[],inn=o.tEnter.filter(x=>o.send.some(s=>s.k===x.k));
  if(inn.length)L.push(`<b>${E(o.team)}</b> has the need: ${E(names(inn))} would start for them${o.tOut[0]?`, pushing ${E(o.tOut[0].n)} out of the lineup`:' in an open spot'}, a ${SG(o.netT)} upgrade to their starting lineup.`);
  else L.push(`<b>${E(o.team)}</b>: this one is about value and timing rather than a lineup hole. They would value what they get at ${NF(o.rPerc)} against ${NF(o.gPerc)} for what they give up.`);
  const bench=o.get.filter(x=>x.p==='PICK'||!o.tOut.some(y=>y.k===x.k));
  if(o.netT>0)L.push(bench.length===o.get.length?`It costs their lineup nothing: ${E(names(o.get))} ${o.get.every(x=>x.p==='PICK')?'are picks':'come off their bench'}.`:`It does cost them ${E(names(o.tOut.filter(x=>o.get.some(g=>g.k===x.k))))} in the lineup, but the upgrade is bigger.`);
  const e=o.uEnter.filter(x=>o.get.some(g=>g.k===x.k));
  L.push(o.netU>0?`For you: ${e.length?E(names(e))+' would start, ':''}your starting lineup ${SG(o.netU)}.`:o.netU<0?`For you: your starting lineup drops ${NF(-o.netU)}, the price of moving ${E(names(o.send))}.`:'For you: your starting lineup does not change.');
  return L.map(x=>`<li>${x}</li>`).join('');
}
function row(i){return `<li><span class="cn"><b>${E(i.n)}</b><small>${E(i.p==='PICK'?'Pick':i.p)}${agel(i)}</small></span><span class="cv">${NF(i.v)}</span></li>`}
function card(o,idx){
  const pct=Math.round(100*Math.abs(o.vR-o.vO)/Math.max(o.vR,o.vO)),lab=pct<5?'Even':'Fair';
  return `<article class="fopt"><header><span class="fn">Option ${idx+1}</span><h4>with ${E(o.team)}</h4><span class="cvm even"><em>${lab} &middot; ${pct}% apart</em></span></header>
<div class="fcols"><div><small>You send</small><ul>${o.send.map(row).join('')}</ul><p>${NF(o.vO)}</p></div><div><small>You get</small><ul>${o.get.map(row).join('')}</ul><p>${NF(o.vR)}</p></div></div>
<ul class="fwhy">${why(o)}</ul><p class="fact"><button type="button" class="btn o" data-act="open" data-i="${idx}">Open in calculator</button></p></article>`;
}
function pool(){
  const mine=items(ST.me),out=[],have=new Set();
  mine.forEach(i=>{const byPos=i.p==='PICK'?ST.pos.has('PICK'):ST.pos.has(i.p);if(byPos||ST.chk.has(i.k)){if(!have.has(i.k)){have.add(i.k);out.push(i)}}});
  return out.filter(i=>i.v>0);
}
function renderOwn(){
  const own=q('f-own'),box=q('f-ownbox');
  if(!ST.me){box.hidden=true;return}
  box.hidden=false;
  own.innerHTML=items(ST.me).filter(i=>i.v>0).map(i=>`<li><label><input type="checkbox" data-f="chk" data-k="${E(i.k)}"${ST.chk.has(i.k)?' checked':''}><span class="cn"><b>${E(i.n)}</b><small>${E(i.p==='PICK'?'Pick':i.p)}${agel(i)}${i.out?' \u00b7 <span class="outt">'+E(i.st||'out')+'</span>':''}</small></span><span class="cv">${NF(i.v)}</span></label></li>`).join('');
}
function renderChips(){
  q('f-pos').innerHTML=POS.concat('PICK').map(p=>`<button type="button" class="chip" aria-pressed="${ST.pos.has(p)}" data-act="chip" data-k="pos" data-p="${p}">${p==='PICK'?'Picks':p}</button>`).join('');
  q('f-want').innerHTML=POS.map(p=>`<button type="button" class="chip" aria-pressed="${ST.want.has(p)}" data-act="chip" data-k="want" data-p="${p}">${p}</button>`).join('');
  const n=pool().length;q('f-count').textContent=ST.me?(n?`${n} ${n===1?'asset is':'assets are'} on the table.`:'Nothing is on the table yet.'):'';
}
function run(){
  if(!ST.me){q('f-msg').textContent='Choose your team first.';return}
  const p=pool();if(!p.length){q('f-msg').textContent='Offer at least one position, pick or player.';return}
  q('f-msg').textContent='';
  LAST=find(ST.me,p,{tol:ST.tol,want:[...ST.want],picks:ST.picks,mode:ST.mode});
  q('f-out').innerHTML=LAST.length?LAST.map((o,i)=>card(o,i)).join(''):'<p class="key">No team has a deal that works for both sides at these values. Try offering something different, widening the value tolerance, or letting picks come back.</p>';
}
function init(el,data){
  root=el;DATA=data;ST={me:'',chk:new Set(),pos:new Set(),want:new Set(),tol:.10,picks:true,mode:'auto'};
  const mg=Object.keys(DATA.managers).sort((x,y)=>x.toLowerCase()<y.toLowerCase()?-1:1);
  root.innerHTML=`<div class="fnd"><div class="ctool"><label class="cl">Your team<select data-f="me" data-r="f-team"><option value="">Choose&hellip;</option>${mg.map(m=>`<option value="${E(m)}">${E(m)}</option>`).join('')}</select></label>
<label class="cl">Your role<select data-f="mode"><option value="auto" selected>Let the finder decide</option><option value="contend">Win now</option><option value="retool">Balanced</option><option value="rebuild">Build for the future</option></select></label>
<label class="cl">How close in value<select data-f="tol" data-r="f-tol"><option value=".05">Very close (within 5%)</option><option value=".10" selected>Fair (within 10%)</option><option value=".20">Flexible (within 20%)</option></select></label>
<label class="chk"><input type="checkbox" data-f="picks" checked> Include draft picks in return</label></div>
<p class="key cap">Offer by position or picks (everything you have there is available)</p><div class="chips" data-r="f-pos"></div>
<p class="key cap">Looking for (optional)</p><div class="chips" data-r="f-want"></div>
<details class="cown" data-r="f-ownbox" open hidden><summary>Or pick the exact players and picks to offer</summary><ul class="cownl" data-r="f-own"></ul></details>
<p class="fgo"><button type="button" class="btn" data-act="find">Find trades</button><button type="button" class="btn o" data-act="reset">Reset</button><span class="key" data-r="f-count"></span><span class="key" data-r="f-msg" aria-live="polite"></span></p>
<div data-r="f-out" aria-live="polite"></div>
</div>`;
  renderChips();
  root.addEventListener('change',e=>{const f=e.target.closest&&e.target.closest('[data-f]');if(!f)return;const k=f.dataset.f;
    if(k==='me'){ST.me=f.value;ST.chk.clear();renderOwn();renderChips()}
    else if(k==='tol')ST.tol=+f.value;else if(k==='mode')ST.mode=f.value;else if(k==='picks')ST.picks=!!f.checked;
    else if(k==='chk'){f.checked?ST.chk.add(f.dataset.k):ST.chk.delete(f.dataset.k);renderChips()}});
  root.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('[data-act]');if(!b)return;const a=b.dataset.act;
    if(a==='chip'){const s=ST[b.dataset.k],p=b.dataset.p;s.has(p)?s.delete(p):s.add(p);renderChips()}
    else if(a==='find')run();
    else if(a==='reset'){ST={me:'',chk:new Set(),pos:new Set(),want:new Set(),tol:.10,picks:true,mode:'auto'};LAST=[];
      root.querySelectorAll('[data-f="me"]').forEach(x=>x.value='');root.querySelectorAll('[data-f="mode"]').forEach(x=>x.value='auto');root.querySelectorAll('[data-f="tol"]').forEach(x=>x.value='.10');
      root.querySelectorAll('[data-f="picks"]').forEach(x=>x.checked=true);q('f-out').innerHTML='';q('f-msg').textContent='';renderOwn();renderChips()}
    else if(a==='open'){const o=LAST[+b.dataset.i];if(o&&window.DynCalc)window.DynCalc.load(ST.me,o.team,o.send.map(x=>x.k),o.get.map(x=>x.k))}});
}
if(typeof module!=='undefined')module.exports={init,items,lineup,modes,factor,find,packages,combos,pool,_set:d=>{DATA=d}};
else{const el=document.getElementById('finder-app');if(el&&window.DynCalc)init(el,window.DynCalc.data())}
})();
