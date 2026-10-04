(()=>{const M=[[/transaction|trade/i,"trades"],[/standings|hero|print/i,"standings"],[/leaderboard|power|game/i,"power"],[/drama|desk|bottom/i,"drama"],[/poll|rules/i,"poll"],[/bankroll|archive|waiver/i,"waivers"]];
const base=document.currentScript.src.replace(/js\/site\.js.*$/,"assets/");
document.querySelectorAll("h2.sec").forEach(h=>{const m=M.find(x=>x[0].test(h.textContent));const i=new Image();i.src=base+"icon-"+(m?m[1]:"standings")+".webp";i.alt="";i.className="ic";h.prepend(i)});})();
