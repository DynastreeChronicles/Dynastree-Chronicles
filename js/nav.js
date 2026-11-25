(()=>{const bs=[...document.querySelectorAll('.ddb')];if(!bs.length)return;
const menu=b=>document.getElementById(b.getAttribute('aria-controls'));
const closeAll=()=>bs.forEach(b=>{const m=menu(b);if(m)m.hidden=true;b.setAttribute('aria-expanded','false')});
bs.forEach(b=>{const m=menu(b);if(!m)return;
b.onclick=e=>{e.stopPropagation();const was=!m.hidden;closeAll();if(was)return;m.hidden=false;b.setAttribute('aria-expanded','true');const r=b.getBoundingClientRect();m.style.left=Math.max(8,Math.min(r.left,innerWidth-m.offsetWidth-8))+'px'};
b.closest('.wrap').addEventListener('scroll',closeAll);});
document.addEventListener('click',e=>{if(!e.target.closest('.ddm'))closeAll()});document.addEventListener('keydown',e=>{if(e.key==='Escape')closeAll()});addEventListener('resize',closeAll);})();
(()=>{document.querySelectorAll('.showmore').forEach(b=>b.onclick=()=>{const t=document.getElementById(b.dataset.t);if(!t)return;const open=t.hidden;t.hidden=!open;b.setAttribute('aria-expanded',open);b.textContent=open?b.dataset.less:b.dataset.more;});
const reveal=()=>{const el=location.hash&&document.getElementById(decodeURIComponent(location.hash.slice(1)));if(!el)return;for(let p=el;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true;}el.scrollIntoView();};
addEventListener('hashchange',reveal);if(location.hash)reveal();})();

(()=>{document.querySelectorAll('table.sortable').forEach(tb=>{const first=tb.tBodies[0],more=tb.tBodies[1],N=+tb.dataset.n||6,btns=tb.querySelectorAll('.sb');
const dirs={pos:1,v:-1,t:-1};let cur={k:'v',d:-1};
const apply=()=>{const rows=[...first.rows,...(more?more.rows:[])];const k=cur.k,d=cur.d;rows.sort((a,b)=>{const x=+a.dataset[k],y=+b.dataset[k];return (x-y)*d||(+b.dataset.v-+a.dataset.v)});
rows.forEach((r,i)=>(i<N||!more?first:more).appendChild(r));btns.forEach(b=>{const th=b.parentElement,on=b.dataset.k===k;th.classList.toggle('sorted',on);th.classList.toggle('asc',on&&d>0);th.classList.toggle('desc',on&&d<0);});};
btns.forEach(b=>b.onclick=()=>{const k=b.dataset.k;cur=cur.k===k?{k,d:-cur.d}:{k,d:dirs[k]};apply();});});})();

/* Manager-name links: on every page, any manager handle in the text becomes a link to that manager's page (class "ml", the same look as the
   standings). Works on content drawn later by other scripts (issue wire, cards, receipts, calculator) through a MutationObserver. It skips
   anything already inside a link, button, form control, heading 1, nav, header, footer, ticker or summary, and a manager's own name on their own page.
   Handles come from data/managers.json (current handles plus former_names, which point to the current page), with the 12 current handles built in as a fallback. */
(()=>{const src=document.currentScript&&document.currentScript.src;if(!src)return;
const root=new URL('../',src).href,names=new Map();
const add=(n,h)=>{if(typeof n==='string'&&n.length>2)names.set(n.toLowerCase(),h)};
['Zygon','Hades9mm','C33DeezNutzz','Johnny4Skins','YesChef23','Darkspaces','fumbduckdumbfuck','CMac91','Snipe58','StealingGas','Sarge71','Painty69'].forEach(h=>add(h,h));
const SKIP='a,button,select,option,textarea,input,script,style,noscript,h1,nav,header,footer,summary,label,svg,canvas,pre,code,title,.ddm,.tick,[data-nolink],[role=button],[role=tab],[contenteditable]';
const own=((location.pathname.match(/\/managers\/([^/]+)\//)||[])[1]||'').toLowerCase();
let rx=null;
const build=()=>{const k=[...names.keys()].sort((a,b)=>b.length-a.length).map(s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'));rx=new RegExp('(^|[^A-Za-z0-9_])('+k.join('|')+')(?![A-Za-z0-9_])','gi')};
const frag=text=>{rx.lastIndex=0;let m,last=0,out=null;
 while((m=rx.exec(text))){const h=names.get(m[2].toLowerCase());if(h.toLowerCase()===own)continue;
  out=out||document.createDocumentFragment();const start=m.index+m[1].length;
  out.append(text.slice(last,start));const a=document.createElement('a');a.className='ml';a.href=root+'managers/'+h.toLowerCase()+'/';a.textContent=m[2];out.append(a);last=start+m[2].length;}
 if(!out)return null;out.append(text.slice(last));return out};
const scan=node=>{if(!node||!node.isConnected)return;
 if(node.nodeType===3){const p=node.parentElement;if(p&&!p.closest(SKIP)){const f=frag(node.nodeValue);if(f)node.replaceWith(f)}return}
 if(node.nodeType!==1||node.closest(SKIP))return;
 const w=document.createTreeWalker(node,NodeFilter.SHOW_TEXT,{acceptNode:t=>t.parentElement&&!t.parentElement.closest(SKIP)&&t.nodeValue.trim()?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT}),list=[];
 while(w.nextNode())list.push(w.currentNode);
 list.forEach(t=>{const f=frag(t.nodeValue);if(f)t.replaceWith(f)})};
let queue=[],busy=false;
const obs=new MutationObserver(rs=>{rs.forEach(r=>r.addedNodes.forEach(n=>queue.push(n)));if(busy||!queue.length)return;busy=true;
 requestAnimationFrame(()=>{obs.disconnect();const q=queue;queue=[];q.forEach(scan);busy=false;obs.observe(document.body,{childList:true,subtree:true})})});
const run=()=>{build();scan(document.body);obs.observe(document.body,{childList:true,subtree:true})};
const start=()=>{run();
 fetch(root+'data/managers.json').then(r=>r.ok?r.json():null).then(j=>{if(!j)return;
  const list=Array.isArray(j)?j:Array.isArray(j.managers)?j.managers:Object.entries(j).map(([k,v])=>v&&typeof v==='object'?{handle:v.handle||k,former_names:v.former_names}:{handle:k});
  list.forEach(m=>{const h=m&&(m.handle||m.name);if(!h)return;add(h,h);(m.former_names||[]).forEach(o=>add(typeof o==='string'?o:o&&o.handle,h))});
  obs.disconnect();build();scan(document.body);obs.observe(document.body,{childList:true,subtree:true})}).catch(()=>{})};
document.readyState==='loading'?document.addEventListener('DOMContentLoaded',start):start();})();
