(()=>{
'use strict';
const APP_KEY='auditarEpiV1',STOCK_KEY='auditarEpiStockV1';
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>[...r.querySelectorAll(s)];
const uid=p=>p+'_'+Date.now()+'_'+Math.random().toString(36).slice(2,8);
function app(){try{return {companies:[],workers:[],epis:[],deliveries:[],...JSON.parse(localStorage.getItem(APP_KEY)||'{}')}}catch{return {companies:[],workers:[],epis:[],deliveries:[]}}}
function stock(){try{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{},...JSON.parse(localStorage.getItem(STOCK_KEY)||'{}')}}catch{return {startedAt:'',processedDeliveryIds:[],movements:[],minimums:{}}}}
function toast(m){const e=$('#toast');if(!e)return alert(m);e.textContent=m;e.classList.add('show');setTimeout(()=>e.classList.remove('show'),2600)}
function notify(){document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'quick-epi-v325'}}))}
function style(){
 if($('#quickEpi325Style'))return;
 const s=document.createElement('style');s.id='quickEpi325Style';s.textContent=
 '.qe325-modal{position:fixed;inset:0;z-index:19000;background:rgba(8,31,28,.58);display:none;align-items:flex-end;justify-content:center;padding:0}'+
 '.qe325-modal.open{display:flex}.qe325-sheet{width:min(100%,620px);max-height:92vh;overflow:auto;background:#fff;border-radius:22px 22px 0 0;padding:18px}'+
 '.qe325-sheet h3{margin:0;color:#173d39}.qe325-sheet p{margin:5px 0 14px;color:#6b807d;font-size:12px}.qe325-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}'+
 '.qe325-grid label{display:grid;gap:5px;font-size:11px;font-weight:850;color:#46615d}.qe325-grid label.full{grid-column:1/-1}.qe325-grid input{width:100%;box-sizing:border-box;min-height:46px;border:1px solid #cededa;border-radius:12px;padding:9px 11px}'+
 '.qe325-actions{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:14px}.qe325-actions button{min-height:48px;border-radius:12px;border:1px solid #c9dcd8;font-weight:900}.qe325-actions .primary{background:#0f766e;color:#fff;border-color:#0f766e}'+
 '.qe325-inline{margin-left:6px}.qe325-note{background:#f4faf8;border:1px solid #dce8e5;border-radius:11px;padding:9px;font-size:11px;color:#5e7772;margin-top:10px}@media(max-width:480px){.qe325-grid{grid-template-columns:1fr}.qe325-grid label.full{grid-column:auto}}';
 document.head.appendChild(s);
}
function modal(){
 let d=$('#quickEpi325Modal');if(d)return d;
 d=document.createElement('div');d.id='quickEpi325Modal';d.className='qe325-modal';d.innerHTML=
 '<div class="qe325-sheet"><h3>Cadastrar EPI</h3><p>Cadastre sem sair da entrega.</p><form id="quickEpi325Form">'+
 '<div class="qe325-grid"><label class="full">EPI<input id="qe325Name" required placeholder="Ex.: Óculos de segurança"></label>'+
 '<label>CA<input id="qe325Ca" inputmode="numeric" placeholder="Número do CA"></label><label>Tamanho<input id="qe325Size" placeholder="Opcional"></label>'+
 '<label>Fabricante / modelo<input id="qe325Model" placeholder="Opcional"></label><label>Troca prevista (dias)<input id="qe325Cycle" type="number" min="0" inputmode="numeric" placeholder="Opcional"></label>'+
 '<label class="full">Saldo inicial nesta empresa<input id="qe325Stock" type="number" min="0" inputmode="numeric" placeholder="Opcional"></label></div>'+
 '<div class="qe325-note">Se informar saldo inicial, o estoque será criado para a empresa selecionada na entrega.</div>'+
 '<div class="qe325-actions"><button id="qe325Cancel" type="button">Cancelar</button><button class="primary" type="submit">Salvar e usar</button></div></form></div>';
 document.body.appendChild(d);
 $('#qe325Cancel').onclick=()=>d.classList.remove('open');
 $('#quickEpi325Form').addEventListener('submit',save);
 d.addEventListener('click',e=>{if(e.target===d)d.classList.remove('open')});
 return d;
}
function open(){
 const companyId=$('#deliveryCompany')?.value||'';
 if(!companyId)return toast('Selecione a empresa da entrega primeiro.');
 const d=modal();['qe325Name','qe325Ca','qe325Size','qe325Model','qe325Cycle','qe325Stock'].forEach(id=>{const e=$('#'+id);if(e)e.value=''});
 d.classList.add('open');setTimeout(()=>$('#qe325Name')?.focus(),50);
}
function save(e){
 e.preventDefault();
 const companyId=$('#deliveryCompany')?.value||'',name=$('#qe325Name')?.value.trim()||'';
 if(!companyId)return toast('Selecione a empresa da entrega.');if(!name)return toast('Informe o nome do EPI.');
 const a=app(),id=uid('e'),now=new Date().toISOString();
 a.epis.push({id,name,ca:$('#qe325Ca')?.value.trim()||'',model:$('#qe325Model')?.value.trim()||'',size:$('#qe325Size')?.value.trim()||'',cycle:Math.max(0,Number($('#qe325Cycle')?.value||0)),createdAt:now,updatedAt:now,active:true});
 localStorage.setItem(APP_KEY,JSON.stringify(a));
 const initial=Math.max(0,Number($('#qe325Stock')?.value||0));
 if(initial>0){const s=stock(),key=companyId+'::'+id;s.minimums[key]=s.minimums[key]??5;s.movements.unshift({id:uid('sm'),type:'SET',delta:initial,companyId,epiId:id,note:'Saldo inicial no cadastro rápido',createdAt:now});localStorage.setItem(STOCK_KEY,JSON.stringify(s));}
 notify();modal().classList.remove('open');
 setTimeout(()=>{let rows=$$('.delivery-item'),row=rows.find(r=>!r.querySelector('.item-epi')?.value);if(!row){$('#btnAddItem')?.click();rows=$$('.delivery-item');row=rows[rows.length-1]}setTimeout(()=>{const sel=row?.querySelector('.item-epi');if(sel){sel.value=id;sel.dispatchEvent(new Event('change',{bubbles:true}))}toast('EPI cadastrado e adicionado à entrega.');},80)},80);
}
function inject(){
 if($('#quickEpi325Button'))return;
 const btn=$('#btnAddItem');if(!btn)return;
 const b=document.createElement('button');b.id='quickEpi325Button';b.type='button';b.className='secondary qe325-inline';b.textContent='＋ Cadastrar EPI';b.onclick=open;btn.insertAdjacentElement('afterend',b);
}
function boot(){style();modal();inject();[250,700,1500].forEach(ms=>setTimeout(inject,ms));document.addEventListener('click',e=>{if(e.target.closest('[data-go="delivery"]'))setTimeout(inject,60)},true);document.addEventListener('gestao-epi-auth-ready',()=>setTimeout(inject,100));}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();