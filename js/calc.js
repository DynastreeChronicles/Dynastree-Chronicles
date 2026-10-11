/* Trade calculator (market/#calculator). Everything runs in the browser from the data embedded in the page (#calc-data): the FantasyCalc
   top-1,000 index, every manager's roster and picks, and the league's real trades. Values are a plain sum, the same numbers as The Market. */
(()=>{
const NF=n=>Math.round(n).toLocaleString('en-US'),SG=n=>(n>0?'+':n<0?'\u2212':'')+NF(Math.abs(n));
const E=s=>String(s??'').replace(/[&<>"]/g,c=>'&#'+c.charCodeAt(0)+';');
let DATA=null,ALL=[],BYK={},ST,root;
const SIDES=['a','b'];

/* ---------- pure logic (also used by the tests) ---------- */
function build(data){
  DATA=data;ALL=[];BYK={};
  data.players.forEach(p=>{const it={k:'p:'+p[0],n:p[1],p:p[2],t:p[3],v:p[4],d:p[5]};ALL.push(it);BYK[it.k]=it});
  data.picks.forEach(p=>{const it={k:'k:'+p[0],n:p[0],p:'PICK',t:'',v:p[1],d:p[2]};ALL.push(it);BYK[it.k]=it});
  ALL.forEach(it=>it.s=(it.n+' '+it.p+' '+it.t).toLowerCase());
}
function ownList(m){
  const t=DATA.managers[m];if(!t)return[];
  const out=t.assets.map(a=>({k:'p:'+a[0],n:a[1],p:a[2],t:'',v:a[3],d:a[4],st:a[5]}));
  t.picklist.forEach(x=>out.push({k:'k:'+x[0],n:x[0],p:'PICK',t:'',v:x[1],d:x[3],via:x[2]}));
  return out.sort((x,y)=>y.v-x.v);
}
function mkItem(k,fallback){const b=BYK[k];if(b)return Object.assign({},b);return {k:k||('x:'+fallback.n),n:fallback.n,p:fallback.p||'',t:'',v:0,d:0,off:true}}
function sum(items){return items.reduce((s,i)=>s+i.v,0)}
function verdict(sa,sb){
  if(!sa||!sb)return{label:'',text:sa||sb?'Add something to the other side to compare.':'Add players or picks to each side to see the values.',diff:0,win:null};
  const diff=sa-sb,big=Math.max(sa,sb),pct=Math.abs(diff)/big;
  const label=pct<.05?'Even':pct<.15?'Fair enough':pct<.30?'Lopsided':'Robbery';
  return{label,diff,pct,win:pct<.05?null:(diff>0?'b':'a')};   // the side that sends LESS receives MORE
}
function rankOf(totals,m){const v=totals[m];return 1+Object.keys(totals).filter(x=>totals[x]>v).length}
function impact(s,side){
  const m=s[side].mgr,o=side==='a'?'b':'a';if(!m||!DATA.managers[m])return null;
  const t=DATA.managers[m],own=new Set(ownList(m).map(i=>i.k));
  const sent=s[side].items.filter(i=>own.has(i.k)),got=s[o].items;
  const dp=(arr,pick)=>arr.filter(i=>(i.p==='PICK')===pick).reduce((x,i)=>x+i.v,0);
  const roster=t.roster-dp(sent,false)+dp(got,false),picks=t.picks-dp(sent,true)+dp(got,true);
  return{m,before:t.total,after:roster+picks,roster,picks,foreign:s[side].items.length-sent.length};
}
function ranksAfter(s){
  const totals={};Object.keys(DATA.managers).forEach(m=>totals[m]=DATA.managers[m].total);
  const imp={};SIDES.forEach(x=>{imp[x]=impact(s,x)});SIDES.forEach(x=>{if(imp[x])totals[imp[x].m]=imp[x].after});
  const before={};Object.keys(DATA.managers).forEach(m=>before[m]=DATA.managers[m].total);
  SIDES.forEach(x=>{if(imp[x]){imp[x].rb=rankOf(before,imp[x].m);imp[x].ra=rankOf(totals,imp[x].m)}});
  return imp;
}
function suggestions(s){   // the side that sends LESS is the one coming out ahead; offer assets from its roster that close the gap
  const v=verdict(sum(s.a.items),sum(s.b.items));if(!v.win)return[];
  const add=v.win,gap=Math.abs(v.diff),m=s[add].mgr;if(!m)return[];const have=new Set(s[add].items.map(i=>i.k));
  return ownList(m).filter(i=>!have.has(i.k)&&i.v>0).sort((x,y)=>Math.abs(x.v-gap)-Math.abs(y.v-gap)).slice(0,3).map(i=>Object.assign({side:add},i));
}
function search(q,mgr){
  q=q.trim().toLowerCase();if(q.length<2)return[];const parts=q.split(/\s+/),own=new Set(mgr?ownList(mgr).map(i=>i.k):[]);
  return ALL.filter(i=>parts.every(p=>i.s.includes(p))).sort((x,y)=>(own.has(y.k)-own.has(x.k))||(y.v-x.v)).slice(0,8);
}

/* ---------- rendering ---------- */
const name=(s,x)=>s[x].mgr||('Side '+x.toUpperCase());
function itemRow(i,x,act){
  const tr=i.d?`<small class="${i.d<0?'dn':'up'}">${SG(i.d)} 30d</small>`:'';
  const note=i.off?'<small>not in the top 1,000 (valued 0)</small>':i.st?`<small class="out">${E(i.st)}</small>`:i.via?`<small>via ${E(i.via)}</small>`:'';
  return `<li><span class="cn"><b>${E(i.n)}</b><small>${E(i.p==='PICK'?'Pick':i.p+(i.t?' \u00b7 '+i.t:''))}</small>${note}</span><span class="cv">${NF(i.v)}${tr}</span>`+
    (act==='rm'?`<button type="button" class="cx" data-act="rm" data-s="${x}" data-k="${E(i.k)}" aria-label="Remove ${E(i.n)}">\u00d7</button>`:
     `<button type="button" class="ca" data-act="add" data-s="${x}" data-k="${E(i.k)}" aria-label="Add ${E(i.n)} to side ${x.toUpperCase()}">+</button>`)+'</li>';
}
function renderSide(x){
  const items=ST[x].items;
  q(`items-${x}`).innerHTML=items.length?items.map(i=>itemRow(i,x,'rm')).join(''):'<li class="empty">Nothing added yet.</li>';
  const m=ST[x].mgr,box=q(`own-${x}`);
  if(m&&DATA.managers[m]){
    const have=new Set(items.map(i=>i.k));
    box.hidden=false;q(`own-title-${x}`).textContent=`${m}'s roster and picks`;
    q(`own-list-${x}`).innerHTML=ownList(m).filter(i=>!have.has(i.k)).map(i=>itemRow(i,x,'add')).join('')||'<li class="empty">Everything is already added.</li>';
  }else box.hidden=true;
}
function renderResult(){
  const sa=sum(ST.a.items),sb=sum(ST.b.items),v=verdict(sa,sb);
  const side=(x,s)=>`<div><small>${E(name(ST,x))} sends</small><b>${NF(s)}</b><span>${ST[x].items.length} ${ST[x].items.length===1?'asset':'assets'}</span></div>`;
  const wname=v.win?name(ST,v.win):'';
  const sentence=v.label?(v.win?`<b>${E(wname)}</b> comes out ahead by <b>${NF(Math.abs(v.diff))}</b> (${Math.round(v.pct*100)}% of the bigger side).`:'The two sides are within 5% of each other.'):E(v.text);
  let h=`<div class="cvs">${side('a',sa)}<div class="cvm ${v.win||'even'}"><em>${E(v.label||'\u2014')}</em></div>${side('b',sb)}</div><p class="cvt">${sentence}</p>`;
  const imp=ranksAfter(ST),rows=SIDES.filter(x=>imp[x]).map(x=>{const i=imp[x],d=i.after-i.before;
    return `<tr><th scope="row">${E(i.m)}</th><td>${NF(i.before)} &rarr; <b>${NF(i.after)}</b></td><td class="${d<0?'dn':d>0?'up':''}">${SG(d)}</td><td>#${i.rb} &rarr; #${i.ra}</td><td>${NF(i.roster)} / ${NF(i.picks)}</td></tr>`}).join('');
  if(rows){h+=`<table class="cimp"><caption>What the trade does to each portfolio</caption><thead><tr><th>Manager</th><th>Total value</th><th>Change</th><th>League rank</th><th>Players / picks after</th></tr></thead><tbody>${rows}</tbody></table>`;
    const fo=SIDES.some(x=>imp[x]&&imp[x].foreign);if(fo)h+='<p class="key">One side includes assets that are not on that manager\'s roster; those do not count against their portfolio.</p>'}
  const sug=suggestions(ST);
  if(sug.length)h+=`<div class="csug"><b>To even it up, ${E(name(ST,sug[0].side))} could add:</b>${sug.map(i=>`<button type="button" class="chip" data-act="add" data-s="${i.side}" data-k="${E(i.k)}">${E(i.n)} <small>${NF(i.v)}</small></button>`).join('')}</div>`;
  q('res').innerHTML=h;
}
function render(){SIDES.forEach(renderSide);renderResult()}
function q(r){return root.querySelector(`[data-r="${r}"]`)}

/* ---------- state, link sharing ---------- */
function add(x,k){const b=mkItem(k,{n:k});if(!ST[x].items.some(i=>i.k===b.k)){ST[x].items.push(b)}}
function norm(s){return String(s).toLowerCase().replace(/[^a-z ]/g,'').replace(/\b(jr|sr|ii|iii|iv|v)\b/g,'').replace(/\s+/g,' ').trim()}
const ORD=n=>({1:'1st',2:'2nd',3:'3rd'}[n]||n+'th');
/* A key from this page, or a plain name such as "D'Andre Swift" or "2027 1st-round pick" (used by the links on the issue pages). */
function resolve(tok){
  if(BYK[tok])return tok;
  const low=String(tok).trim().toLowerCase(),pk=low.match(/(20\d\d)\s+(\d+)(?:st|nd|rd|th)/);
  if(pk&&/pick|round/.test(low)){const pre=(pk[1]+' '+ORD(+pk[2])).toLowerCase(),c=ALL.filter(i=>i.p==='PICK'&&i.n.toLowerCase().startsWith(pre));
    const hit=c.find(i=>/\(mid\)/i.test(i.n))||c.find(i=>!/\(/.test(i.n))||c[0];return hit?hit.k:null}
  const name=low.replace(/\s*\([^)]*\)/g,'').trim(),hit=ALL.find(i=>i.p!=='PICK'&&i.n.toLowerCase()===name)||ALL.find(i=>i.p!=='PICK'&&norm(i.n)===norm(name));
  return hit?hit.k:null;
}
function link(){
  const u=new URLSearchParams();if(ST.a.mgr)u.set('a',ST.a.mgr);if(ST.b.mgr)u.set('b',ST.b.mgr);
  if(ST.a.items.length)u.set('as',ST.a.items.map(i=>i.k).join('~'));if(ST.b.items.length)u.set('bs',ST.b.items.map(i=>i.k).join('~'));
  return location.origin+location.pathname+(u.toString()?'?'+u.toString():'')+'#calculator';
}
function fromQuery(){
  const u=new URLSearchParams(location.search);
  ['a','b'].forEach(x=>{const m=u.get(x);if(m&&DATA.managers[m]){ST[x].mgr=m;q('mgr-'+x).value=m}
    (u.get(x+'s')||'').split('~').filter(Boolean).forEach(k=>{const r=resolve(k);if(r)add(x,r)})});
}
function init(el){
  root=el;const raw=document.getElementById('calc-data');if(!raw)return;
  build(JSON.parse(raw.textContent));ST={a:{mgr:'',items:[]},b:{mgr:'',items:[]}};
  const mg=Object.keys(DATA.managers).sort((x,y)=>x.toLowerCase()<y.toLowerCase()?-1:1);
  const opts='<option value="">Anyone (no roster)</option>'+mg.map(m=>`<option value="${E(m)}">${E(m)}</option>`).join('');
  const side=x=>`<div class="cs" data-s="${x}"><h3>Side ${x.toUpperCase()}</h3>
<label class="cl">Team<select data-f="mgr" data-s="${x}" data-r="mgr-${x}">${opts}</select></label>
<div class="cq"><label class="vh2" for="q-${x}">Search any player or pick for side ${x.toUpperCase()}</label><input id="q-${x}" type="search" data-f="q" data-s="${x}" data-r="q-${x}" placeholder="Search any player or pick" autocomplete="off"><ul class="sug" data-r="sug-${x}" hidden></ul></div>
<p class="key cap">Sends</p><ul class="citems" data-r="items-${x}"></ul>
<details class="cown" data-r="own-${x}" open hidden><summary data-r="own-title-${x}"></summary><ul class="cownl" data-r="own-list-${x}"></ul></details></div>`;
  root.innerHTML=`<div class="ctool"><button type="button" class="btn o" data-act="swap">Swap sides</button><button type="button" class="btn o" data-act="reset">Reset</button><button type="button" class="btn o" data-act="copy">Copy link</button><span class="key" data-r="msg" aria-live="polite"></span></div>
<div class="csides">${side('a')}${side('b')}</div><section class="cres" data-r="res" aria-live="polite" aria-label="Result"></section>
<p class="key">Values are <a href="https://www.fantasycalc.com">FantasyCalc</a> dynasty trade values based on superflex, 12 teams, full PPR.</p>`;
  fromQuery();render();
  root.addEventListener('change',e=>{const f=e.target.closest&&e.target.closest('[data-f]');if(!f)return;const k=f.dataset.f;
    if(k==='mgr'){ST[f.dataset.s].mgr=f.value;render()}});
  root.addEventListener('input',e=>{const f=e.target.closest&&e.target.closest('[data-f="q"]');if(!f)return;const x=f.dataset.s,ul=q('sug-'+x),r=search(f.value,ST[x].mgr);
    ul.hidden=!r.length;ul.innerHTML=r.map(i=>itemRow(i,x,'add')).join('')});
  root.addEventListener('keydown',e=>{const f=e.target.closest&&e.target.closest('[data-f="q"]');if(!f||e.key!=='Enter')return;e.preventDefault();
    const x=f.dataset.s,r=search(f.value,ST[x].mgr);if(r.length){add(x,r[0].k);f.value='';q('sug-'+x).hidden=true;render()}});
  root.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('[data-act]');if(!b)return;const a=b.dataset.act,x=b.dataset.s;
    if(a==='add'){add(x,b.dataset.k);const f=q('q-'+x);if(f)f.value='';const u=q('sug-'+x);if(u)u.hidden=true;render()}
    else if(a==='rm'){ST[x].items=ST[x].items.filter(i=>i.k!==b.dataset.k);render()}
    else if(a==='swap'){ST={a:ST.b,b:ST.a};q('mgr-a').value=ST.a.mgr;q('mgr-b').value=ST.b.mgr;render()}
    else if(a==='reset'){ST={a:{mgr:'',items:[]},b:{mgr:'',items:[]}};q('mgr-a').value='';q('mgr-b').value='';render()}
    else if(a==='copy'){const l=link(),m=q('msg');const done=()=>{if(m)m.textContent='Link copied.'};
      if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(l).then(done,()=>{if(m)m.textContent=l});else if(m)m.textContent=l}});
}
if(typeof module!=='undefined')module.exports={build,ownList,sum,verdict,impact,ranksAfter,suggestions,search,mkItem,_set:s=>{ST=s},_init:init};
else{const el=document.getElementById('calc-app');if(el){init(el);
  window.DynCalc={data:()=>DATA,load:(a,b,as,bs)=>{ST={a:{mgr:a,items:[]},b:{mgr:b,items:[]}};as.forEach(k=>add('a',k));bs.forEach(k=>add('b',k));
    q('mgr-a').value=a;q('mgr-b').value=b;render();const t=document.getElementById('calculator');if(t&&t.scrollIntoView)t.scrollIntoView({behavior:'smooth'})}}}}
})();
