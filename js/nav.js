(()=>{const b=document.querySelector('.ddb'),m=document.getElementById('vault');if(!b||!m)return;
const close=()=>{m.hidden=true;b.setAttribute('aria-expanded','false')};
b.onclick=e=>{e.stopPropagation();if(!m.hidden)return close();m.hidden=false;b.setAttribute('aria-expanded','true');const r=b.getBoundingClientRect();m.style.left=Math.max(8,Math.min(r.left,innerWidth-m.offsetWidth-8))+'px'};
document.addEventListener('click',e=>{if(!m.contains(e.target))close()});document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
b.closest('.wrap').addEventListener('scroll',close);addEventListener('resize',close);})();
(()=>{document.querySelectorAll('.showmore').forEach(b=>b.onclick=()=>{const t=document.getElementById(b.dataset.t);if(!t)return;const open=t.hidden;t.hidden=!open;b.setAttribute('aria-expanded',open);b.textContent=open?b.dataset.less:b.dataset.more;});
const reveal=()=>{const el=location.hash&&document.getElementById(decodeURIComponent(location.hash.slice(1)));if(!el)return;for(let p=el;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true;}el.scrollIntoView();};
addEventListener('hashchange',reveal);if(location.hash)reveal();})();

(()=>{document.querySelectorAll('table.sortable').forEach(tb=>{const first=tb.tBodies[0],more=tb.tBodies[1],N=+tb.dataset.n||6,btns=tb.querySelectorAll('.sb');
const dirs={pos:1,v:-1,t:-1};let cur={k:'v',d:-1};
const apply=()=>{const rows=[...first.rows,...(more?more.rows:[])];const k=cur.k,d=cur.d;rows.sort((a,b)=>{const x=+a.dataset[k],y=+b.dataset[k];return (x-y)*d||(+b.dataset.v-+a.dataset.v)});
rows.forEach((r,i)=>(i<N||!more?first:more).appendChild(r));btns.forEach(b=>{const th=b.parentElement,on=b.dataset.k===k;th.classList.toggle('sorted',on);th.classList.toggle('asc',on&&d>0);th.classList.toggle('desc',on&&d<0);});};
btns.forEach(b=>b.onclick=()=>{const k=b.dataset.k;cur=cur.k===k?{k,d:-cur.d}:{k,d:dirs[k]};apply();});});})();
