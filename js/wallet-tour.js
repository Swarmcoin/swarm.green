/* Passive film of actual wallet UI captures. No wallet, form or payment API. */
(()=>{'use strict';document.querySelectorAll('[data-wallet-tour]').forEach(root=>{
 const reduced=matchMedia('(prefers-reduced-motion: reduce)'),frames=[...root.querySelectorAll('[data-wt-scene]')];
 if(!frames.length)return;
 const holds=[4500,4500,5500,4500];let index=0,timer=0,visible=false,paused=Boolean(window.swarmMotionPaused)||document.documentElement.dataset.swarmMotion==='paused',destroyed=false;
 const cleanup=[],on=(target,event,fn)=>{target.addEventListener(event,fn);cleanup.push(()=>target.removeEventListener(event,fn));};
 function show(next){index=next;frames.forEach((frame,i)=>frame.classList.toggle('is-active',i===index));root.dataset.wtPanel=frames[index].dataset.wtScene;}
 function active(){return visible&&!paused&&!reduced.matches&&!document.hidden&&!destroyed;}
 function sync(){clearTimeout(timer);root.dataset.wtPlaying=String(active());if(!active())return;timer=setTimeout(()=>{const next=(index+1)%frames.length;if(frames[next].complete&&frames[next].naturalWidth)show(next);sync();},holds[index]||4500);}
 const io='IntersectionObserver'in window?new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;sync();},{threshold:.25}):null;
 if(io){io.observe(root);cleanup.push(()=>io.disconnect());}else visible=true;
 on(window,'swarm:motion',event=>{paused=Boolean(event.detail?.paused);sync();});
 on(reduced,'change',()=>{if(reduced.matches)show(0);sync();});
 on(document,'visibilitychange',sync);
 on(window,'pagehide',event=>{clearTimeout(timer);if(!event.persisted){destroyed=true;cleanup.forEach(fn=>fn());}});
 on(window,'pageshow',sync);show(0);sync();
});})();
