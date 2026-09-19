import * as T from 'https://cdn.jsdelivr.net/npm/three@0.180.0/+esm';
const host=document.getElementById('ye-popper-canvas'),push=document.getElementById('ye-popper-push'),status=document.getElementById('ye-popper-status');
const scene=new T.Scene();scene.background=new T.Color(0xffffff);
const camera=new T.PerspectiveCamera(34,1,.1,100);camera.position.set(10.4,11.6,14.4);camera.lookAt(0,-.05,0);
const r=new T.WebGLRenderer({antialias:true});r.setPixelRatio(Math.min(2,devicePixelRatio||1));r.shadowMap.enabled=true;host.appendChild(r.domElement);
scene.add(new T.HemisphereLight(0xffffff,0x888888,2.8));const dl=new T.DirectionalLight(0xffffff,3.8);dl.position.set(-5,10,6);dl.castShadow=true;scene.add(dl);
const ground=new T.Mesh(new T.PlaneGeometry(30,30),new T.ShadowMaterial({opacity:.12}));ground.rotation.x=-Math.PI/2;ground.position.y=-1.19;ground.receiveShadow=true;scene.add(ground);
const sm=(c,m=.25,q=.35)=>new T.MeshStandardMaterial({color:c,metalness:m,roughness:q});
function mesh(g,m,y){const x=new T.Mesh(g,m);x.position.y=y;x.castShadow=x.receiveShadow=true;scene.add(x);return x}
mesh(new T.CylinderGeometry(4.5,4.8,1.15,64),sm(0xd85b61,.28,.3),-.6);
mesh(new T.CylinderGeometry(4.78,4.72,.18,64),sm(0xb94450,.24,.34),-1.12);
mesh(new T.CylinderGeometry(4.05,4.05,.13,64),sm(0xc8d82e,0,.9),.01);
const ring=mesh(new T.TorusGeometry(4.12,.14,16,72),sm(0x27a8c6,.32,.27),.08);ring.rotation.x=Math.PI/2;
const dome=mesh(new T.SphereGeometry(4.15,64,32,0,Math.PI*2,0,Math.PI/2),new T.MeshPhysicalMaterial({color:0xffffff,transparent:true,opacity:.14,roughness:.025,transmission:.38,thickness:.1,ior:1.45,side:T.DoubleSide,depthWrite:false}),.08);
const dm=new T.MeshPhysicalMaterial({color:0xeadbb9,roughness:.34,clearcoat:.28,clearcoatRoughness:.3});
const spots={1:[[0,0]],2:[[-1,-1],[1,1]],3:[[-1,-1],[0,0],[1,1]],4:[[-1,-1],[1,-1],[-1,1],[1,1]],5:[[-1,-1],[1,-1],[0,0],[-1,1],[1,1]],6:[[-1,-1],[1,-1],[-1,0],[1,0],[-1,1],[1,1]]};
const faces=[[0,1,0,1],[0,-1,0,6],[1,0,0,3],[-1,0,0,4],[0,0,1,5],[0,0,-1,2]],Z=new T.Vector3(0,0,1);
function die(x){const g=new T.Group(),cube=new T.Mesh(new T.BoxGeometry(1.02,1.02,1.02,5,5,5),dm);cube.castShadow=true;g.add(cube);
 for(const [nx,ny,nz,num] of faces){const n=new T.Vector3(nx,ny,nz),up=Math.abs(n.y)>.5?new T.Vector3(0,0,-1):new T.Vector3(0,1,0),right=new T.Vector3().crossVectors(up,n).normalize(),vert=new T.Vector3().crossVectors(n,right).normalize();
  for(const [a,b] of spots[num]){const p=new T.Mesh(new T.CircleGeometry(.073,18),new T.MeshBasicMaterial({color:0x4a2b1b,side:T.DoubleSide}));p.position.copy(n).multiplyScalar(.516).addScaledVector(right,a*.205).addScaledVector(vert,b*.205);p.quaternion.setFromUnitVectors(Z,n);g.add(p)}}
 g.scale.setScalar(1.15);g.position.set(x,1.3,0);scene.add(g);return{m:g,v:new T.Vector3(),w:new T.Vector3(),t:0,rest:false}}
const dice=[die(-.65),die(.65)],F=.69,R=3.34;let rolling=false,last=performance.now(),audio;
function reset(d,i){d.rest=false;d.t=0;d.m.position.set(i?.65:-.65,1.25+Math.random()*.3,(Math.random()-.5)*.6);d.m.rotation.set(Math.random()*6,Math.random()*6,Math.random()*6);d.v.set((Math.random()-.5)*5.3,7.8+Math.random()*1.9,(Math.random()-.5)*5.3);d.w.set((Math.random()-.5)*18,(Math.random()-.5)*18,(Math.random()-.5)*18)}
function h(style){try{window.Capacitor?.Plugins?.Haptics?.impact({style})}catch(e){}}
function snd(){audio||=new(window.AudioContext||window.webkitAudioContext)();const t=audio.currentTime,o=audio.createOscillator(),g=audio.createGain();o.frequency.setValueAtTime(92,t);o.frequency.exponentialRampToValueAtTime(58,t+.08);g.gain.setValueAtTime(.24,t);g.gain.exponentialRampToValueAtTime(.001,t+.095);o.connect(g).connect(audio.destination);o.start();o.stop(t+.1)}
function pop(){if(rolling)return;rolling=true;push.disabled=true;dice.forEach(reset);h('LIGHT');snd();const s=performance.now();(function a(){const x=performance.now()-s;if(x<150){let k=x/150;dome.scale.set(1-.1*k,1-.27*k,1-.1*k);dome.position.y=.08-.2*k}else{let k=Math.min(1,(x-150)/230),e=1-(1-k)**3;dome.scale.set(.9+.1*e,.73+.27*e,.9+.1*e);dome.position.y=-.12+.2*e}if(x<380)requestAnimationFrame(a);else{dome.scale.set(1,1,1);dome.position.y=.08}})();setTimeout(()=>h('HEAVY'),170)}
function step(dt){for(const d of dice){if(d.rest)continue;d.t+=dt;d.v.y-=9.8*dt;d.m.position.addScaledVector(d.v,dt);const a=d.w.length()*dt;if(a)d.m.quaternion.premultiply(new T.Quaternion().setFromAxisAngle(d.w.clone().normalize(),a));
 const rad=Math.hypot(d.m.position.x,d.m.position.z);if(rad>R){const n=new T.Vector3(d.m.position.x,0,d.m.position.z).normalize();d.m.position.x=n.x*R;d.m.position.z=n.z*R;const out=d.v.dot(n);if(out>0)d.v.addScaledVector(n,-1.72*out);d.v.multiplyScalar(.96)}
 if(d.m.position.y<F){d.m.position.y=F;if(d.v.y<0)d.v.y=-d.v.y*.5;d.v.x*=.915;d.v.z*=.915;d.w.multiplyScalar(.84)}
 if(d.t>.38&&d.m.position.y<=F+.035&&Math.abs(d.v.y)<.32&&Math.hypot(d.v.x,d.v.z)<.34&&d.w.length()<1.9){d.rest=true;d.v.set(0,0,0);d.w.set(0,0,0)}}
 if(rolling&&dice.every(d=>d.rest)){rolling=false;push.disabled=false;status.textContent='Roll complete · native haptics active'}}
function resize(){const w=host.clientWidth||innerWidth,h=host.clientHeight||innerHeight;r.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}addEventListener('resize',resize);resize();
push.onclick=pop;r.domElement.onclick=pop;(function frame(n){const dt=Math.min(.024,(n-last)/1000)*1.2;last=n;if(rolling)step(dt);r.render(scene,camera);requestAnimationFrame(frame)})(performance.now());