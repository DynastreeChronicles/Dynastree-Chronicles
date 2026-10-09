(()=>{const M=[[/champions/i,"champions"],[/all-time records/i,"records"],[/careers/i,"careers"],[/award shelf/i,"awards"],[/season by season/i,"timeline"],[/transaction|trade/i,"trades"],[/standings|hero|print/i,"standings"],[/leaderboard|power|game/i,"power"],[/drama|desk|bottom/i,"drama"],[/poll|rules/i,"poll"],[/bankroll|archive|waiver/i,"waivers"]];
const base=document.currentScript.src.replace(/js\/site\.js.*$/,"assets/");
document.querySelectorAll("h2.sec").forEach(h=>{if(h.id==="hero-zero")return;const m=M.find(x=>x[0].test(h.textContent));const i=new Image();i.src=base+"icon-"+(m?m[1]:"standings")+".webp";i.alt="";i.className="ic";i.onerror=()=>i.remove();h.prepend(i)});})();

(()=>{const bs=document.querySelectorAll('.sortbar .chip');if(!bs.length)return;
bs.forEach(btn=>btn.onclick=()=>{bs.forEach(c=>{const on=c===btn,el=document.getElementById('v-'+c.dataset.view);c.classList.toggle('on',on);if(el)el.hidden=!on;});});})();

(()=>{const base=document.currentScript.src.replace(/js\/site\.js.*$/,"assets/");
const D=[[/standings|leaderboard|power/i,"01"],[/hero|zero|issues|archive|vault/i,"02"],[/transaction|trade|wire/i,"03"],[/rules|scoring|poll|bankroll|ledger/i,"04"],[/drama|desk|bottom/i,"05"],[/game|draft|week/i,"06"]];
[...document.querySelectorAll("main h2.sec")].forEach((h,i)=>{if(!i)return;const m=D.find(x=>x[0].test(h.textContent));const im=new Image();im.src=base+"divider-"+(m?m[1]:"04")+".webp";im.alt="";im.className="divider";im.loading="lazy";im.onerror=()=>im.remove();h.before(im)})})();
