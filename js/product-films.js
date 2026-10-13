/* Passive product screen films; no inputs, messages, wallet calls or external requests. */
(()=>{'use strict';document.querySelectorAll('[data-product-film]').forEach(root=>{
const type=root.dataset.productFilm,reduced=matchMedia('(prefers-reduced-motion: reduce)');let visible=false,paused=Boolean(window.swarmMotionPaused),destroyed=false,timer=0,time=0,last=0;const remove=[];const on=(t,e,f)=>{t.addEventListener(e,f);remove.push(()=>t.removeEventListener(e,f));};
const query='Explore the SWARM network';const field=root.querySelector('[data-pm-search]');
function draw(){if(type==='browser'){const cycle=time%16000;let scene=cycle<3500?'overview':cycle<8000?'search':cycle<12000?'wallet':'features';if(reduced.matches)scene='overview';root.dataset.filmScene=scene;if(field)field.textContent=scene==='search'?query.slice(0,Math.max(0,Math.floor((cycle-3500)/110))):'';}else{const cycle=time%12000;const count=reduced.matches?3:cycle<3000?1:cycle<6000?2:3;root.querySelectorAll('.pm-bubble').forEach((bubble,i)=>bubble.classList.toggle('pm-bubble-waiting',i>=count));root.dataset.filmScene='message-'+count;}}
function active(){return visible&&!paused&&!reduced.matches&&!document.hidden&&!destroyed;}
function tick(){if(!active())return;const now=performance.now();time+=Math.min(250,now-last);last=now;draw();timer=setTimeout(tick,110);}
function sync(){clearTimeout(timer);root.dataset.filmPlaying=String(active());if(active()){last=performance.now();timer=setTimeout(tick,110);}}
const io='IntersectionObserver'in window?new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;sync();},{threshold:.25}):null;if(io){io.observe(root.querySelector('.pm-device-stage')||root);remove.push(()=>io.disconnect());}else visible=true;
on(window,'swarm:motion',event=>{paused=Boolean(event.detail?.paused);sync();});on(reduced,'change',()=>{if(reduced.matches)time=0;draw();sync();});on(document,'visibilitychange',sync);on(window,'pagehide',event=>{clearTimeout(timer);if(!event.persisted){destroyed=true;remove.forEach(fn=>fn());}});on(window,'pageshow',sync);draw();sync();
});})();
