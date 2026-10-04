// Run with node --test tests/test_page.js. No browser or network connection.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const html=fs.readFileSync(path.join(__dirname,'..','Browser-Region-SelfCheck.html'),'utf8');
const code=html.match(/<script>([\s\S]*?)<\/script>/)[1];

function page(rtc){
  const elements=new Map();
  function element(){return {textContent:'',disabled:false,children:[],append(...items){this.children.push(...items);},replaceChildren(){this.children=[];},click(){},getContext(){return null;}};}
  const document={getElementById(id){if(!elements.has(id))elements.set(id,element());return elements.get(id);},createElement:element};
  const window={};if(rtc)window.RTCPeerConnection=rtc;
  const context=vm.createContext({document,window,RTCPeerConnection:rtc,location:{origin:'null',protocol:'file:',hostname:''},navigator:{language:'zh-CN',languages:['ja','en'],platform:'Test'},screen:{width:1280,height:720,colorDepth:24},Intl,Date,Array,JSON,TextEncoder,Uint8Array,Error,Blob,URL,setTimeout,clearTimeout});
  vm.runInContext(code,context);
  return {elements,read:()=>JSON.parse(elements.get('result').textContent)};
}

test('file mode renders expectations without fetching headers',async()=>{
  const p=page();await new Promise(resolve=>setImmediate(resolve));
  assert.equal(p.read().expectations.timeZone,'Asia/Tokyo');
  assert.match(p.read().requestHeaders,/直接打开文件/);
  assert.equal(p.elements.get('summary').children.length,4);
});

test('missing WebRTC API reports failure and re-enables button',async()=>{
  const p=page();await p.elements.get('rtc').onclick();
  assert.equal(p.read().webRTC.status,'检查失败');
  assert.equal(p.elements.get('rtc').disabled,false);
  assert.match(p.read().webRTC.errors[0].text,/RTCPeerConnection/);
});

test('WebRTC constructor failure does not leave checking state',async()=>{
  const p=page(class{constructor(){throw new Error('policy blocked');}});
  await p.elements.get('rtc').onclick();
  assert.equal(p.read().webRTC.status,'检查失败');
  assert.equal(p.elements.get('rtc').disabled,false);
});

test('completed gathering preserves candidates and closes peer',async()=>{
  let closed=false;
  class Peer{
    constructor(){this.iceGatheringState='new';}
    createDataChannel(){}
    async createOffer(){return {};}
    async setLocalDescription(){this.iceGatheringState='complete';this.onicecandidate({candidate:{type:'host',address:'192.0.2.1',protocol:'udp',candidate:'test'}});}
    addEventListener(){}
    close(){closed=true;}
  }
  const p=page(Peer);await p.elements.get('rtc').onclick();
  assert.equal(p.read().webRTC.status,'收集完成');
  assert.equal(p.read().webRTC.candidates[0].address,'192.0.2.1');
  assert.equal(closed,true);
  assert.equal(p.elements.get('rtc').disabled,false);
});
