/* SWARM experience. Three.js r180, served locally. The mascot is the actual V4 GLB.
 * assets/logo-v2.svg is a sampling mask only; it is never rendered as a solid plane.
 * Chart geometry is fictional illustration, not a price feed or prediction.
 * No global animation API: data attributes expose real phase/state for inspection.
 * Pointer events are passive; touch scrolling is never captured or cancelled.
 */
const initialCanvas = document.querySelector('.rd-canvas');
if (initialCanvas) startSwarm(initialCanvas);

async function startSwarm(originalCanvas) {
  let canvas = originalCanvas;
  const art = canvas.closest('.rd-art') || document.querySelector('.rd-art');
  const animationRegion=canvas.closest('.rd-hero')||art;
  const pauseButton = art?.querySelector('.rd-motion');
  const stirButton = art?.querySelector('.rd-stir');
  if (!art) return;
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const coarse = matchMedia('(pointer: coarse)').matches;
  const constrained = (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 4;
  const saveData = Boolean(navigator.connection?.saveData);
  const count = saveData ? 900 : constrained ? 1200 : coarse ? 1800 : 4200;
  const dprLimit = saveData || constrained ? 1 : 1.5;
  const random = () => Math.random();
  const mix = (a, b, t) => a + (b - a) * t;
  const clamp = x => Math.min(1, Math.max(0, x));
  const ease = x => { const t = clamp(x); return t*t*t*(t*(t*6-15)+10); };
  let localPaused = reduced.matches;
  let globalPaused = Boolean(window.swarmMotionPaused);
  let paused = localPaused || globalPaused;
  let staticPreference = reduced.matches;
  let visible = true;
  let destroyed = false;
  let contextLost = false;
  let elapsed = 0;
  let cycleTime = 0;
  let cycle = 0;
  let frame = 0;
  let previous = 0;
  let frames = 0;
  let lastReport = -1;
  let width = 1, height = 1, halfW = 1.4, halfH = 1.4;
  let stageX=0,stageY=0;
  let meshAvailable=false;
  let meshOpacity=0;
  let draw, resizeEngine, destroyEngine;
  let rendererType = 'fallback';
  let durations = [2, 3, 11, 4, 5, 3, 5, 5, 5];
  const phases=['swarm','forming-chart','chart','forming-bee','bee','eyes-light','dissolving-bee','logo','scatter'];
  let cycleYaw = -.16;
  let wingSpeed = 5.2;
  let flightVariation = 1;
  let chartDirection = 1;
  let chartSeed = random()*6;
  const pointer = {x: 10, y: 10, strength: 0, target: 0};
  const ripple = {x: 0, y: 0, start: -100, strength: 0};
  let touchStart = null;
  const cleanups = [];
  const on = (target, name, handler, options) => {
    target.addEventListener(name, handler, options);
    cleanups.push(() => target.removeEventListener(name, handler, options));
  };
  const bee = new Float32Array(count * 3);
  const beeColors = new Float32Array(count * 3);
  const eyes = new Float32Array(count * 3);
  const chart = new Float32Array(count * 4);
  const chartColors = new Float32Array(count * 3);
  const chartData = new Float32Array(count * 4);
  const flags = new Float32Array(count * 3);
  const logo = new Float32Array(count * 3);
  const scatterA = new Float32Array(count * 3);
  const scatterB = new Float32Array(count * 3);
  const seeds = new Float32Array(count * 4);
  const parts = new Float32Array(count);
  const logoColors = new Float32Array(count * 3);
  let modelSource='procedural-fallback';
  let eyeCenter=[0,.425,.20],eyeWidth=.47;
  let modelEyes=[];
  let logoCell=.025,eyeCell=.012;
  let visibleCount=count;
  const sphere = () => {
    const y = 1 - random()*2, r = Math.sqrt(1-y*y), angle = random()*Math.PI*2;
    return [Math.cos(angle)*r, y, Math.sin(angle)*r];
  };
  function scatterFill(array) {
    for (let i=0; i<count; i++) {
      array[i*3] = (random()*2-1)*.98;
      array[i*3+1] = (random()*2-1)*.94;
      array[i*3+2] = (random()*2-1)*.55;
    }
  }
  scatterFill(scatterA); scatterFill(scatterB);
  for (let i=0; i<count; i++) {
    const part = random();
    let [x,y,z] = sphere();
    if (part < .43) {
      // Two unfilled horizontal bands produce the bee's striped abdomen.
      let bodyY = -.18 + y*.52;
      while ((bodyY>-.10 && bodyY<-.025) || (bodyY>-.39 && bodyY<-.305)) {
        [x,y,z] = sphere(); bodyY = -.18+y*.52;
      }
      bee.set([x*.285,bodyY,z*.23],i*3); parts[i]=0;
    } else if (part < .57) {
      bee.set([x*.205,.425+y*.205,z*.18],i*3); parts[i]=1;
    } else if (part < .97) {
      const side=part<.77?-1:1;
      const xx=x*.405, yy=y*.185, angle=side*.45;
      bee.set([side*.43+xx*Math.cos(angle)-yy*Math.sin(angle),.38+xx*Math.sin(angle)+yy*Math.cos(angle),z*.07-.025],i*3);
      parts[i]=side<0?2:3;
    } else {
      const side=i%2?-1:1,t=random();
      bee.set([side*(.08+.15*t),.57+.20*t,.025+Math.sin(t*Math.PI)*.03],i*3);parts[i]=4;
    }
    seeds.set([random()*Math.PI*2,.5+random()*.8,random(),random()],i*4);
    const tone=.67+random()*.33;
    beeColors.set([tone,.35+random()*.35,.045+random()*.13],i*3);
  }

  // Replace the procedural safety fallback with actual Blender surface samples.
  // This local asset is optional: a unavailable model never blanks the experience.
  try {
    const response=await fetch('/assets/mascot/swarm-mascot-points.json?v=4',{signal:AbortSignal.timeout(4500)});
    if(!response.ok)throw new Error('Model unavailable');
    const model=await response.json();
    if(!Array.isArray(model.positions)||model.positions.length<900||model.positions.length%3)throw new Error('Invalid points');
    if(!Array.isArray(model.colors)||model.colors.length!==model.positions.length)throw new Error('Invalid colors');
    if(!model.positions.every(Number.isFinite)||!model.colors.every(Number.isFinite))throw new Error('Invalid numeric data');
    const available=[];
    for(let j=0;j<model.positions.length/3;j++)if(model.parts?.[j]!==5)available.push(j);
    if(available.length<200)throw new Error('Insufficient body samples');
    // Exporters group samples by mesh. Shuffle before resampling so the 2D and
    // adaptive draw-range prefixes still contain both wings, head and abdomen.
    for(let j=available.length-1;j>0;j--){const k=Math.floor(random()*(j+1));[available[j],available[k]]=[available[k],available[j]];}
    for(let i=0;i<count;i++){
      const j=available[Math.floor(i/count*available.length)];
      bee.set(model.positions.slice(j*3,j*3+3),i*3);
      const color=model.colors.slice(j*3,j*3+3).map(clamp);
      // Dark physical materials need a little warm rim light in a point-only
      // rendering. Keep the head, bands and limbs legible against warm black.
      if(Math.max(...color)<.18){
        const depth=clamp((model.positions[j*3+2]+.25)/.55);
        const rim=clamp(Math.abs(model.positions[j*3])*1.9);
        const bronze=.13+depth*.09+rim*.12;
        color[0]=Math.max(color[0],bronze);color[1]=Math.max(color[1],bronze*.62);color[2]=Math.max(color[2],bronze*.30);
      }
      beeColors.set(color,i*3);
      parts[i]=Number.isFinite(model.parts?.[j])?model.parts[j]:0;
    }
    if(Array.isArray(model.eyeCenter)&&model.eyeCenter.length===3&&model.eyeCenter.every(Number.isFinite))eyeCenter=model.eyeCenter;
    if(Number.isFinite(model.eyeWidth)&&model.eyeWidth>.1&&model.eyeWidth<1.6)eyeWidth=model.eyeWidth;
    for(let j=0;j<model.positions.length/3;j++)if(model.parts?.[j]===5)modelEyes.push({position:model.positions.slice(j*3,j*3+3),color:model.colors.slice(j*3,j*3+3)});
    modelSource='blender';
  } catch { /* retain the fully local procedural bee */ }

  // Fictional rolling OHLC stream. Each settled candle retains its identity and
  // shape; only the newest candle develops, then a new candle enters each second.
  function chartPrice(index){return -.52+index*.060+Math.cos(index*Math.PI)*.145+Math.sin(index*.72+chartSeed)*.045;}
  function liveClose(index,progress){return mix(chartPrice(index),chartPrice(index+1),progress)+Math.sin(progress*Math.PI)*Math.sin(progress*Math.PI*3.2+index*.7)*.15;}
  function candle(index,progress){
    const open=chartPrice(index),close=liveClose(index,progress);let high=Math.max(open,close),low=Math.min(open,close);
    for(let j=1;j<=16;j++){const p=j/16;if(p>progress)break;const value=liveClose(index,p);high=Math.max(high,value);low=Math.min(low,value);}
    return {open,close,high:high+.025,low:low-.025};
  }
  let candleCache=[],chartCacheTime=-1;
  function updateCandles(time){
    if(time===chartCacheTime)return;chartCacheTime=time;const tick=Math.floor(time),fraction=time-tick;
    candleCache=Array.from({length:12},(_,slot)=>candle(tick+slot,slot===11?fraction:1));
  }
  function chartPoint(i,time){
    const k=i*4,type=chartData[k],index=chartData[k+1],t=chartData[k+2];
    if(!type)return {x:chart[k],y:chart[k+1],color:[.34,.225,.12]};
    updateCandles(time);const tick=Math.floor(time),fraction=time-tick,slot=((index-tick)%12+12)%12;
    const {open,close,high,low}=candleCache[slot],offset=type===1?chartData[k+3]:0;
    return {x:-.94+slot*.18-fraction*.18+offset,y:(type===1?mix(open,close,t):mix(low,high,t))-.060*time,color:close>=open?[1,.72,.22]:[.96,.31,.055]};
  }
  for(let i=0;i<count;i++){
    let x,y,z=(random()-.5)*.05,order,color;
    if(i<count*.94){
      const index=i%12,sample=Math.floor(i/12),wick=sample%19===18,t=(wick?(Math.floor(sample/19)*7)%18:sample%19)/17;
      const offset=((Math.floor(sample/19)%7)-3)*.015;
      chartData.set([wick?2:1,index,t,offset],i*4);
      const point=chartPoint(i,0);x=point.x;y=point.y;color=point.color;order=(index+.3)/12;
    }else{
      const axis=random()<.25;
      if(axis){x=-1.03;y=mix(-.74,.80,random());}else{x=mix(-1.03,1.04,random());y=-.74+Math.floor(random()*5)*.37;}
      order=axis?0:(x+1.03)/2.07;color=[.34,.225,.12];z=-.12;
    }
    chart.set([x,y,z,order],i*4);chartColors.set(color,i*3);
  }

  // Regular point grids sample the SVG's silhouette and preserve the open eye gaps.
  // The raster exists only in memory to read the mask; no image/mesh is displayed.
  const markImage = new Image();
  markImage.src = '/assets/logo-v2.svg';
  try { await markImage.decode(); }
  catch {
    showStaticFallback();
    return;
  }
  if (!canvas.isConnected) return;
  const markCanvas=document.createElement('canvas');
  markCanvas.width=768;markCanvas.height=384;
  const markContext=markCanvas.getContext('2d',{willReadFrequently:true});
  if (!markContext) { showStaticFallback(); return; }
  markContext.drawImage(markImage,0,0,768,384);
  const pixels=markContext.getImageData(0,0,768,384).data;
  function sampleGrid(target){
    let columns=18,cells=[];
    while(cells.length<target&&columns<240){
      columns+=2;cells=[];const rows=columns/2;
      for(let row=0;row<rows;row++)for(let col=0;col<columns;col++){
        const x=Math.floor((col+.5)/columns*768),y=Math.floor((row+.5)/rows*384),n=(y*768+x)*4;
        if(pixels[n+3]>190)cells.push({x:(col+.5)/columns-.5,y:.5-(row+.5)/rows,tone:pixels[n+1]/255});
      }
    }
    for(let i=cells.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[cells[i],cells[j]]=[cells[j],cells[i]];}
    return {cells,columns};
  }
  const logoCount=modelEyes.length?Math.min(count,modelEyes.length):Math.min(1400,Math.floor(count*.72));
  const eyeCount=modelEyes.length?logoCount:Math.min(340,Math.floor(count*.2));
  const logoGrid=sampleGrid(logoCount),eyeGrid=sampleGrid(eyeCount);
  logoCell=1.95/logoGrid.columns*.77;eyeCell=eyeWidth/eyeGrid.columns*.83;
  for(let i=0;i<count;i++){
    const cell=logoGrid.cells[i%logoGrid.cells.length],eye=eyeGrid.cells[i%eyeGrid.cells.length];
    const layer=Math.floor(random()*4)/3;
    logo.set([cell.x*1.95,cell.y*.975,.025+layer*.095],i*3);
    eyes.set([eyeCenter[0]+eye.x*eyeWidth,eyeCenter[1]+eye.y*eyeWidth*.5,eyeCenter[2]+.018+layer*.024],i*3);
    const shade=random();
    const palette=shade>.88?[1,.9,.65]:shade>.43?[1,.65,.14]:shade>.13?[.94,.39,.065]:[.50,.18,.035];
    const lighting=.76+layer*.24;
    logoColors.set(palette.map(value=>value*lighting),i*3);
    flags.set([i<eyeCount?1:0,i<logoCount?1:0,layer],i*3);
  }
  if(modelEyes.length){
    // These are the centers/colors exported from the actual 832 raised GLB eye
    // tiles. Their identity and ordering survive the entire extraction/zoom.
    for(let i=0;i<count;i++){
      const sample=modelEyes[i%modelEyes.length],p=sample.position;
      eyes.set(p,i*3);
      logo.set([(p[0]-eyeCenter[0])*1.95/eyeWidth,(p[1]-eyeCenter[1])*1.95/eyeWidth,(p[2]-eyeCenter[2])*1.95/eyeWidth+.06],i*3);
      logoColors.set(sample.color,i*3);
    }
    eyeCell=.009;logoCell=eyeCell*1.95/eyeWidth;
  }

  function state() {
    if (staticPreference) return {phase:'bee',progress:1,chart:0,reveal:1,bee:1,logo:0,mark:1,variation:1};
    const ends=[];durations.reduce((total,d)=>{ends.push(total+d);return total+d;},0);
    const segment=ends.findIndex(end=>cycleTime<end);
    const index=segment<0?8:segment;
    const start=index?ends[index-1]:0;
    const progress=clamp((cycleTime-start)/durations[index]);
    const t=ease(progress);
    const result={phase:phases[index],progress,chart:0,reveal:0,bee:0,logo:0,mark:0,variation:ease(cycleTime/durations[0])};
    if(index===1){result.chart=ease(progress*4);result.reveal=progress;}
    if(index===2){result.chart=1;result.reveal=1;}
    if(index===3){result.chart=1-ease(progress/.23);result.reveal=1;result.bee=ease((progress-.20)/.80);}
    if(index>=4&&index<=7)result.bee=1;
    if(index===5)result.mark=t;
    if(index===6){result.logo=t;result.mark=1;}
    if(index===7){result.logo=1;result.mark=1;}
    if(index===8){result.bee=1-t;result.logo=1-t;result.mark=1-t;}
    return result;
  }
  // One soft sweep during the isolated mark hold, never a repeating flash.
  function sweepTime(s){return s.logo>.99?Math.max(0,cycleTime-durations.slice(0,7).reduce((sum,d)=>sum+d,0)):elapsed%11;}

  try {
    // Dynamic local import allows a fully animated 2D fallback if GPU or module setup fails.
    const THREE = await import('./vendor/three.module.min.js');
    const renderer = new THREE.WebGLRenderer({canvas,alpha:true,antialias:false,powerPreference:'low-power',premultipliedAlpha:false});
    renderer.setPixelRatio(Math.min(devicePixelRatio||1,dprLimit));
    renderer.setClearColor(0x000000,0);
    renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1.4,1.4,1.4,-1.4,.1,20);
    camera.position.z=5;
    const mascot=new THREE.Group();scene.add(mascot);
    const normalizedModel=new THREE.Group();normalizedModel.scale.setScalar(1/1.7);normalizedModel.position.y=-.03/1.7;mascot.add(normalizedModel);
    const meshMaterials=[],eyeMaterials=[],wingPivots=[],wingGhosts=[];
    const bodyPixels={uBodyPixel:{value:coarse?3:5},uBodyDpr:{value:renderer.getPixelRatio()},uBodyDissolve:{value:0}};
    const lightingTarget=new THREE.Object3D();scene.add(lightingTarget);
    scene.add(new THREE.HemisphereLight(0xfff0d2,0x65360f,2.3));
    const lights=[];
    for(const [color,intensity,x,y,z] of [[0xfff1da,4.2,-2.7,3.7,4.0],[0xffa638,3.4,3.2,1.8,-1.2],[0xffd583,1.5,1.7,-1.4,3.0]]){
      const light=new THREE.DirectionalLight(color,intensity);light.position.set(x,y,z);light.target=lightingTarget;scene.add(light);lights.push({light,x,y,z});
    }
    try{
      const {GLTFLoader}=await import('./vendor/GLTFLoader.js');
      const response=await fetch('/assets/mascot-v4/swarm-mascot.glb',{signal:AbortSignal.timeout(12000)});
      if(!response.ok)throw new Error('Mascot unavailable');
      const gltf=await new GLTFLoader().parseAsync(await response.arrayBuffer(),'/assets/mascot-v4/');
      normalizedModel.add(gltf.scene);
      // GLB nodes are the actual Blender parts. Reparent just the wing assemblies
      // around their original root; screen, eyes and body remain one aligned model.
      for(const side of [-1,1]){
        const pivot=new THREE.Group();pivot.position.set(side*.30,.22,-.17);gltf.scene.add(pivot);gltf.scene.updateMatrixWorld(true);
        const label=side<0?'left':'right';
        const wingNodes=gltf.scene.children.filter(node=>node!==pivot&&node.name.toLowerCase().startsWith(label)&&/(upper.*wing|lower.*wing|honeycomb.*vein|primary.*flight.*spar)/i.test(node.name));
        for(const node of wingNodes)pivot.attach(node);
        wingPivots.push({pivot,side});
      }
      const clones=new Map();
      gltf.scene.traverse(node=>{
        if(!node.isMesh)return;
        node.frustumCulled=false;
        const clone=source=>{
          if(clones.has(source))return clones.get(source);
          const mat=source.clone(),isEye=/exact.swarm.logo/i.test(source.name);
          const record={mat,opacity:/wing membrane/i.test(source.name)?.56:mat.opacity,color:mat.color.clone(),emissive:mat.emissive?.clone(),intensity:mat.emissiveIntensity||0};
          // Warm metal needs visible grazing light on a black page. Keep the
          // supplied materials, adding a restrained bronze lift to dark shells.
          if(!isEye&&Math.max(mat.color.r,mat.color.g,mat.color.b)<.035)mat.color.lerp(new THREE.Color(.06,.039,.022),.45);
          if(/screen glass/i.test(source.name)){mat.roughness=.48;mat.metalness=.12;}
          if(!isEye){
            mat.onBeforeCompile=shader=>{
              Object.assign(shader.uniforms,bodyPixels);
              shader.fragmentShader='uniform float uBodyPixel,uBodyDpr,uBodyDissolve;\n'+shader.fragmentShader;
              shader.fragmentShader=shader.fragmentShader.replace('#include <clipping_planes_fragment>',`#include <clipping_planes_fragment>
                vec2 tileCoord=gl_FragCoord.xy/(uBodyPixel*uBodyDpr);
                vec2 tile=fract(tileCoord);
                float tileSeed=fract(sin(dot(floor(tileCoord),vec2(127.1,311.7)))*43758.5453);
                float gutter=max(.18,1./(uBodyPixel*uBodyDpr));
                if(tile.x<gutter||tile.y<gutter)discard;
                if(tileSeed<uBodyDissolve)discard;`);
              shader.fragmentShader=shader.fragmentShader.replace('#include <opaque_fragment>',`outgoingLight*=mix(.62,1.18,tileSeed);
                outgoingLight+=vec3(.026,.013,.003)*step(.86,tileSeed);
                #include <opaque_fragment>`);
            };
            mat.customProgramCacheKey=()=> 'swarm-pixel-body-v7';
          }
          meshMaterials.push(record);if(isEye)eyeMaterials.push(record);clones.set(source,mat);return mat;
        };
        node.material=Array.isArray(node.material)?node.material.map(clone):clone(node.material);
      });
      // Two low-opacity temporal wing samples give fast flight a continuous
      // membrane sweep, rather than flashing wing brightness between frames.
      for(const {pivot,side} of wingPivots)for(const offset of [-1.35,1.35]){
        const ghost=pivot.clone(true);gltf.scene.add(ghost);
        ghost.traverse(node=>{if(!node.isMesh)return;const duplicate=source=>{
          const mat=source.clone();mat.onBeforeCompile=source.onBeforeCompile;mat.customProgramCacheKey=source.customProgramCacheKey;
          const record={mat,opacity:source.opacity*.13,color:mat.color.clone(),emissive:mat.emissive?.clone(),intensity:mat.emissiveIntensity||0};meshMaterials.push(record);return mat;
        };node.material=Array.isArray(node.material)?node.material.map(duplicate):duplicate(node.material);});
        wingGhosts.push({pivot:ghost,side,offset});
      }
      meshAvailable=true;canvas.dataset.mascotGeometry='gltf-mesh';canvas.dataset.meshNodes=String(gltf.scene.children.length);
    }catch{canvas.dataset.mascotGeometry='particle-fallback';}
    const geometry=new THREE.BufferGeometry();
    geometry.setAttribute('position',new THREE.BufferAttribute(bee,3));
    geometry.setAttribute('aBee',new THREE.BufferAttribute(bee,3));
    geometry.setAttribute('aBeeColor',new THREE.BufferAttribute(beeColors,3));
    geometry.setAttribute('aEyes',new THREE.BufferAttribute(eyes,3));
    geometry.setAttribute('aChart',new THREE.BufferAttribute(chart,4));
    geometry.setAttribute('aChartColor',new THREE.BufferAttribute(chartColors,3));
    geometry.setAttribute('aChartData',new THREE.BufferAttribute(chartData,4));
    geometry.setAttribute('aFlags',new THREE.BufferAttribute(flags,3));
    geometry.setAttribute('aLogo',new THREE.BufferAttribute(logo,3));
    geometry.setAttribute('aScatterA',new THREE.BufferAttribute(scatterA,3));
    geometry.setAttribute('aScatterB',new THREE.BufferAttribute(scatterB,3));
    geometry.setAttribute('aSeed',new THREE.BufferAttribute(seeds,4));
    geometry.setAttribute('aPart',new THREE.BufferAttribute(parts,1));
    geometry.setAttribute('aLogoColor',new THREE.BufferAttribute(logoColors,3));
    const uniforms={
      uTime:{value:0},uBee:{value:0},uLogo:{value:0},uEye:{value:0},uChart:{value:0},uReveal:{value:0},uVariation:{value:0},
      uUnit:{value:200},uCell:{value:new THREE.Vector2(logoCell,eyeCell)},
      uEyeFrame:{value:new THREE.Vector3(eyeCenter[0],eyeCenter[1],eyeWidth)},
      uDpr:{value:renderer.getPixelRatio()},uBounds:{value:new THREE.Vector2(halfW,halfH)},
      uPointer:{value:new THREE.Vector4(10,10,0,.3)},uRipple:{value:new THREE.Vector4(0,0,-100,0)},
      uCycle:{value:new THREE.Vector3(cycleYaw,wingSpeed,flightVariation)},
      uChartMotion:{value:new THREE.Vector3(0,chartDirection,chartSeed)},
      uSweepTime:{value:0},
      uMeshVisible:{value:0},uStage:{value:new THREE.Vector2(0,0)},
      uMascotMatrix:{value:new THREE.Matrix4()},
      uWake:{value:0},
    };
    const material=new THREE.ShaderMaterial({
      transparent:true,depthWrite:false,depthTest:false,blending:THREE.NormalBlending,uniforms,
      vertexShader:`
        attribute vec3 aBee,aBeeColor,aEyes,aLogo,aScatterA,aScatterB,aLogoColor,aFlags,aChartColor;
        attribute vec4 aSeed,aChart,aChartData; attribute float aPart;
        uniform float uTime,uBee,uLogo,uEye,uChart,uReveal,uVariation,uDpr,uUnit,uSweepTime,uMeshVisible,uWake; uniform vec2 uBounds,uCell,uStage;
        uniform vec4 uPointer,uRipple; uniform vec3 uCycle,uEyeFrame,uChartMotion;
        uniform mat4 uMascotMatrix;
        varying vec3 vColor; varying float vAlpha;
        vec3 beePose(vec3 p){
          float yaw=uCycle.x+sin(uTime*.55)*.14+clamp(uPointer.x-uStage.x,-1.,1.)*uPointer.z*.22;
          float pitch=sin(uTime*.43)*.075-clamp(uPointer.y-uStage.y,-1.,1.)*uPointer.z*.12;
          p.xz=mat2(cos(yaw),-sin(yaw),sin(yaw),cos(yaw))*p.xz;
          p.yz=mat2(cos(pitch),-sin(pitch),sin(pitch),cos(pitch))*p.yz;
          p.xy*=3.8/(3.8-p.z);
          p.x+=sin(uTime*.47)*.023;p.y+=sin(uTime*.85)*.025;
          return p;
        }
        void main(){
          vec3 cloud=mix(aScatterA,aScatterB,uVariation);
          cloud.xy*=uBounds*.94;
          cloud.x=mod(cloud.x+uTime*(aSeed.z-.5)*.24+uBounds.x,2.*uBounds.x)-uBounds.x;
          cloud.x+=sin(uTime*(.40+aSeed.z*.45)+aSeed.x)*.16;
          cloud.y+=cos(uTime*(.32+aSeed.y*.25)+aSeed.x*2.)*.16;
          cloud.z+=sin(uTime*(.2+aSeed.z*.3)+aSeed.x)*.25;
          vec3 target=aBee;
          if(aPart>1.5&&aPart<3.5){
            float side=sign(target.x),angle=side*(sin(uTime*uCycle.y)*.36+.10);
            vec3 hinge=vec3(side*.176,.129,-.100),local=target-hinge;
            local.xz=mat2(cos(angle),-sin(angle),sin(angle),cos(angle))*local.xz;
            local.y+=sin(uTime*uCycle.y)*abs(local.x)*.045;target=hinge+local;
          }
          target=(uMascotMatrix*vec4(target,1.)).xyz;
          float arrival=smoothstep(aSeed.w*.15,.83+aSeed.w*.17,uBee);
          vec3 chartPoint=aChart.xyz,chartColor=aChartColor;
          chartPoint.xy+=uStage;
          vec3 p=mix(cloud,chartPoint,uChart);
          p=mix(p,target,arrival);
          float flight=sin(arrival*3.14159);
          p+=vec3(sin(aSeed.x+arrival*6.*uCycle.z),cos(aSeed.x*2.+arrival*8.),sin(aSeed.x*3.+arrival*5.))*flight*.22;
          vec2 route=target.xy-cloud.xy;
          p.xy+=normalize(vec2(-route.y,route.x)+vec2(.001))*flight*sin(aSeed.x+arrival*3.14159)*.52;
          float wake=step(.96,aSeed.w)*uWake;
          vec3 wakePoint=(uMascotMatrix*vec4(-.18-aSeed.y*.90,-.1+sin(aSeed.x+uTime*2.)*.19,.1+cos(aSeed.x+uTime)*.18,1.)).xyz;
          p=mix(p,wakePoint,wake);
          float eye=uEye*aFlags.x;
          vec3 eyeTarget=(uMascotMatrix*vec4(aEyes,1.)).xyz;
          p=mix(p,eyeTarget,eye);
          vec3 raisedLogo=aLogo;
          float logoYaw=sin(uTime*.30)*.075+uPointer.z*clamp(uPointer.x-uStage.x,-1.,1.)*.13;
          float logoPitch=sin(uTime*.37)*.035-uPointer.z*clamp(uPointer.y-uStage.y,-1.,1.)*.06;
          raisedLogo.xz=mat2(cos(logoYaw),-sin(logoYaw),sin(logoYaw),cos(logoYaw))*raisedLogo.xz;
          raisedLogo.yz=mat2(cos(logoPitch),-sin(logoPitch),sin(logoPitch),cos(logoPitch))*raisedLogo.yz;
          raisedLogo.xy*=1.015;raisedLogo.y+=sin(uTime*.6)*.023;
          raisedLogo.xy+=uStage;
          vec3 destination=mix(cloud*1.2,raisedLogo,aFlags.y);
          p=mix(p,destination,uLogo);
          if(aFlags.y>.5&&uLogo>0.){
            // The exact face tiles pull forward first, then grow from that same
            // anchor into the large mark. No unrelated second logo fades in.
            float growth=smoothstep(.10,1.,uLogo);
            p=mix(eyeTarget,raisedLogo,growth);
            p.z+=sin(uLogo*3.14159)*.40;
          }
          float breakup=sin(uLogo*3.14159)*mix(.48,.13,aFlags.y);
          p+=vec3(sin(aSeed.x+uLogo*9.),cos(aSeed.x*2.+uLogo*7.),sin(aSeed.x+uLogo*5.))*breakup*(1.-aFlags.y);
          vec2 delta=p.xy-uPointer.xy;float distance=length(delta);
          p.xy+=normalize(delta+vec2(.0001))*exp(-distance*distance/.12)*uPointer.z*mix(.16,.21,uLogo);
          float age=uTime-uRipple.z;float ring=age*.85;
          float ripple=exp(-pow((length(p.xy-uRipple.xy)-ring)*8.,2.))*exp(-age*1.3)*step(0.,age)*uRipple.w;
          p.xy+=normalize(p.xy-uRipple.xy+vec2(.0001))*ripple*.23;p.z+=ripple*.13;
          gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.);
          float size=2.+aSeed.y*1.5;
          size=mix(size,max(1.7,uUnit*.013),uChart);
          size=mix(size,max(1.2,uCell.y*uUnit),eye);
          size=mix(size,max(1.3,uCell.x*uUnit),smoothstep(.10,1.,uLogo)*aFlags.y);
          gl_PointSize=size*uDpr;
          vec3 honey=mix(vec3(1.,.39,.07),vec3(1.,.72,.24),aSeed.z);
          vColor=mix(honey,chartColor,uChart);
          float depthLight=.78+clamp((target.z+.28)/.65,0.,1.)*.32;
          vColor=mix(vColor,aBeeColor*depthLight,arrival);
          vColor=mix(vColor,aLogoColor,eye);
          vColor=mix(vColor,aLogoColor,uLogo);
          float sweep=uSweepTime,sweepX=-1.3+sweep*.95;
          float glint=exp(-pow((p.x-uStage.x-sweepX)*7.,2.))*smoothstep(.2,.6,sweep)*(1.-smoothstep(2.3,2.8,sweep));
          vColor=mix(vColor,vec3(1.,.87,.60),glint*.30*max(eye,uLogo));
          float chartVisibility=mix(1.,smoothstep(aChart.w-.10,aChart.w+.08,uReveal),uChart);
          vAlpha=(.78+aSeed.z*.22)*(1.-uLogo*(1.-aFlags.y))*chartVisibility;
          float behindEyes=step(abs(aBee.x-uEyeFrame.x),uEyeFrame.z*.55)*step(abs(aBee.y-uEyeFrame.y),uEyeFrame.z*.29)*(1.-aFlags.x);
          vAlpha*=1.-behindEyes*uEye*(1.-uLogo);
          vAlpha*=aFlags.y>.5&&uLogo>0.?smoothstep(0.,.16,uLogo):1.-uMeshVisible;
          vAlpha=max(vAlpha,wake*.34*(1.-uLogo));
          vColor*=1.+ripple*.35;
        }`,
      fragmentShader:`
        varying vec3 vColor; varying float vAlpha;
        void main(){vec2 pixel=abs(gl_PointCoord-.5)*2.;float edge=max(pixel.x,pixel.y);if(edge>.97)discard;
          float core=1.-smoothstep(.78,.92,edge);float halo=(1.-edge)*.055;
          float bevel=.83+.17*(1.-gl_PointCoord.y);
          gl_FragColor=vec4(vColor*bevel,(core+halo)*vAlpha);
        }`,
    });
    const points=new THREE.Points(geometry,material);points.frustumCulled=false;scene.add(points);
    let lastCycle=-1,slowFrames=0,adaptive=false;
    draw=(s,dt)=>{
      if(s.chart>0){
        const chartTime=Math.max(0,cycleTime-durations[0]-durations[1]);
        updateCandles(chartTime);
        for(let i=0;i<count;i++){if(!chartData[i*4])continue;const point=chartPoint(i,chartTime);chart[i*4]=point.x;chart[i*4+1]=point.y;chartColors.set(point.color,i*3);}
        geometry.attributes.aChart.needsUpdate=true;geometry.attributes.aChartColor.needsUpdate=true;
        const active=candleCache[11];canvas.dataset.candleTick=String(Math.floor(chartTime));canvas.dataset.candleClose=active.close.toFixed(4);canvas.dataset.candleHigh=active.high.toFixed(4);canvas.dataset.candleLow=active.low.toFixed(4);canvas.dataset.chartScroll=(chartTime*.18).toFixed(4);
      }
      if(cycle!==lastCycle){geometry.attributes.aScatterA.needsUpdate=true;geometry.attributes.aScatterB.needsUpdate=true;lastCycle=cycle;}
      uniforms.uTime.value=elapsed;uniforms.uBee.value=s.bee;uniforms.uLogo.value=s.logo;uniforms.uEye.value=s.mark;uniforms.uChart.value=s.chart;uniforms.uReveal.value=s.reveal;uniforms.uVariation.value=s.variation;
      uniforms.uPointer.value.set(pointer.x,pointer.y,pointer.strength,.3);uniforms.uRipple.value.set(ripple.x,ripple.y,ripple.start,ripple.strength);
      uniforms.uCycle.value.set(cycleYaw,wingSpeed,flightVariation);
      uniforms.uChartMotion.value.set(Math.max(0,cycleTime-durations[0]-durations[1]),chartDirection,chartSeed);
      uniforms.uSweepTime.value=sweepTime(s);
      meshOpacity=meshAvailable?ease((s.bee-.62)/.32)*(1-ease((s.logo-.90)/.10)):0;
      bodyPixels.uBodyDissolve.value=ease(s.logo/.80);bodyPixels.uBodyDpr.value=renderer.getPixelRatio();
      uniforms.uMeshVisible.value=meshOpacity;mascot.visible=meshOpacity>.001;
      const yaw=cycleYaw+Math.sin(elapsed*.55)*.14+Math.max(-1,Math.min(1,pointer.x-stageX))*pointer.strength*.20;
      const pitch=Math.sin(elapsed*.43)*.075-Math.max(-1,Math.min(1,pointer.y-stageY))*pointer.strength*.10;
      const beeProgress=s.phase==='forming-bee'?0:s.phase==='bee'?s.progress:1;
      const flightProgress=ease(beeProgress/.86),orbit=flightProgress*Math.PI*2,depth=Math.sin(flightProgress*Math.PI);
      const gaze=ease((beeProgress-.72)/.26);
      const flightX=Math.sin(orbit)*.29,flightY=Math.sin(orbit)*.10+(1-Math.cos(orbit))*.085;
      const flightScale=.94-depth*.16;
      mascot.scale.setScalar(flightScale);
      mascot.position.set(stageX+flightX+Math.sin(elapsed*.47)*.025,stageY+flightY+Math.sin(elapsed*.85)*.035,-depth*.60);
      mascot.rotation.set(pitch*(1-gaze*.55)+Math.sin(orbit)*.18,orbit+yaw*(1-gaze*.80),Math.sin(elapsed*.31)*.018-Math.sin(orbit)*.25,'YXZ');
      mascot.updateMatrixWorld(true);uniforms.uMascotMatrix.value.copy(mascot.matrixWorld);
      uniforms.uWake.value=s.phase==='forming-bee'?s.bee*.8:s.phase==='bee'?(1-ease((beeProgress-.72)/.28))*.8:0;
      const wingPhase=elapsed*Math.PI*2*17+Math.sin(elapsed*.8)*.6;
      for(const {pivot,side} of wingPivots){pivot.rotation.y=side*(Math.sin(wingPhase)*.62+.10);pivot.rotation.z=side*Math.sin(wingPhase+.5)*.095;}
      for(const {pivot,side,offset} of wingGhosts){pivot.visible=!staticPreference&&meshOpacity>.001;pivot.rotation.y=side*(Math.sin(wingPhase+offset)*.62+.10);pivot.rotation.z=side*Math.sin(wingPhase+offset+.5)*.095;}
      for(const record of meshMaterials){record.mat.opacity=record.opacity*meshOpacity;record.mat.transparent=record.opacity<1||meshOpacity<.999;record.mat.depthWrite=record.opacity>=1&&meshOpacity>.98;}
      for(const record of eyeMaterials){record.mat.opacity=record.opacity*meshOpacity*(1-ease(s.logo/.16));record.mat.transparent=record.mat.opacity<.999;record.mat.depthWrite=false;record.mat.color.copy(record.color).multiplyScalar(.12+s.mark*.14);record.mat.emissive.copy(record.color);record.mat.emissiveIntensity=.025+s.mark*.34;}
      const parallaxX=pointer.strength*Math.max(-1,Math.min(1,pointer.x-stageX))*.018,parallaxY=pointer.strength*Math.max(-1,Math.min(1,pointer.y-stageY))*.018;
      points.position.set(parallaxX*s.logo,parallaxY*s.logo,0);
      canvas.dataset.bodyStyle='lit-pixel-cells';canvas.dataset.eyeExtraction=s.logo.toFixed(3);canvas.dataset.eyeTiles=String(modelEyes.length);
      canvas.dataset.beeAction=s.phase==='forming-bee'?'assembling':s.phase==='bee'?(beeProgress<.86?'flight':'look'):s.phase==='eyes-light'?'eye-handoff':'idle';canvas.dataset.beeFlight=flightProgress.toFixed(3);canvas.dataset.beeX=mascot.position.x.toFixed(3);canvas.dataset.beeY=mascot.position.y.toFixed(3);canvas.dataset.beeYaw=mascot.rotation.y.toFixed(3);canvas.dataset.beeScale=flightScale.toFixed(3);canvas.dataset.wingHz=staticPreference?'0':'17';
      const growth=clamp((s.logo-.10)/.90),eyeGrowth=growth*growth*(3-2*growth);
      canvas.dataset.eyeWidth=mix(eyeWidth,1.95,eyeGrowth).toFixed(3);canvas.dataset.bodyDissolve=bodyPixels.uBodyDissolve.value.toFixed(3);
      if(dt>.035)slowFrames++;else slowFrames=Math.max(0,slowFrames-1);
      if(!adaptive&&slowFrames>70){adaptive=true;renderer.setPixelRatio(1);uniforms.uDpr.value=1;visibleCount=Math.max(logoCount,Math.floor(count*.7));geometry.setDrawRange(0,visibleCount);canvas.dataset.quality='adaptive';}
      renderer.render(scene,camera);
    };
    resizeEngine=()=>{renderer.setSize(width,height,false);camera.left=-halfW;camera.right=halfW;camera.top=halfH;camera.bottom=-halfH;camera.updateProjectionMatrix();uniforms.uBounds.value.set(halfW,halfH);uniforms.uUnit.value=height/(halfH*2);uniforms.uStage.value.set(stageX,stageY);lightingTarget.position.set(stageX,stageY,0);for(const {light,x,y,z} of lights)light.position.set(stageX+x,stageY+y,z);};
    destroyEngine=()=>{geometry.dispose();material.dispose();normalizedModel.traverse(node=>{if(node.isMesh)node.geometry.dispose();});for(const record of meshMaterials)record.mat.dispose();renderer.dispose();};
    rendererType='webgl';
    on(canvas,'webglcontextlost',event=>{
      event.preventDefault();
      if(destroyed)return;
      contextLost=true;
      if(frame)cancelAnimationFrame(frame);frame=0;
      localPaused=true;paused=true;showStaticFallback();canvas.dataset.renderer='context-lost';
    });
    on(canvas,'webglcontextrestored',()=>{
      if(destroyed)return;
      contextLost=false;
      if(pauseButton)pauseButton.disabled=false;
      resize();sync();
    });
  } catch {
    // A context cannot change from WebGL to 2D; replace only the decorative canvas.
    const replacement=canvas.cloneNode(false);canvas.replaceWith(replacement);canvas=replacement;
    const context=canvas.getContext('2d');
    if(!context){showStaticFallback();return;}
    rendererType='fallback';
    let fallbackMascot=null;
    try{const image=new Image();image.src='/assets/mascot-v4/swarm-mascot-hero.png';await image.decode();fallbackMascot=image;canvas.dataset.mascotGeometry='rendered-image-fallback';}catch{canvas.dataset.mascotGeometry='particle-fallback';}
    const fallbackCount=Math.min(count,900);
    visibleCount=fallbackCount;
    const renderPoints=[];
    function pose(x,y,z,part=0,mark=false){
      if(part===2||part===3){
        const side=Math.sign(x),angle=side*(Math.sin(elapsed*wingSpeed)*.36+.10),xx=x-side*.176,zz=z+.100;
        x=side*.176+xx*Math.cos(angle)+zz*Math.sin(angle);z=-.100-xx*Math.sin(angle)+zz*Math.cos(angle);y+=Math.sin(elapsed*wingSpeed)*Math.abs(xx)*.045;
      }
      const yaw=mark?Math.sin(elapsed*.30)*.075+pointer.strength*Math.max(-1,Math.min(1,pointer.x-stageX))*.13:cycleYaw+Math.sin(elapsed*.55)*.14+Math.max(-1,Math.min(1,pointer.x-stageX))*pointer.strength*.22;
      const pitch=mark?Math.sin(elapsed*.37)*.035-pointer.strength*Math.max(-1,Math.min(1,pointer.y-stageY))*.06:Math.sin(elapsed*.43)*.075-Math.max(-1,Math.min(1,pointer.y-stageY))*pointer.strength*.12;
      const xx=x*Math.cos(yaw)+z*Math.sin(yaw),zz=-x*Math.sin(yaw)+z*Math.cos(yaw);
      const yy=y*Math.cos(pitch)+zz*Math.sin(pitch),depth=-y*Math.sin(pitch)+zz*Math.cos(pitch),projection=mark?1.015:3.8/(3.8-depth);
      return [xx*projection+(mark?0:Math.sin(elapsed*.47)*.023),yy*projection+Math.sin(elapsed*(mark?.6:.85))*(mark?.023:.025),depth];
    }
    resizeEngine=()=>{const dpr=Math.min(devicePixelRatio||1,1.25);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);context.setTransform(dpr,0,0,dpr,0,0);};
    draw=s=>{
      context.clearRect(0,0,width,height);const unit=height/(halfH*2);renderPoints.length=0;
      meshOpacity=fallbackMascot?ease((s.bee-.62)/.32)*(1-ease(s.logo/.55)):0;
      for(let i=0;i<fallbackCount;i++){
        const n=i*3,k=i*4;const arrival=ease((s.bee-seeds[k+3]*.15)/.85),eye=s.mark*flags[n];
        let x=mix(scatterA[n],scatterB[n],s.variation)*halfW*.94;
        x=((x+elapsed*(seeds[k+2]-.5)*.24+halfW)%(2*halfW)+2*halfW)%(2*halfW)-halfW+Math.sin(elapsed*(.40+seeds[k+2]*.45)+seeds[k])*.16;
        let y=mix(scatterA[n+1],scatterB[n+1],s.variation)*halfH*.94+Math.cos(elapsed*(.32+seeds[k+1]*.25)+seeds[k]*2)*.16;
        const cp=chartPoint(i,Math.max(0,cycleTime-durations[0]-durations[1]));
        x=mix(x,cp.x+stageX,s.chart);y=mix(y,cp.y+stageY,s.chart);
        const bp=pose(bee[n],bee[n+1],bee[n+2],parts[i]);
        x=mix(x,bp[0]+stageX,arrival);y=mix(y,bp[1]+stageY,arrival);
        x+=Math.sin(seeds[k]+arrival*6)*Math.sin(arrival*Math.PI)*.22;y+=Math.cos(seeds[k]*2+arrival*8)*Math.sin(arrival*Math.PI)*.22;
        const ep=pose(eyes[n],eyes[n+1],eyes[n+2]);x=mix(x,ep[0]+stageX,eye);y=mix(y,ep[1]+stageY,eye);
        const cloudX=mix(scatterA[n],scatterB[n],s.variation)*halfW,cloudY=mix(scatterA[n+1],scatterB[n+1],s.variation)*halfH;
        const lp=pose(logo[n],logo[n+1],logo[n+2],0,true);
        x=mix(x,mix(cloudX,lp[0]+stageX,flags[n+1]),s.logo);y=mix(y,mix(cloudY,lp[1]+stageY,flags[n+1]),s.logo);
        const breakup=Math.sin(s.logo*Math.PI)*mix(.48,.13,flags[n+1]);
        x+=Math.sin(seeds[k]+s.logo*9)*breakup;y+=Math.cos(seeds[k]*2+s.logo*7)*breakup;
        const dx=x-pointer.x,dy=y-pointer.y,dist=Math.hypot(dx,dy)||1;
        const push=Math.exp(-dist*dist/.12)*pointer.strength*mix(.16,.21,s.logo);x+=dx/dist*push;y+=dy/dist*push;
        const rx=x-ripple.x,ry=y-ripple.y,rd=Math.hypot(rx,ry)||1,age=elapsed-ripple.start;
        const ripplePush=age>=0?Math.exp(-Math.pow((rd-age*.85)*8,2))*Math.exp(-age*1.3)*ripple.strength*.23:0;
        x+=rx/rd*ripplePush;y+=ry/rd*ripplePush;
        let alpha=(.78+seeds[k+2]*.22)*(1-s.logo*(1-flags[n+1]))*mix(1,ease((s.reveal-chart[k+3]+.1)/.18),s.chart);
        if(!flags[n]&&Math.abs(bee[n]-eyeCenter[0])<eyeWidth*.55&&Math.abs(bee[n+1]-eyeCenter[1])<eyeWidth*.29)alpha*=1-s.mark*(1-s.logo);
        alpha*=1-meshOpacity*(1-s.logo);
        const depthLight=.78+clamp((bp[2]+.28)/.65)*.32;
        let color=[1,.55,.11].map((value,j)=>mix(mix(mix(mix(value,cp.color[j],s.chart),beeColors[n+j]*depthLight,arrival),logoColors[n+j],eye),logoColors[n+j],s.logo));
        const sweep=sweepTime(s),glint=Math.exp(-Math.pow((x-stageX-(-1.3+sweep*.95))*7,2))*ease((sweep-.2)/.4)*(1-ease((sweep-2.3)/.5));
        color=color.map((v,j)=>mix(v,[1,.87,.60][j],glint*.30*Math.max(eye,s.logo)));
        const size=mix(mix(2+seeds[k+1]*1.5,Math.max(1.2,eyeCell*unit),eye),Math.max(1.3,logoCell*unit),s.logo*flags[n+1]);
        renderPoints.push({x:width/2+x*unit,y:height/2-y*unit,size,alpha,color});
      }
      context.globalCompositeOperation='source-over';
      for(const p of renderPoints){if(p.alpha<.01)continue;context.fillStyle=`rgba(${p.color.map(value=>Math.round(value*255)).join(',')},${p.alpha})`;context.fillRect(p.x-p.size*.43,p.y-p.size*.43,p.size*.86,p.size*.86);}
      if(fallbackMascot&&meshOpacity>.001){context.globalAlpha=meshOpacity;const size=unit*2.15;context.drawImage(fallbackMascot,width/2+stageX*unit-size/2,height/2-stageY*unit-size/2,size,size);context.globalAlpha=1;}
    };
    destroyEngine=()=>{};
  }

  function showStaticFallback(){
    art.classList.remove('is-rendered');
    canvas.dataset.renderer='static';canvas.dataset.phase='logo';canvas.dataset.motion='paused';
    if(pauseButton){pauseButton.textContent='Static artwork';pauseButton.disabled=true;pauseButton.setAttribute('aria-pressed','true');}
    if(stirButton)stirButton.disabled=true;
  }
  function report(s){
    canvas.dataset.phase=s.phase;canvas.dataset.cycle=String(cycle);canvas.dataset.renderer=rendererType;
    canvas.dataset.motion=paused?'paused':'playing';canvas.dataset.particles=String(visibleCount);
    canvas.dataset.modelSource=modelSource;canvas.dataset.chart='illustrative';canvas.dataset.logoGeometry='particles';
    canvas.dataset.eyeMark=s.mark>.95?'lit':s.mark>0?'lighting':'off';canvas.dataset.frame=String(frames);
    canvas.dataset.reducedMotion=String(staticPreference);
    canvas.dataset.chartDirection='rising-path-alternating-candles';canvas.dataset.chartReveal=s.reveal.toFixed(2);
    canvas.dataset.chartTime=Math.max(0,cycleTime-durations[0]-durations[1]).toFixed(2);
    canvas.dataset.meshOpacity=meshOpacity.toFixed(2);canvas.dataset.chartTick=String(Math.floor(Math.max(0,cycleTime-durations[0]-durations[1])));
  }
  function render(dt=0){if(contextLost||destroyed)return;const s=state();draw(s,dt);frames++;if(Math.floor(elapsed*4)!==lastReport||paused){report(s);lastReport=Math.floor(elapsed*4);}art.classList.add('is-rendered');}
  function resize(){
    if(contextLost||destroyed)return;
    const rect=canvas.getBoundingClientRect(),stage=art.getBoundingClientRect();
    width=Math.max(1,rect.width);height=Math.max(1,rect.height);
    // Desktop CSS intentionally extends the canvas past the stage for loose swarm
    // particles. Fit formed silhouettes to the visible stage, not that overscan.
    const visualHeight=Math.max(140,stage.height-64);
    const unit=Math.max(1,Math.min(stage.width/2.22,visualHeight/2.02));
    halfW=width/(2*unit);halfH=height/(2*unit);
    stageX=(stage.left+stage.width/2-rect.left-rect.width/2)/unit;
    stageY=(rect.top+rect.height/2-stage.top-visualHeight/2-8)/unit;
    resizeEngine();render();
  }
  function nextCycle(){
    cycleTime-=durations.reduce((sum,d)=>sum+d,0);cycle++;
    scatterA.set(scatterB);scatterFill(scatterB);
    cycleYaw=(random()-.5)*.36;wingSpeed=4+random()*3;flightVariation=.72+random()*.65;
    chartDirection*=-1;chartSeed=random()*6;chartCacheTime=-1;
    durations=[1.8+random()*.8,2.8+random()*.8,11,3.5+random(),4.7+random()*.8,2.7+random()*.8,4.5+random(),4.5+random(),4.5+random()];
    canvas.dataset.variant=String(Math.floor(random()*1e9));
  }
  function tick(time){
    frame=0;if(destroyed||contextLost||paused||!visible||document.hidden)return;
    if(!previous)previous=time;
    const dt=(time-previous)/1000;
    const interval=coarse||constrained?1/30:1/60;
    if(dt>=interval-.002){previous=time;const step=Math.min(dt,.08);elapsed+=step;cycleTime+=step;pointer.strength=mix(pointer.strength,pointer.target,1-Math.exp(-step*6));if(cycleTime>=durations.reduce((sum,d)=>sum+d,0))nextCycle();render(dt);}
    frame=requestAnimationFrame(tick);
  }
  function sync(){
    if(frame)cancelAnimationFrame(frame);frame=0;previous=0;
    if(contextLost){showStaticFallback();canvas.dataset.renderer='context-lost';return;}
    if(pauseButton){pauseButton.textContent=globalPaused?'Motion paused':paused?'Play animation':'Pause animation';pauseButton.disabled=globalPaused;pauseButton.setAttribute('aria-pressed',String(paused));}
    if(stirButton){stirButton.disabled=paused;stirButton.title=paused?'Play the animation to stir the swarm':'Send a ripple through the swarm';}
    report(state());
    if(!paused&&visible&&!document.hidden&&!destroyed)frame=requestAnimationFrame(tick);
  }
  function locate(event){const rect=canvas.getBoundingClientRect();pointer.x=((event.clientX-rect.left)/rect.width*2-1)*halfW;pointer.y=(1-(event.clientY-rect.top)/rect.height*2)*halfH;}
  function stir(x=0,y=0){if(paused)return;ripple.x=x;ripple.y=y;ripple.start=elapsed;ripple.strength=1;canvas.dataset.interaction='ripple';}
  on(animationRegion,'pointermove',event=>{locate(event);pointer.target=1;},{passive:true});
  on(animationRegion,'pointerleave',()=>{pointer.target=0;},{passive:true});
  on(animationRegion,'pointercancel',()=>{pointer.target=0;touchStart=null;},{passive:true});
  on(animationRegion,'pointerdown',event=>{locate(event);pointer.target=1;touchStart={x:event.clientX,y:event.clientY,time:performance.now()};},{passive:true});
  on(animationRegion,'pointerup',event=>{if(touchStart&&Math.hypot(event.clientX-touchStart.x,event.clientY-touchStart.y)<12&&performance.now()-touchStart.time<550){locate(event);stir(pointer.x,pointer.y);}touchStart=null;if(event.pointerType!=='mouse')pointer.target=0;},{passive:true});
  on(window,'blur',()=>{pointer.target=0;touchStart=null;});
  if(stirButton)on(stirButton,'click',()=>stir());
  if(pauseButton)on(pauseButton,'click',()=>{if(globalPaused)return;if(paused&&staticPreference){staticPreference=false;cycleTime=0;elapsed=0;}localPaused=!localPaused;paused=localPaused;sync();render();});
  on(window,'swarm:motion',event=>{globalPaused=Boolean(event.detail?.paused);paused=localPaused||globalPaused;sync();render();});
  on(reduced,'change',event=>{staticPreference=event.matches;if(event.matches){localPaused=true;paused=true;pointer.target=0;pointer.strength=0;render();}sync();});
  on(document,'visibilitychange',sync);
  if('IntersectionObserver'in window){const observer=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;canvas.dataset.visibility=visible?'visible':'offscreen';sync();},{rootMargin:'40px'});observer.observe(animationRegion);cleanups.push(()=>observer.disconnect());}
  if('ResizeObserver'in window){const observer=new ResizeObserver(resize);observer.observe(art);if(animationRegion!==art)observer.observe(animationRegion);cleanups.push(()=>observer.disconnect());}else on(window,'resize',resize);
  on(window,'pagehide',event=>{if(event.persisted){visible=false;sync();return;}destroyed=true;if(frame)cancelAnimationFrame(frame);cleanups.splice(0).forEach(cleanup=>cleanup());destroyEngine();});
  on(window,'pageshow',event=>{if(event.persisted){visible=true;sync();}});
  globalPaused=Boolean(window.swarmMotionPaused);paused=localPaused||globalPaused;
  resize();sync();
}
