/* Warm presentation motion; content stays readable without JavaScript. */
(() => {
  const reduced=matchMedia('(prefers-reduced-motion: reduce)');
  let paused=reduced.matches||Boolean(window.swarmMotionPaused);
  let hidden=document.hidden;
  const typers=[];
  for(const element of document.querySelectorAll('[data-type-phrases]')){
    let phrases;try{phrases=JSON.parse(element.dataset.typePhrases);}catch{continue;}
    if(!Array.isArray(phrases)||!phrases.length)continue;
    typers.push({element,phrases,index:0,chars:phrases[0].length,mode:'hold',elapsed:0});
  }
  let last=0,frame;
  function reset(){for(const t of typers){t.index=0;t.chars=t.phrases[0].length;t.mode='hold';t.elapsed=0;t.element.textContent=t.phrases[0];}}
  function run(now){
    const dt=Math.min(now-last,100);last=now;
    if(!paused&&!hidden){
      for(const t of typers){
        t.elapsed+=dt;
        const delay=t.mode==='hold'?4400:t.mode==='erase'?45:92;
        if(t.elapsed<delay)continue;
        t.elapsed=0;
        if(t.mode==='hold')t.mode='erase';
        else if(t.mode==='erase'){
          t.chars=Math.max(0,t.chars-1);
          if(!t.chars){t.index=(t.index+1)%t.phrases.length;t.mode='type';}
        }else{
          t.chars=Math.min(t.phrases[t.index].length,t.chars+1);
          if(t.chars===t.phrases[t.index].length)t.mode='hold';
        }
        t.element.textContent=t.phrases[t.index].slice(0,t.chars);
      }
    }
    if(!paused&&!hidden&&typers.length)frame=requestAnimationFrame(run);
  }
  function schedule(){cancelAnimationFrame(frame);last=performance.now();if(!paused&&!hidden&&typers.length)frame=requestAnimationFrame(run);}
  window.addEventListener('swarm:motion',event=>{paused=Boolean(event.detail?.paused)||reduced.matches;schedule();});
  reduced.addEventListener('change',()=>{paused=reduced.matches||Boolean(window.swarmMotionPaused);if(reduced.matches)reset();schedule();});
  document.addEventListener('visibilitychange',()=>{hidden=document.hidden;schedule();});
  schedule();
  const observer=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting){entry.target.classList.add('is-visible');observer.unobserve(entry.target);}}},{threshold:.22});
  document.querySelectorAll('.rd-facts,.rd-step').forEach(e=>observer.observe(e));
  for(const brand of document.querySelectorAll('.rd-header .rd-brand')){
    brand.addEventListener('pointermove',event=>{if(paused||reduced.matches)return;const r=brand.getBoundingClientRect();brand.style.setProperty('--brand-x',`${((event.clientY-r.top)/r.height-.5)*-10}deg`);brand.style.setProperty('--brand-y',`${((event.clientX-r.left)/r.width-.5)*18}deg`);});
    brand.addEventListener('pointerleave',()=>{brand.style.setProperty('--brand-x','0deg');brand.style.setProperty('--brand-y','0deg');});
  }
})();
