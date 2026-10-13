/* Synthetic decorative market board; no quotes, fetches, financial feed or controls. */
(()=>{'use strict';
const hero=document.querySelector('.rd-hero'),canvas=hero?.querySelector('.rd-canvas'),art=hero?.querySelector('.rd-art');
if(!hero||!canvas||!art||hero.querySelector('.md-market'))return;
const reduced=matchMedia('(prefers-reduced-motion: reduce)'),board=document.createElement('div');board.className='md-market';board.setAttribute('aria-hidden','true');board.dataset.marketData='illustrative';
const plane=document.createElement('div');plane.className='md-market-plane';const grid=document.createElement('div');grid.className='md-market-grid';plane.append(grid);
const columns=document.createElement('div');columns.className='md-market-columns';const cells=[];
let seed=7281;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
function figure(){return(24+random()*960).toFixed(2).padStart(6,'0');}
function variation(){const v=(random()-.45)*7;return(v>=0?'+':'')+v.toFixed(2);}
for(let c=0;c<4;c++){const column=document.createElement('div');column.className='md-market-column';column.style.setProperty('--md-offset',(c%2?-5:5)+'px');for(let row=0;row<10;row++){const cell=document.createElement('span');cell.className='md-market-cell';const value=document.createElement('span');value.textContent=figure();const change=document.createElement('em');change.textContent=variation();const arrow=document.createElement('i');arrow.textContent=(c+row)%3?'▴':'▾';cell.append(value,change,arrow);column.append(cell);cells.push({cell,value,change,arrow});}columns.append(column);}
plane.append(columns);const scan=document.createElement('div');scan.className='md-market-scan';plane.append(scan);board.append(plane);
const meta=document.createElement('div');meta.className='md-market-meta';const caption=document.createElement('span');caption.textContent='SIMULATED SEQUENCE';const sequence=document.createElement('span');sequence.textContent='SEQ 000';meta.append(caption,sequence);board.append(meta);
// Same stacking level, earlier paint order: the actual candlestick canvas stays above this board.
hero.insertBefore(board,canvas);
let visible=false,paused=Boolean(window.swarmMotionPaused)||document.documentElement.dataset.swarmMotion==='paused',running=false,destroyed=false,timer=0,ticks=0;board.dataset.marketTick='0';
const cleanup=[];const on=(target,event,fn,options)=>{target.addEventListener(event,fn,options);cleanup.push(()=>target.removeEventListener(event,fn,options));};
function position(){if(destroyed)return;const h=hero.getBoundingClientRect(),a=art.getBoundingClientRect();board.style.left=(a.left-h.left)+'px';board.style.top=(a.top-h.top)+'px';board.style.width=a.width+'px';board.style.height=a.height+'px';}
function tick(){if(!running||destroyed)return;ticks++;for(const {cell} of cells)cell.classList.remove('is-tick');for(let column=0;column<4;column++)for(let row=0;row<2;row++){const target=cells[column*10+(ticks*2+row+column)%10];target.value.textContent=figure();target.change.textContent=variation();target.arrow.textContent=target.change.textContent.startsWith('-')?'▾':'▴';target.cell.classList.add('is-tick');}sequence.textContent='SEQ '+String(ticks%1000).padStart(3,'0');board.dataset.marketTick=String(ticks);timer=setTimeout(tick,1000);}
function sync(){if(destroyed)return;const phase=canvas.dataset.phase,chart=phase==='chart',forming=phase==='forming-chart',show=(chart||forming)&&!reduced.matches;
 board.classList.toggle('is-chart',show&&chart);board.classList.toggle('is-forming',show&&forming);board.dataset.marketPhase=phase||'waiting';
 const next=show&&visible&&!document.hidden&&!paused&&canvas.dataset.motion!=='paused';board.classList.toggle('is-running',next);
 if(next===running)return;running=next;clearTimeout(timer);timer=0;if(running)timer=setTimeout(tick,1000);
}
const phases=new MutationObserver(sync);phases.observe(canvas,{attributes:true,attributeFilter:['data-phase','data-motion']});cleanup.push(()=>phases.disconnect());
const motion=new MutationObserver(()=>{paused=Boolean(window.swarmMotionPaused)||document.documentElement.dataset.swarmMotion==='paused';sync();});motion.observe(document.documentElement,{attributes:true,attributeFilter:['data-swarm-motion']});cleanup.push(()=>motion.disconnect());
if('ResizeObserver'in window){const sizes=new ResizeObserver(position);sizes.observe(hero);sizes.observe(art);cleanup.push(()=>sizes.disconnect());}on(window,'resize',position,{passive:true});
if('IntersectionObserver'in window){const viewport=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;sync();},{threshold:.08});viewport.observe(art);cleanup.push(()=>viewport.disconnect());}else visible=true;
on(window,'swarm:motion',event=>{paused=Boolean(event.detail?.paused);sync();});on(reduced,'change',sync);on(document,'visibilitychange',sync);
on(window,'pagehide',event=>{clearTimeout(timer);timer=0;running=false;board.classList.remove('is-running');if(!event.persisted){destroyed=true;cleanup.forEach(remove=>remove());board.remove();}});on(window,'pageshow',()=>{position();sync();});
document.fonts?.ready.then(()=>{position();sync();});position();sync();
})();
