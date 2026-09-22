import * as T from 'https://cdn.jsdelivr.net/npm/three@0.180.0/+esm';

const host=document.getElementById('stage'), miniHost=document.getElementById('miniStage'), push=document.getElementById('push'), status=document.getElementById('status'), rollread=document.getElementById('rollread');
const scene=new T.Scene(); scene.background=new T.Color(0xffffff);
const camera=new T.PerspectiveCamera(34,1,.1,100);
camera.position.set(7.6,8.5,10.5); camera.lookAt(0,-.05,0);
const r=new T.WebGLRenderer({antialias:true,alpha:false}); r.setPixelRatio(Math.min(2,devicePixelRatio||1)); r.shadowMap.enabled=true; host.appendChild(r.domElement); const miniR=new T.WebGLRenderer({antialias:true,alpha:false}); miniR.setPixelRatio(Math.min(2,devicePixelRatio||1)); miniR.shadowMap.enabled=true; if(miniHost)miniHost.appendChild(miniR.domElement);
scene.add(new T.HemisphereLight(0xffffff,0x888888,2.8));
const dl=new T.DirectionalLight(0xffffff,3.8); dl.position.set(-5,10,6); dl.castShadow=true; scene.add(dl);
const ground=new T.Mesh(new T.PlaneGeometry(30,30),new T.ShadowMaterial({opacity:.12})); ground.rotation.x=-Math.PI/2; ground.position.y=-1.19; ground.receiveShadow=true; scene.add(ground);
const sm=(c,m=.25,q=.35)=>new T.MeshStandardMaterial({color:c,metalness:m,roughness:q});
function mesh(g,m,y){const x=new T.Mesh(g,m);x.position.y=y;x.castShadow=x.receiveShadow=true;scene.add(x);return x}
mesh(new T.CylinderGeometry(4.5,4.8,1.15,64),sm(0xd85b61,.28,.3),-.6);
mesh(new T.CylinderGeometry(4.78,4.72,.18,64),sm(0xb94450,.24,.34),-1.12);
mesh(new T.CylinderGeometry(4.05,4.05,.13,64),sm(0xc8d82e,0,.9),.01);
const ring=mesh(new T.TorusGeometry(4.12,.14,16,72),sm(0x27a8c6,.32,.27),.08); ring.rotation.x=Math.PI/2;
const dome=mesh(new T.SphereGeometry(4.15,64,32,0,Math.PI*2,0,Math.PI/2),new T.MeshPhysicalMaterial({color:0xffffff,transparent:true,opacity:.14,roughness:.025,transmission:.38,thickness:.1,ior:1.45,side:T.DoubleSide,depthWrite:false}),.08);
const dm=new T.MeshPhysicalMaterial({color:0xeadbb9,roughness:.34,clearcoat:.28,clearcoatRoughness:.3});
const spots={1:[[0,0]],2:[[-1,-1],[1,1]],3:[[-1,-1],[0,0],[1,1]],4:[[-1,-1],[1,-1],[-1,1],[1,1]],5:[[-1,-1],[1,-1],[0,0],[-1,1],[1,1]],6:[[-1,-1],[1,-1],[-1,0],[1,0],[-1,1],[1,1]]};
const faces=[[0,1,0,1],[0,-1,0,6],[1,0,0,3],[-1,0,0,4],[0,0,1,5],[0,0,-1,2]],Z=new T.Vector3(0,0,1);
function roundedBox(size=1.02,radius=.14,segments=6){const g=new T.BoxGeometry(size,size,size,segments,segments,segments),p=g.attributes.position,half=size/2,inner=half-radius,v=new T.Vector3(),q=new T.Vector3();for(let i=0;i<p.count;i++){v.fromBufferAttribute(p,i);q.set(T.MathUtils.clamp(v.x,-inner,inner),T.MathUtils.clamp(v.y,-inner,inner),T.MathUtils.clamp(v.z,-inner,inner));v.sub(q).normalize().multiplyScalar(radius).add(q);p.setXYZ(i,v.x,v.y,v.z)}p.needsUpdate=true;g.computeVertexNormals();return g}
function die(x){const g=new T.Group(),cube=new T.Mesh(roundedBox(),dm);cube.castShadow=true;g.add(cube);for(const [nx,ny,nz,num] of faces){const n=new T.Vector3(nx,ny,nz),up=Math.abs(n.y)>.5?new T.Vector3(0,0,-1):new T.Vector3(0,1,0),right=new T.Vector3().crossVectors(up,n).normalize(),vert=new T.Vector3().crossVectors(n,right).normalize();for(const [a,b] of spots[num]){const sh=new T.Mesh(new T.CircleGeometry(.093,18),new T.MeshBasicMaterial({color:0x5a3925,transparent:true,opacity:.38,side:T.DoubleSide}));sh.position.copy(n).multiplyScalar(.516).addScaledVector(right,a*.205).addScaledVector(vert,b*.205);sh.quaternion.setFromUnitVectors(Z,n);g.add(sh);const p=new T.Mesh(new T.CircleGeometry(.071,18),new T.MeshBasicMaterial({color:0x4a2b1b,side:T.DoubleSide}));p.position.copy(n).multiplyScalar(.518).addScaledVector(right,a*.205).addScaledVector(vert,b*.205);p.quaternion.setFromUnitVectors(Z,n);g.add(p)}}g.scale.setScalar(1.15);g.position.set(x,1.3,0);scene.add(g);return{m:g,v:new T.Vector3(),w:new T.Vector3(),t:0,rest:false}}
const dice=[die(-.65),die(.65)],F=.69,DR=4.02,RR=.68; let rolling=false,last=performance.now(),audio;
function haptic(style){try{if(window.webkit?.messageHandlers?.popperHaptic){window.webkit.messageHandlers.popperHaptic.postMessage(style);return}const H=window.Capacitor?.Plugins?.Haptics;if(H?.impact){H.impact({style});return}if(navigator.vibrate)navigator.vibrate(style==='HEAVY'?45:18)}catch(e){}}
function reset(d,i){d.rest=false;d.t=0;d.m.position.set(i?.65:-.65,1.25+Math.random()*.3,(Math.random()-.5)*.6);d.m.rotation.set(Math.random()*6,Math.random()*6,Math.random()*6);d.v.set((Math.random()-.5)*5.3,7.8+Math.random()*1.9,(Math.random()-.5)*5.3);d.w.set((Math.random()-.5)*18,(Math.random()-.5)*18,(Math.random()-.5)*18)}
function compressionSound(){
 audio||=new(window.AudioContext||window.webkitAudioContext)();if(audio.state==='suspended')audio.resume();
 const t=audio.currentTime,o=audio.createOscillator(),g=audio.createGain();o.type='sine';o.frequency.setValueAtTime(105,t);o.frequency.exponentialRampToValueAtTime(62,t+.13);g.gain.setValueAtTime(.19,t);g.gain.exponentialRampToValueAtTime(.001,t+.14);o.connect(g).connect(audio.destination);o.start(t);o.stop(t+.145);
}
function releaseSound(){
 audio||=new(window.AudioContext||window.webkitAudioContext)();const t=audio.currentTime;
 const len=Math.floor(audio.sampleRate*.07),buf=audio.createBuffer(1,len,audio.sampleRate),data=buf.getChannelData(0);for(let i=0;i<len;i++){const e=1-i/len;data[i]=(Math.random()*2-1)*e}
 const src=audio.createBufferSource(),bp=audio.createBiquadFilter(),ng=audio.createGain();src.buffer=buf;bp.type='bandpass';bp.frequency.setValueAtTime(1450,t);bp.Q.value=.8;ng.gain.setValueAtTime(.24,t);ng.gain.exponentialRampToValueAtTime(.001,t+.065);src.connect(bp).connect(ng).connect(audio.destination);src.start(t);
 const o=audio.createOscillator(),g=audio.createGain();o.type='triangle';o.frequency.setValueAtTime(390,t);o.frequency.exponentialRampToValueAtTime(155,t+.085);g.gain.setValueAtTime(.18,t);g.gain.exponentialRampToValueAtTime(.001,t+.09);o.connect(g).connect(audio.destination);o.start(t);o.stop(t+.095);
}
function pop(){if(rolling)return;audio||=new(window.AudioContext||window.webkitAudioContext)();if(audio.state==='suspended')audio.resume();rolling=true;push.disabled=true;status.textContent='Rolling…';dice.forEach(reset);
 if(window.webkit?.messageHandlers?.popperFX) window.webkit.messageHandlers.popperFX.postMessage('compress'); else {compressionSound();haptic('LIGHT')}
 const start=performance.now(),releaseAt=150;let released=false;
 (function a(){const x=performance.now()-start;if(x<releaseAt){const k=x/releaseAt;dome.scale.set(1-.1*k,1-.27*k,1-.1*k);dome.position.y=.08-.2*k}else{if(!released){released=true;if(window.webkit?.messageHandlers?.popperFX) window.webkit.messageHandlers.popperFX.postMessage('release'); else {releaseSound();haptic('HEAVY')}}const k=Math.min(1,(x-releaseAt)/230),e=1-(1-k)**3;dome.scale.set(.9+.1*e,.73+.27*e,.9+.1*e);dome.position.y=-.12+.2*e}if(x<380)requestAnimationFrame(a);else{dome.scale.set(1,1,1);dome.position.y=.08}})()}
function step(dt){for(const d of dice){if(d.rest===true)continue;if(d.rest==='settling'){d.settleT+=dt;d.m.position.y=T.MathUtils.lerp(d.m.position.y,F,Math.min(1,12.034*dt));const ang=d.m.quaternion.angleTo(d.targetQ);d.m.quaternion.slerp(d.targetQ,Math.min(1,dt*(4.125+Math.max(0,.45-ang)*3.4375)));if(ang<=.009&&d.settleT>=.291){d.m.position.y=F;d.m.quaternion.copy(d.targetQ);d.v.set(0,0,0);d.w.set(0,0,0);d.rest=true}continue}d.t+=dt;d.v.y-=9.8*dt;d.m.position.addScaledVector(d.v,dt);const a=d.w.length()*dt;if(a)d.m.quaternion.premultiply(new T.Quaternion().setFromAxisAngle(d.w.clone().normalize(),a));const cx=d.m.position.x,cy=d.m.position.y-.08,cz=d.m.position.z,rad3=Math.hypot(cx,cy,cz),limit=DR-RR;
 if(cy>=0&&rad3>limit){const n=new T.Vector3(cx,cy,cz).normalize();d.m.position.set(n.x*limit,n.y*limit+.08,n.z*limit);const out=d.v.dot(n);if(out>0)d.v.addScaledVector(n,-1.72*out);d.v.multiplyScalar(.96)}if(d.m.position.y<F){d.m.position.y=F;if(d.v.y<0)d.v.y=-d.v.y*.50;d.v.x*=.915;d.v.z*=.915;d.w.multiplyScalar(.84)}if(d.t>.55&&d.w.length()<5.2){d.w.x+=(Math.random()-.5)*1.15*dt;d.w.z+=(Math.random()-.5)*1.15*dt}if(d.m.position.y<F+.22){const pr=T.MathUtils.clamp((F+.22-d.m.position.y)/.22,0,1);d.w.multiplyScalar(Math.pow(.14,dt*pr))}if(d.t>.38&&d.m.position.y<=F+.035&&Math.abs(d.v.y)<.32&&Math.hypot(d.v.x,d.v.z)<.34&&d.w.length()<1.9){
  d.v.multiplyScalar(.12);d.w.multiplyScalar(.08);
  const ups=[new T.Vector3(0,1,0),new T.Vector3(0,-1,0),new T.Vector3(1,0,0),new T.Vector3(-1,0,0),new T.Vector3(0,0,1),new T.Vector3(0,0,-1)];
  let best=ups[0],score=-99;for(const n of ups){const wn=n.clone().applyQuaternion(d.m.quaternion),sc=wn.y;if(sc>score){score=sc;best=n}}
  const current=best.clone().applyQuaternion(d.m.quaternion),fix=new T.Quaternion().setFromUnitVectors(current,new T.Vector3(0,1,0));
  d.targetQ=fix.multiply(d.m.quaternion.clone());d.settleT=0;d.rest='settling';
 }
 }if(rolling&&dice.every(d=>d.rest===true)){rolling=false;push.disabled=false;status.textContent='Roll complete';const vals=dice.map(topFaceValue);if(rollread)rollread.textContent=`🎲 ${vals[0]} + ${vals[1]} = ${vals[0]+vals[1]}`}}
function topFaceValue(d){let best=faces[0],score=-99;for(const f of faces){const n=new T.Vector3(f[0],f[1],f[2]).applyQuaternion(d.m.quaternion);if(n.y>score){score=n.y;best=f}}return best[3]}
function resize(){const side=Math.max(1,Math.round(Math.min(host.clientWidth||innerWidth,host.clientHeight||innerWidth,620)));r.setSize(side,side,false);r.domElement.style.width='100%';r.domElement.style.height='100%';if(miniHost){const ms=Math.max(1,Math.round(Math.min(miniHost.clientWidth,miniHost.clientHeight)));miniR.setSize(ms,ms,false);miniR.domElement.style.width='100%';miniR.domElement.style.height='100%'}camera.aspect=1;camera.updateProjectionMatrix()}
function loop(now){const dt=Math.min(.024,(now-last)/1000)*1.2;last=now;step(dt);r.render(scene,camera);if(miniHost)miniR.render(scene,camera);requestAnimationFrame(loop)}
addEventListener('resize',resize);resize();push.onclick=pop;host.onclick=pop;if(miniHost)miniHost.onclick=pop;requestAnimationFrame(loop);