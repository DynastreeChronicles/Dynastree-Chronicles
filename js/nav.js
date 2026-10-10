(()=>{const b=document.querySelector('.ddb'),m=document.getElementById('vault');if(!b||!m)return;
const close=()=>{m.hidden=true;b.setAttribute('aria-expanded','false')};
b.onclick=e=>{e.stopPropagation();if(!m.hidden)return close();m.hidden=false;b.setAttribute('aria-expanded','true');const r=b.getBoundingClientRect();m.style.left=Math.max(8,Math.min(r.left,innerWidth-m.offsetWidth-8))+'px'};
document.addEventListener('click',e=>{if(!m.contains(e.target))close()});document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
b.closest('.wrap').addEventListener('scroll',close);addEventListener('resize',close);})();
(()=>{document.querySelectorAll('.showmore').forEach(b=>b.onclick=()=>{const t=document.getElementById(b.dataset.t);if(!t)return;const open=t.hidden;t.hidden=!open;b.setAttribute('aria-expanded',open);b.textContent=open?b.dataset.less:b.dataset.more;});
const reveal=()=>{const el=location.hash&&document.getElementById(decodeURIComponent(location.hash.slice(1)));if(!el)return;for(let p=el;p;p=p.parentElement){if(p.tagName==='DETAILS')p.open=true;}el.scrollIntoView();};
addEventListener('hashchange',reveal);if(location.hash)reveal();})();
