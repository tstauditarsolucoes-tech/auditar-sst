// Independent simulated-browser regression: no production session or Apps Script calls.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../feature_sources/client_treatment_portal_ui_v1.js'),'utf8');
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.value='';this.open=false;this.disabled=false;this.removed=false;this.textContent='';}
  append(...items){this.children.push(...items);}
  replaceChildren(...items){this.children=[...items];}
  remove(){this.removed=true;}
  setAttribute(key,value){this[key]=value;}
  addEventListener(name,cb){this['event_'+name]=cb;}
  focus(){this.focused=true;}
  scrollIntoView(){this.scrolled=true;}
  get options(){return this.children;}
  querySelector(selector){
    const matches=x=> selector==='select'?x.tag==='select':selector==='textarea'?x.tag==='textarea':
      selector==='[role="status"]'&&x.role==='status';
    const walk=x=>{for(const item of x.children){if(matches(item))return item;const result=walk(item);if(result)return result;}return null;};
    return walk(this);
  }
}
const text=(tag,value,cls)=>{const e=new Element(tag);e.textContent=String(value||'');e.className=cls||'';return e;};
let storedInbox=new Element('section'),failures=[];
const runner={
  withSuccessHandler(fn){this.success=fn;return this;},
  withFailureHandler(fn){this.failure=fn;return this;}
};
const ctx={
  document:{createElement:tag=>new Element(tag)},
  google:{script:{run:runner}},
  $:id=>id==='treatmentInboxV2'?storedInbox:null,
  text,token:'session-token',current:null,console,
  formatPortalDate:x=>x,
  showEvidenceForm:()=>{},
  statusBucket:()=> 'todo'
};
vm.createContext(ctx);
vm.runInContext(source,ctx,{filename:'client_treatment_portal_ui_v1.js'});

// Previously rendered conversations must be discarded on a switch to an unauthorized login.
vm.runInContext('renderTreatmentInboxV2()',ctx);
assert.equal(storedInbox.removed,true,'old inbox persisted after losing authorization');

let missing='';
ctx.treatmentCallV1('clientPortalTreatmentPost',['token','company','GERAL',{message:'x'}],
 ()=>{throw Error('a missing route cannot succeed');},message=>{missing=message;});
assert.match(missing,/Módulo de comunicação indisponível/);

// The general timeline is visible and the support shortcut selects a real send action.
ctx.current={user:{role:'cliente'},companies:[{id:'c1',permissions:{tratativas:true,naoConformidades:false}}]};
const company={id:'c1',permissions:{tratativas:true,naoConformidades:false}};
const hub=ctx.renderTreatmentHubV1(company);
const support=hub.children.find(x=>x.tag==='button' && x.textContent==='Solicitar apoio técnico');
const general=hub.children.find(x=>x.tag==='details');
assert.ok(support&&general,'support button / general timeline missing');
assert.equal(general.open,true,'client general timeline should be expanded');
support.onclick();
const type=general.querySelector('select');
const note=general.querySelector('textarea');
assert.equal(type.value,'pedido_apoio');
assert.match(note.value,/Precisamos do apoio/);
const form=general.querySelector('form'); // Form must remain available and actionable.
assert.ok(form&&typeof form.onsubmit==='function');
assert.ok(note.focused,'support must focus on the message field');
assert.ok(general.scrolled,'support must navigate to the conversation');

let called=0;
ctx.treatmentCallV1=(name,args,onSuccess)=>{
  if(name==='clientPortalTreatmentPost'){called++;onSuccess({ok:true,id:'treat_success_01'});}
  else if(name==='clientPortalTreatmentList'){onSuccess({ok:true,events:[]});}
};
ctx.renderTreatmentInboxV2=()=>{};
note.value='Solicito uma visita técnica para avaliar o equipamento.';
form.onsubmit({preventDefault(){}});
assert.equal(called,1,'one support request must call the backend only once');
assert.ok(form.children.some(x=>/Pedido de apoio registrado/.test(x.textContent)),
  'support confirmation must be shown after backend acknowledgment');
console.log('CLIENT_PORTAL_UI_V2_OK: support, single post, missing GS, session isolation, visible timeline');
