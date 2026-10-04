(()=>{const M=[[/trade machine|transaction|trades/i,"trades"],[/standings/i,"standings"],[/leaderboard|power/i,"power"],[/drama/i,"drama"],[/poll/i,"poll"],[/waiver/i,"waivers"]];
const base=document.currentScript.src.replace(/js\/site\.js.*$/,"assets/");
document.querySelectorAll("h2.sec").forEach(h=>{const m=M.find(x=>x[0].test(h.textContent));if(m){const i=new Image();i.src=base+"icon-"+m[1]+".png";i.alt="";i.className="ic";h.prepend(i)}});})();
