/* A small copy of the real GLB acts as the fine-pointer cursor. No input capture. */
(() => {
  'use strict';
  const fine = matchMedia('(hover: hover) and (pointer: fine)');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  if (!fine.matches || reduce.matches || !document.body.classList.contains('redesign')) return;
  let started = false, disposed = false, inside = false, field = false, paused = false, ready = false, contextLost = false;
  let shell, renderer, scene, camera, mascot, frame = 0, last = 0, time = 0;
  let x = 0, y = 0, dx = 0, dy = 0, angle = 0, pulse = 0;
  const wings = [], resources = new Set();
  const allowed = () => inside && !field && fine.matches && !reduce.matches && !paused && !document.hidden && !disposed && !contextLost;
  function sync() {
    paused = Boolean(window.swarmMotionPaused) || document.documentElement.dataset.swarmMotion === 'paused';
    const run = ready && allowed();
    document.documentElement.classList.toggle('bee-pointer-ready', run);
    if (shell) shell.hidden = !run;
    if (run && !frame) frame = requestAnimationFrame(draw);
    if (!run) { cancelAnimationFrame(frame); frame = 0; last = 0; }
  }
  function draw(now) {
    frame = 0;
    if (!allowed()) { sync(); return; }
    frame = requestAnimationFrame(draw);
    if (last && now-last < 24) return;
    const dt = last ? Math.min((now-last)/1000, .08) : 0;
    last = now; time += dt;
    angle += (Math.max(-.45, Math.min(.45, -dx*.018))-angle)*.18;
    mascot.rotation.set(Math.max(-.16, Math.min(.16, dy*.009)), Math.sin(time*1.7)*.18, angle);
    mascot.position.y = Math.sin(time*7)*.025;
    const wingBeat = Math.sin(time*Math.PI*2*17);
    wings.forEach(({pivot, side}) => { pivot.rotation.z = side*(.11+wingBeat*.29); pivot.rotation.y = side*wingBeat*.28; });
    pulse = Math.max(0, pulse-dt*3);
    mascot.scale.setScalar(1+pulse*.08);
    renderer.render(scene,camera);
    shell.dataset.frame = String(Number(shell.dataset.frame||0)+1);
    dx *= .82; dy *= .82;
  }
  async function init() {
    if (started || disposed) return;
    started = true;
    try {
      const THREE = await import('./vendor/three.module.min.js');
      const {GLTFLoader} = await import('./vendor/GLTFLoader.js');
      if (disposed || reduce.matches || !fine.matches) return;
      shell = document.createElement('div'); shell.className = 'bee-pointer'; shell.hidden = true; shell.setAttribute('aria-hidden','true');
      const canvas = document.createElement('canvas'); shell.append(canvas); document.body.append(shell);
      renderer = new THREE.WebGLRenderer({canvas,alpha:true,antialias:true,powerPreference:'low-power'});
      renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.25)); renderer.setSize(72,72); renderer.setClearColor(0,0);
      scene = new THREE.Scene(); camera = new THREE.OrthographicCamera(-1.08,1.08,1.08,-1.08,.1,15); camera.position.z = 4;
      scene.add(new THREE.AmbientLight(0xffd5a0,1.7));
      const light = new THREE.DirectionalLight(0xfff0cf,3.4); light.position.set(-2,3,4); scene.add(light);
      const rim = new THREE.DirectionalLight(0xff8a1f,2); rim.position.set(3,1,-1); scene.add(rim);
      mascot = new THREE.Group(); scene.add(mascot);
      const normalized = new THREE.Group(); normalized.scale.setScalar(1/1.7); normalized.position.y = -.03/1.7; mascot.add(normalized);
      const response = await fetch('/assets/mascot-v4/swarm-mascot.glb');
      if (!response.ok) throw new Error('Mascot unavailable');
      const gltf = await new GLTFLoader().parseAsync(await response.arrayBuffer(),'/assets/mascot-v4/');
      if (disposed) { renderer.dispose(); return; }
      normalized.add(gltf.scene);
      for (const side of [-1,1]) {
        const label = side<0?'left':'right', pivot = new THREE.Group();
        pivot.position.set(side*.30,.22,-.17); gltf.scene.add(pivot); gltf.scene.updateMatrixWorld(true);
        const nodes = gltf.scene.children.filter(node=>node!==pivot && node.name.toLowerCase().startsWith(label) && /(upper.*wing|lower.*wing|honeycomb.*vein|primary.*flight.*spar)/i.test(node.name));
        nodes.forEach(node=>pivot.attach(node)); wings.push({pivot,side});
      }
      gltf.scene.traverse(node=>{if(node.geometry)resources.add(node.geometry); if(node.material)for(const material of [].concat(node.material))resources.add(material);});
      shell.dataset.engine = 'three.js actual mascot'; shell.style.transform = `translate3d(${x}px,${y}px,0)`; ready = true;
      canvas.addEventListener('webglcontextlost', event=>{event.preventDefault();contextLost=true;sync();});
      canvas.addEventListener('webglcontextrestored',()=>{contextLost=false;sync();});
      sync();
    } catch (_) {
      renderer?.dispose(); renderer = null; shell?.remove(); shell = null;
      document.documentElement.classList.remove('bee-pointer-ready');
    }
  }
  document.addEventListener('pointermove', event=>{
    if(event.pointerType !== 'mouse') return;
    dx = event.clientX-x; dy = event.clientY-y; x=event.clientX; y=event.clientY; inside=true;
    field = Boolean(event.target.closest('input,textarea,select,[contenteditable="true"],[role="textbox"]'));
    if(shell) { shell.style.transform=`translate3d(${x}px,${y}px,0)`; shell.classList.toggle('bee-pointer-link',Boolean(event.target.closest('a,button,summary'))); }
    init(); sync();
  },{passive:true});
  document.addEventListener('pointerdown',event=>{if(event.pointerType==='mouse')pulse=1;},{passive:true});
  document.documentElement.addEventListener('pointerleave',()=>{inside=false;sync();},{passive:true});
  window.addEventListener('blur',()=>{inside=false;sync();});
  window.addEventListener('swarm:motion',sync);
  document.addEventListener('visibilitychange',sync);
  fine.addEventListener('change',sync); reduce.addEventListener('change',sync);
  window.addEventListener('pagehide',event=>{
    if(event.persisted){inside=false;sync();return;}
    disposed=true;cancelAnimationFrame(frame);document.documentElement.classList.remove('bee-pointer-ready');
    resources.forEach(resource=>resource.dispose());renderer?.dispose();shell?.remove();
  });
})();
