/* Site-wide SWARM motion. Decorations never intercept input or represent market data. */
(() => {
  'use strict';
  if (!document.body.classList.contains('redesign') || document.querySelector('.mv-motion-tools')) return;
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  let manualPause = false;
  try { manualPause = sessionStorage.getItem('swarm-motion-paused') === 'true'; } catch (_) { /* Storage is optional. */ }
  let paused = manualPause || reduce.matches;
  const motionRefresh = [];
  const tools = document.createElement('div');
  tools.className = 'mv-motion-tools rd-wrap';
  const toggle = document.createElement('button');
  toggle.type = 'button'; toggle.className = 'mv-motion-toggle';
  tools.append(toggle);
  const main = document.querySelector('main');
  (main || document.querySelector('.rd-footer'))?.before(tools);
  let refreshGPU = () => {};
  const sync = () => {
    paused = manualPause || reduce.matches;
    root.dataset.swarmMotion = paused ? 'paused' : 'running';
    window.swarmMotionPaused = paused;
    toggle.textContent = reduce.matches ? 'Motion off · system preference' : paused ? 'Resume all motion' : 'Pause all motion';
    toggle.setAttribute('aria-pressed', String(paused));
    toggle.setAttribute('aria-label', reduce.matches ? 'Motion disabled by your reduced motion preference' : toggle.textContent);
    toggle.disabled = reduce.matches;
    window.dispatchEvent(new CustomEvent('swarm:motion', {detail: {paused}}));
    refreshGPU();
    motionRefresh.forEach(refresh => refresh());
  };
  toggle.addEventListener('click', () => {
    manualPause = !manualPause;
    try { sessionStorage.setItem('swarm-motion-paused', String(manualPause)); } catch (_) { /* Optional persistence. */ }
    sync();
  });
  let lastReduced = reduce.matches;
  const syncPreference = () => { lastReduced=reduce.matches; sync(); if (!reduce.matches) startField(); };
  reduce.addEventListener('change', syncPreference);
  // Some embedded browsers defer media-query events. This check does no rendering.
  const preferenceTimer = setInterval(() => {if(!document.hidden && reduce.matches!==lastReduced) syncPreference();}, 1000);
  addEventListener('pagehide', event => {if(!event.persisted) clearInterval(preferenceTimer);});
  sync();

  const svgNS = 'http://www.w3.org/2000/svg';
  const decorateHex = (el, index) => {
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', '0 0 100 110');
    svg.setAttribute('aria-hidden', 'true'); svg.classList.add('mv-hex-current');
    const path = document.createElementNS(svgNS, 'path');
    path.setAttribute('d', 'M50 3 94 28 94 82 50 107 6 82 6 28Z');
    svg.append(path); el.append(svg); el.style.setProperty('--mv-delay', `${index * -.8}s`);
  };
  document.querySelectorAll('.rd-step-hex,.ob-hex,.rd-roadmap-next .rd-roadmap-marker,.roadmap-stage--scheduled .roadmap-hex').forEach(decorateHex);

  const candles=[];
  document.querySelectorAll('.rd-trade-card,.tv-pool').forEach((card,index)=>{
    const chart=document.createElement('figure');chart.className='mv-chart mv-candle-chart';
    const svg=document.createElementNS(svgNS,'svg');svg.setAttribute('viewBox','0 0 320 84');svg.setAttribute('preserveAspectRatio','none');svg.setAttribute('aria-hidden','true');
    const grid=document.createElementNS(svgNS,'path');grid.setAttribute('d','M0 18H320M0 42H320M0 66H320');grid.classList.add('mv-chart-grid');svg.append(grid);
    const bars=[],seed=new Uint32Array(1);try{crypto.getRandomValues(seed);}catch(_){seed[0]=(Math.random()*4294967296)>>>0;}let randomState=seed[0],regimeLeft=0,drift=0,volatility=2;
    const random=()=>{randomState=(randomState+0x6D2B79F5)>>>0;let t=randomState;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296;};
    const normal=()=>Math.sqrt(-2*Math.log(Math.max(.00001,random())))*Math.cos(random()*Math.PI*2);
    const bound=v=>Math.max(35,Math.min(180,v));
    const makeBar=open=>{if(--regimeLeft<=0){regimeLeft=3+Math.floor(random()*7);drift=(random()-.43)*2.2;volatility=1.5+random()*2.8;}const pull=(105-open)*.025,target=bound(open+drift+pull+normal()*volatility),path=[open];for(let j=1;j<12;j++){const p=j/12;path.push(bound(open+(target-open)*p+normal()*volatility*1.2*Math.sqrt(p*(1-p))));}path.push(target);return{open,close:target,target,path,high:Math.max(open,target)+random()*volatility,low:Math.min(open,target)-random()*volatility};};
    const makeLive=open=>{const bar=makeBar(open);bar.close=open;bar.high=open;bar.low=open;return bar;};
    let previous=85+random()*35;
    const parts=[];
    for(let i=0;i<23;i++){
      const group=document.createElementNS(svgNS,'g');group.classList.add('mv-candle');group.style.setProperty('--bar-delay',`${i*30}ms`);
      const wick=document.createElementNS(svgNS,'line'),body=document.createElementNS(svgNS,'rect');
      body.setAttribute('width','8');body.setAttribute('rx','.5');group.append(wick,body);svg.append(group);
      parts.push({group,wick,body});const bar=makeBar(previous);bars.push(bar);previous=bar.close;
      if(i===22)group.classList.add('mv-candle-live');
    }
    const guide=document.createElementNS(svgNS,'line');guide.classList.add('mv-candle-price');svg.append(guide);
    const marker=document.createElementNS(svgNS,'circle');marker.classList.add('mv-candle-marker');marker.setAttribute('r','2.4');svg.append(marker);
    const c={card,chart,parts,bars,makeLive,time:0,step:0,guide,marker,last:0};
    const render=()=>{const progress=c.time%1,live=bars[22],target=live.target,k=Math.min(11,Math.floor(progress*12)),f=progress*12-k,ease=f*f*(3-2*f);live.close=live.path[k]+(live.path[k+1]-live.path[k])*ease;live.high=Math.max(live.high,live.close);live.low=Math.min(live.low,live.close);const low=Math.min(...bars.map(b=>b.low),...live.path)-1.4,high=Math.max(...bars.map(b=>b.high),...live.path)+1.5,scale=v=>76-(v-low)/(high-low)*68;
      parts.forEach((p,i)=>{const bar=bars[i],x=8+i*14-progress*14,open=scale(bar.open),close=scale(bar.close);p.body.setAttribute('x',x-4);p.body.setAttribute('y',Math.min(open,close));p.body.setAttribute('height',Math.max(1.5,Math.abs(close-open)));p.wick.setAttribute('x1',x);p.wick.setAttribute('x2',x);p.wick.setAttribute('y1',scale(bar.high));p.wick.setAttribute('y2',scale(bar.low));p.group.classList.toggle('mv-candle-down',bar.close<bar.open);});
      const x=316-progress*14,y=scale(live.close);guide.setAttribute('x1',x+5);guide.setAttribute('x2','320');guide.setAttribute('y1',y);guide.setAttribute('y2',y);marker.setAttribute('cx',x);marker.setAttribute('cy',y);chart.dataset.candleStep=String(c.step);chart.dataset.candlePrice=live.close.toFixed(3);chart.dataset.candleProgress=progress.toFixed(3);c.frameData=bars.map((bar,i)=>({x:8+i*14-progress*14,open:scale(bar.open),close:scale(bar.close),high:scale(bar.high),low:scale(bar.low),down:bar.close<bar.open}));c.gpu?.();
    };
    c.render=render;bars[22]=makeLive(bars[21].close);render();
    const caption=document.createElement('figcaption');caption.textContent='Illustrative candles · not market data';chart.append(svg,caption);card.querySelector('.rd-textlink,.rd-button')?.before(chart);
    candles.push(c);
  });
  const candleTimer=setInterval(()=>{const now=performance.now();candles.forEach(c=>{if(paused||reduce.matches||document.hidden||!c.card.classList.contains('mv-inview')){c.last=0;c.chart.dataset.candleMotion='static';return;}if(!c.gpuLoading){c.gpuLoading=true;installCandleGPU(c);}c.chart.dataset.candleMotion='running';c.time+=c.last?Math.min((now-c.last)/1000,.1):0;c.last=now;const step=Math.floor(c.time);if(step!==c.step){const settled=c.bars[22];settled.close=settled.target;settled.high=Math.max(settled.high,settled.close);settled.low=Math.min(settled.low,settled.close);c.bars.shift();c.bars.push(c.makeLive(settled.close));c.step=step;}c.render();});},50);
  addEventListener('pagehide',e=>{if(!e.persisted)clearInterval(candleTimer);});
  async function installCandleGPU(c){
    let renderer;
    try{
      const THREE=await import('./vendor/three.module.min.js');if(reduce.matches){c.gpuLoading=false;return;}
      const canvas=document.createElement('canvas');canvas.className='mv-candle-canvas';canvas.setAttribute('aria-hidden','true');
      renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:false,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.25));renderer.setClearColor(0,0);
      const scene=new THREE.Scene(),camera=new THREE.OrthographicCamera(0,320,84,0,.1,100);camera.position.z=30;
      scene.add(new THREE.AmbientLight(0xffe2b7,1.7));const light=new THREE.DirectionalLight(0xfff0cb,3);light.position.set(-60,100,80);scene.add(light);
      const geometry=new THREE.BoxGeometry(1,1,1),material=new THREE.MeshStandardMaterial({roughness:.55,metalness:.2});
      const bodies=new THREE.InstancedMesh(geometry,material,23),wicks=new THREE.InstancedMesh(geometry,material,23);scene.add(bodies,wicks);
      const dot=new THREE.Object3D(),color=new THREE.Color();let lost=false,disposed=false;
      const resize=()=>{const r=c.chart.querySelector('svg').getBoundingClientRect();renderer.setSize(Math.max(1,r.width),Math.max(1,r.height),false);};
      c.gpu=()=>{if(lost||disposed||reduce.matches)return;c.frameData.forEach((bar,i)=>{dot.position.set(bar.x,84-(bar.open+bar.close)/2,1.4);dot.rotation.set(.07,-.27,0);dot.scale.set(8,Math.max(1.5,Math.abs(bar.open-bar.close)),3);dot.updateMatrix();bodies.setMatrixAt(i,dot.matrix);color.setHex(bar.down?0xa95419:i===22?0xffca69:0xf4a72d);bodies.setColorAt(i,color);dot.position.set(bar.x,84-(bar.high+bar.low)/2,0);dot.rotation.set(0,0,0);dot.scale.set(1.1,Math.max(2,bar.low-bar.high),1.1);dot.updateMatrix();wicks.setMatrixAt(i,dot.matrix);wicks.setColorAt(i,color);});bodies.instanceMatrix.needsUpdate=true;wicks.instanceMatrix.needsUpdate=true;bodies.instanceColor.needsUpdate=true;wicks.instanceColor.needsUpdate=true;renderer.render(scene,camera);c.chart.classList.add('mv-candle-gpu-ready');c.chart.dataset.candleRenderer='three.js voxel OHLC';};
      canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();lost=true;c.chart.classList.remove('mv-candle-gpu-ready');c.chart.dataset.candleRenderer='svg fallback';});canvas.addEventListener('webglcontextrestored',()=>{lost=false;resize();c.gpu();});
      c.chart.append(canvas);const resizeObserver=new ResizeObserver(resize);resizeObserver.observe(c.chart);
      motionRefresh.push(()=>{canvas.hidden=reduce.matches;c.chart.classList.toggle('mv-candle-gpu-ready',!reduce.matches&&!lost);});
      addEventListener('pagehide',e=>{if(!e.persisted){disposed=true;resizeObserver.disconnect();renderer.dispose();geometry.dispose();material.dispose();}});
      resize();c.gpu();
    }catch(_){renderer?.dispose();c.chart.dataset.candleRenderer='svg fallback';}
  }
  document.querySelectorAll('.rd-steps,.ob-steps,.rd-roadmap-list,.roadmap-trail').forEach(connectNodes);
  document.querySelectorAll('.rd-fuel-art').forEach(art => {
    const embers = document.createElement('div'); embers.className = 'mv-fuel-embers'; embers.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < 14; i++) {
      const ember = document.createElement('i'); ember.style.setProperty('--x', `${8 + i * 6.4}%`);
      ember.style.setProperty('--d', `${-i * .61}s`); ember.style.setProperty('--s', `${4 + i % 4}s`); embers.append(ember);
    }
    art.prepend(embers);
    installFire(art);
  });
  const observed = document.querySelectorAll('.rd-step,.ob-step,.rd-trade-card,.tv-pool,.rd-fuel-art,.rd-roadmap-next,.roadmap-stage--scheduled');
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => entries.forEach(entry => entry.target.classList.toggle('mv-inview', entry.isIntersecting)), {rootMargin: '50px'});
    observed.forEach(el => observer.observe(el));
  } else observed.forEach(el => el.classList.add('mv-inview'));
  const visibility = () => { root.classList.toggle('mv-page-hidden', document.hidden); refreshGPU(); motionRefresh.forEach(refresh => refresh()); };
  document.addEventListener('visibilitychange', visibility);
  visibility();

  function connectNodes(group){
    const road=group.matches('.rd-roadmap-list,.roadmap-trail');
    const nodes=[...group.querySelectorAll(road?'.rd-roadmap-marker,.roadmap-stage>.roadmap-hex':'.rd-step-hex,.ob-hex')];
    if(nodes.length<2)return;
    group.classList.add('mv-connected');
    const svg=document.createElementNS(svgNS,'svg');svg.classList.add('mv-connector');svg.setAttribute('aria-hidden','true');
    const track=document.createElementNS(svgNS,'path'),charge=document.createElementNS(svgNS,'path');track.classList.add('mv-connector-track');charge.classList.add(road?'mv-road-draw':'mv-connector-energy');svg.append(track,charge);
    const orbs=[];for(let i=0;i<(road?1:3);i++){const dot=document.createElementNS(svgNS,'circle');dot.setAttribute('r',i===0?'3.5':'2');dot.classList.add('mv-charge');dot.style.opacity=String(1-i*.28);svg.append(dot);orbs.push(dot);}
    group.prepend(svg);let length=0,visible=false,frame=0,last=0,time=0;
    const layout=()=>{const box=group.getBoundingClientRect();svg.setAttribute('viewBox',`0 0 ${box.width} ${box.height}`);svg.setAttribute('width',box.width);svg.setAttribute('height',box.height);const pts=nodes.map(n=>{const r=n.getBoundingClientRect();return{x:r.x-box.x+r.width/2,y:r.y-box.y+r.height/2};});let d=`M${pts[0].x},${pts[0].y}`;
      for(let i=1;i<pts.length;i++){const a=pts[i-1],b=pts[i];if(Math.abs(a.y-b.y)<45){const dx=(b.x-a.x)*.38;d+=` C${a.x+dx},${a.y-22} ${b.x-dx},${b.y+22} ${b.x},${b.y}`;}else{const mid=(a.y+b.y)/2;d+=` C${a.x},${mid} ${b.x},${mid} ${b.x},${b.y}`;}}
      track.setAttribute('d',d);charge.setAttribute('d',d);length=track.getTotalLength();if(road){charge.style.strokeDasharray=String(length);drawRoad();}else charge.style.strokeDasharray=`${Math.max(55,length*.18)} ${length}`;
    };
    const drawRoad=()=>{if(!road||!length)return;const r=group.getBoundingClientRect();const fraction=reduce.matches?1:Math.max(0,Math.min(1,(innerHeight*.77-r.top)/Math.max(1,r.height*.83)));charge.style.strokeDashoffset=String(length*(1-fraction));const p=track.getPointAtLength(length*fraction);orbs[0].setAttribute('cx',p.x);orbs[0].setAttribute('cy',p.y);nodes.forEach(n=>n.classList.toggle('mv-node-seen',n.getBoundingClientRect().top<innerHeight*.78));};
    const run=()=>visible&&!paused&&!reduce.matches&&!document.hidden;
    const tick=now=>{frame=0;if(!run()){last=0;return;}frame=requestAnimationFrame(tick);if(last&&now-last<32)return;time+=last?Math.min((now-last)/1000,.08):0;last=now;if(road){drawRoad();return;}const progress=(time/7)%1;charge.style.strokeDashoffset=String(-progress*(length+Math.max(55,length*.18)));orbs.forEach((dot,i)=>{const point=track.getPointAtLength(((progress-i*.015+1)%1)*length);dot.setAttribute('cx',point.x);dot.setAttribute('cy',point.y);});nodes.forEach((node,i)=>node.classList.toggle('mv-node-charge',Math.abs(progress-i/(nodes.length-1))<.09));};
    const update=()=>{if(run()){orbs.forEach((dot,i)=>dot.style.opacity=String(1-i*.28));if(!frame)frame=requestAnimationFrame(tick);}else{cancelAnimationFrame(frame);frame=0;last=0;if(reduce.matches){charge.style.strokeDashoffset='0';orbs.forEach(dot=>dot.style.opacity='0');nodes.forEach(node=>node.classList.remove('mv-node-charge'));}}};motionRefresh.push(update);
    nodes.forEach(node=>{const card=node.closest('.rd-step,.ob-step,.rd-roadmap-item,.roadmap-stage');if(!card)return;card.addEventListener('pointermove',e=>{if(e.pointerType!=='mouse'||paused||reduce.matches)return;const r=card.getBoundingClientRect();node.style.setProperty('--mv-rx',`${(e.clientY-r.top-r.height/2)/r.height*-8}deg`);node.style.setProperty('--mv-ry',`${(e.clientX-r.left-r.width/2)/r.width*12}deg`);},{passive:true});card.addEventListener('pointerleave',()=>{node.style.removeProperty('--mv-rx');node.style.removeProperty('--mv-ry');});});
    if('IntersectionObserver'in window)new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;group.classList.toggle('mv-route-visible',visible);update();},{rootMargin:'60px'}).observe(group);else{visible=true;update();}
    if('ResizeObserver'in window)new ResizeObserver(layout).observe(group);else addEventListener('resize',layout,{passive:true});
    addEventListener('scroll',()=>{if(road&&visible&&!paused)drawRoad();},{passive:true});addEventListener('pagehide',()=>{cancelAnimationFrame(frame);frame=0;});addEventListener('pageshow',e=>{if(e.persisted){layout();update();}});layout();
  }

  function installFire(art) {
    let visible=false, initializing=false, update=()=>{};
    const consider=()=>{if(visible&&!reduce.matches&&!initializing){initializing=true;build();}update();};
    motionRefresh.push(consider);
    if('IntersectionObserver' in window) new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;consider();},{rootMargin:'80px'}).observe(art);
    else {visible=true;consider();}
    async function build(){
      let renderer;
      try{
        const THREE=await import('./vendor/three.module.min.js');
        if(reduce.matches){initializing=false;return;}
        const canvas=document.createElement('canvas');canvas.className='mv-fire-canvas';canvas.setAttribute('aria-hidden','true');art.prepend(canvas);
        renderer=new THREE.WebGLRenderer({canvas,alpha:true,antialias:false,powerPreference:'low-power'});renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.25));renderer.setClearColor(0,0);
        const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(38,1,.1,20);camera.position.z=3.5;
        const geometry=new THREE.BufferGeometry(),n=1100,pos=new Float32Array(n*3),seeds=new Float32Array(n*3);
        for(let i=0;i<n;i++){seeds[i*3]=(i*.61803399)%1;seeds[i*3+1]=(i*.41421356)%1;seeds[i*3+2]=(i*.75487766)%1;}
        geometry.setAttribute('position',new THREE.BufferAttribute(pos,3));geometry.setAttribute('aSeed',new THREE.BufferAttribute(seeds,3));
        const uniforms={uTime:{value:0},uDpr:{value:renderer.getPixelRatio()},uBend:{value:0},uLift:{value:0},uScale:{value:1}};
        const material=new THREE.ShaderMaterial({uniforms,transparent:true,depthWrite:false,blending:THREE.NormalBlending,
          vertexShader:`attribute vec3 aSeed;uniform float uTime;uniform float uDpr;uniform float uBend;uniform float uLift;uniform float uScale;varying float vLife;varying float vSpark;varying float vSeed;varying float vDepth;
          void main(){float spiral=step(.67,aSeed.z)* (1.-step(.94,aSeed.z));float spark=step(.94,aSeed.z);float life=fract(aSeed.x+uTime*(.15+aSeed.z*.08));float rise=life*.78+life*life*.22;float laneIndex=floor(aSeed.y*3.);float lane=(laneIndex-1.)*.36;float tongue=1.-abs(laneIndex-1.)*.18;float x=lane+(fract(aSeed.y*17.)-.5)*(.65-rise*.51)+sin(rise*8.+laneIndex*2.+uTime*1.55)*.13*rise;float y=-.98+rise*(2.02*tongue+spark*.3);float z=(aSeed.z-.34)*.6;
          if(spiral>.5){float strand=step(.805,aSeed.z);float angle=life*9.42478+strand*3.14159-uTime*.75;float radius=.72+sin(life*3.14159)*.16;float jitter=(aSeed.y-.5)*.13;x=cos(angle)*(radius+jitter);z=sin(angle)*.48;y=-.94+life*1.94;}
          x+=uBend*(rise*.17+z*.22);y+=uLift*z*.15;z+=uBend*x*.13;vec4 mv=modelViewMatrix*vec4(x,y,z,1.);gl_Position=projectionMatrix*mv;float size=(2.+floor(fract(aSeed.z*7.)*3.))*(1.-spark*.25)*(1.+z*.2);gl_PointSize=max(2.,floor(size*uDpr*uScale));vLife=life;vSpark=max(spark,spiral*.55);vSeed=aSeed.z;vDepth=z;}`,
          fragmentShader:`precision mediump float;varying float vLife;varying float vSpark;varying float vSeed;varying float vDepth;
          void main(){float shade=fract(vSeed*13.);vec3 hot=shade<.3?vec3(.68,.29,.025):shade<.7?vec3(1.,.54,.122):vec3(1.,.69,.125);hot=mix(hot,vec3(1.,.79,.32),vSpark*.45);float core=step(max(abs(gl_PointCoord.x-.5),abs(gl_PointCoord.y-.5)),.22);hot=mix(hot,vec3(1.,.76,.3),core*.25);float fade=smoothstep(0.,.06,vLife)*(1.-smoothstep(.81,1.,vLife));float depth=.72+vDepth*.35;gl_FragColor=vec4(hot,fade*(.6+shade*.35)*depth);}`});
        scene.add(new THREE.Points(geometry,material));
        let frame=0,last=0,time=0,lost=false,bendTarget=0,liftTarget=0;
        const resize=()=>{const r=art.getBoundingClientRect();renderer.setSize(Math.max(1,r.width),Math.max(1,r.height));camera.aspect=r.width/Math.max(1,r.height);camera.updateProjectionMatrix();const mobile=innerWidth<=760;geometry.setDrawRange(0,mobile?450:1100);uniforms.uScale.value=Math.min(r.height/280,1.25)*(mobile?1.2:1);canvas.dataset.particles=mobile?'450':'1100';canvas.dataset.style='helical-pixel-swarm';};
        const run=()=>visible&&!paused&&!reduce.matches&&!document.hidden&&!lost;
        const tick=now=>{frame=0;if(!run()){last=0;return;}frame=requestAnimationFrame(tick);if(last&&now-last<32)return;time+=last?Math.min((now-last)/1000,.08):0;last=now;uniforms.uTime.value=time;uniforms.uBend.value+=(bendTarget-uniforms.uBend.value)*.07;uniforms.uLift.value+=(liftTarget-uniforms.uLift.value)*.07;renderer.render(scene,camera);canvas.dataset.state='running';};
        update=()=>{canvas.hidden=reduce.matches;if(run()){if(!frame)frame=requestAnimationFrame(tick);}else{cancelAnimationFrame(frame);frame=0;last=0;canvas.dataset.state='paused';}};
        canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();lost=true;update();});canvas.addEventListener('webglcontextrestored',()=>{lost=false;update();});
        if('ResizeObserver' in window)new ResizeObserver(resize).observe(art);else addEventListener('resize',resize,{passive:true});
        art.closest('.rd-stake')?.addEventListener('pointermove',e=>{if(e.pointerType==='mouse'){const r=art.getBoundingClientRect();bendTarget=Math.max(-1,Math.min(1,(e.clientX-r.left)/r.width*2-1));liftTarget=Math.max(-1,Math.min(1,1-(e.clientY-r.top)/r.height*2));}},{passive:true});
        art.closest('.rd-stake')?.addEventListener('pointerleave',()=>{bendTarget=0;liftTarget=0;},{passive:true});
        addEventListener('pagehide',e=>{cancelAnimationFrame(frame);frame=0;last=0;if(!e.persisted){renderer.dispose();geometry.dispose();material.dispose();}});addEventListener('pageshow',e=>{if(e.persisted)update();});
        art.classList.add('mv-fire-ready');resize();update();
      }catch(_){renderer?.dispose();art.querySelector('.mv-fire-canvas')?.remove();}
    }
  }

  let loading = false;
  async function startField() {
    if (loading || reduce.matches) return;
    loading = true;
    let renderer;
    try {
      const THREE = await import('./vendor/three.module.min.js');
      if (reduce.matches) { loading = false; return; }
      const canvas = document.createElement('canvas'); canvas.className = 'mv-swarm-field';
      canvas.setAttribute('aria-hidden', 'true'); canvas.dataset.particles = innerWidth <= 760 ? '350' : '1000';
      document.body.prepend(canvas);
      renderer = new THREE.WebGLRenderer({canvas, alpha: true, antialias: false, powerPreference: 'low-power'});
      renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.25));
      renderer.setClearColor(0, 0);
      const scene = new THREE.Scene();
      const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, .1, 10); camera.position.z = 2;
      const count = 1000;
      const points = new Float32Array(count * 3); const seeds = new Float32Array(count);
      for (let i = 0; i < count; i++) { points[i*3] = ((i * .61803398875) % 1) * 2 - 1; points[i*3+1] = ((i * .41421356237) % 1) * 2 - 1; seeds[i] = (i * .75487766) % 1; }
      const geometry = new THREE.BufferGeometry(); geometry.setAttribute('position', new THREE.BufferAttribute(points, 3)); geometry.setAttribute('aSeed', new THREE.BufferAttribute(seeds, 1));
      const zones=[...document.querySelectorAll('#hive,#roadmap,.roadmap-trail,#communities,.rd-footer')].slice(0,6);
      const uniforms = {uTime:{value:0},uScroll:{value:scrollY},uPointer:{value:new THREE.Vector2(3,3)},uDpr:{value:renderer.getPixelRatio()},uBands:{value:Array.from({length:6},()=>new THREE.Vector2(-3,-2))}};
      const material = new THREE.ShaderMaterial({transparent:true,depthWrite:false,depthTest:false,uniforms,
        vertexShader: `attribute float aSeed; uniform float uTime; uniform float uScroll; uniform vec2 uPointer; uniform float uDpr; varying float vAlpha;varying float vY;
          void main(){vec2 p=position.xy; float t=uTime*.018; p.y=mod(p.y+t*(.4+aSeed)+uScroll*.00013+1.,2.)-1.; p.x+=sin(p.y*5.+uTime*.11+aSeed*12.)*.09; vec2 away=p-uPointer; float d=length(away); p+=normalize(away+vec2(.001))*max(0.,.25-d)*.17; vAlpha=.11+aSeed*.18;vY=(p.y+1.)*.5; gl_Position=vec4(p,0.,1.); gl_PointSize=(1.+aSeed*1.7)*uDpr;}`,
        fragmentShader:`precision mediump float;uniform vec2 uBands[6]; varying float vAlpha;varying float vY; void main(){float band=0.;for(int i=0;i<6;i++){band=max(band,smoothstep(uBands[i].x,uBands[i].x+.09,vY)*(1.-smoothstep(uBands[i].y-.09,uBands[i].y,vY)));}if(band<.01)discard;float d=length(gl_PointCoord-.5); if(d>.5)discard; gl_FragColor=vec4(1.,.51,.105,vAlpha*band*(1.-smoothstep(.12,.5,d)));}`});
      scene.add(new THREE.Points(geometry, material));
      let frame = 0, last = 0, elapsed = 0, visible = false, contextLost = false;
      const updateZones=()=>{visible=false;zones.forEach((zone,i)=>{const r=zone.getBoundingClientRect();uniforms.uBands.value[i].set(1-r.bottom/innerHeight,1-r.top/innerHeight);if(r.top<innerHeight&&r.bottom>0)visible=true;});canvas.dataset.zones=visible?'selected-visible':'outside-selected';if(!visible)renderer.clear();refreshGPU();};
      const resize = () => { renderer.setSize(innerWidth, innerHeight); const n=innerWidth<=760?350:1000; geometry.setDrawRange(0,n);canvas.dataset.particles=String(n); };
      const canRun = () => !paused && !reduce.matches && !document.hidden && visible && !contextLost;
      const tick = now => {
        frame = 0;
        if (!canRun()) { last=0; return; }
        frame = requestAnimationFrame(tick);
        if (last && now-last < 32) return;
        elapsed += last ? Math.min((now-last)/1000,.08) : 0; last=now;
        uniforms.uTime.value=elapsed; uniforms.uScroll.value=scrollY;
        renderer.render(scene,camera); canvas.dataset.state='running';
      };
      refreshGPU = () => {
        canvas.hidden = reduce.matches;
        if (canRun()) { if (!frame) frame=requestAnimationFrame(tick); }
        else { cancelAnimationFrame(frame);frame=0;last=0;canvas.dataset.state='paused'; }
      };
      addEventListener('resize', resize, {passive:true});
      addEventListener('scroll',updateZones,{passive:true});addEventListener('resize',updateZones,{passive:true});
      addEventListener('pointermove', e => { if(e.pointerType==='mouse') uniforms.uPointer.value.set(e.clientX/innerWidth*2-1,1-e.clientY/innerHeight*2); }, {passive:true});
      document.addEventListener('pointerleave', () => uniforms.uPointer.value.set(3,3));
      canvas.addEventListener('webglcontextlost', e => { e.preventDefault();contextLost=true;refreshGPU(); });
      canvas.addEventListener('webglcontextrestored', () => {contextLost=false;refreshGPU();});
      addEventListener('pagehide', event => {
        cancelAnimationFrame(frame); frame=0;last=0;
        if (!event.persisted) {renderer.dispose();geometry.dispose();material.dispose();}
      });
      addEventListener('pageshow', event => {if(event.persisted) refreshGPU();});
      resize(); updateZones(); refreshGPU();
    } catch (_) {
      renderer?.dispose(); document.querySelector('.mv-swarm-field')?.remove();
      // Motion is decorative: unavailable WebGL never affects content or navigation.
    }
  }
  startField();
})();
