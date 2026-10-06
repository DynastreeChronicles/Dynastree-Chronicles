(()=>{const M=[[/champions/i,"champions"],[/all-time records/i,"records"],[/careers/i,"careers"],[/award shelf/i,"awards"],[/season by season/i,"timeline"],[/transaction|trade/i,"trades"],[/standings|hero|print/i,"standings"],[/leaderboard|power|game/i,"power"],[/drama|desk|bottom/i,"drama"],[/poll|rules/i,"poll"],[/bankroll|archive|waiver/i,"waivers"]];
const base=document.currentScript.src.replace(/js\/site\.js.*$/,"assets/");
document.querySelectorAll("h2.sec").forEach(h=>{if(h.id==="hero-zero")return;const m=M.find(x=>x[0].test(h.textContent));const i=new Image();i.src=base+"icon-"+(m?m[1]:"standings")+".webp";i.alt="";i.className="ic";i.onerror=()=>i.remove();h.prepend(i)});})();

(()=>{const bs=document.querySelectorAll('.sortbar .chip');if(!bs.length)return;
bs.forEach(btn=>btn.onclick=()=>{const d=btn.dataset.view==='draft';
const r=document.getElementById('v-rank'),f=document.getElementById('v-draft');if(r)r.hidden=d;if(f)f.hidden=!d;
bs.forEach(c=>c.classList.toggle('on',c===btn));});})();
