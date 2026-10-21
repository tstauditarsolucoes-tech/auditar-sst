(()=>{
'use strict';
const APP='auditarEpiV1';
const $=(s,r=document)=>r.querySelector(s);
const esc=(v='')=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let currentReceiptId='',scanStream=null,scanTimer=null;
function data(){try{return JSON.parse(localStorage.getItem(APP)||'{}')}catch{return {deliveries:[],workers:[]}}}
function user(){return window.GestaoEpiAuth?.user?.()||{}}
function toast(m){const t=$('#toast');if(t){t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)}else alert(m)}
function validImage(src){return /^data:image\/(?:png|jpeg|jpg|webp);base64,/i.test(String(src||''))}
function repairReceipt(id){
 const root=data(),d=(root.deliveries||[]).find(x=>x.id===id);if(!d)return;currentReceiptId=id;
 const content=$('#receiptContent');if(!content)return;
 const sign=content.querySelector('.receipt-sign');if(sign){
   const img=sign.querySelector('img'),line=sign.querySelector('.sign-line'),name=(root.workers||[]).find(w=>w.id===d.workerId)?.name||'Colaborador';
   if(d.confirmationMethod==='face-biometric'||d.biometricVerified){
     img?.remove();
     if(!sign.querySelector('.receipt-face-proof'))sign.insertAdjacentHTML('afterbegin','<div class="receipt-face-proof" aria-hidden="true">🙂</div>');
     if(line)line.innerHTML=esc(name)+'<br>Biometria facial verificada';
     if(!sign.querySelector('.receipt-face-details')){
       const info=[Number.isFinite(Number(d.biometricSimilarity))&&Number(d.biometricSimilarity)>0?'Compatibilidade: '+Math.round(Number(d.biometricSimilarity)*100)+'%':'',d.biometricVerifiedAt?'Verificado em '+new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(d.biometricVerifiedAt)):'',d.biometricEvidenceId?'ID da evidência: '+d.biometricEvidenceId:''].filter(Boolean);
       if(info.length){const el=document.createElement('p');el.className='receipt-face-details';el.textContent=info.join(' • ');sign.appendChild(el)}
     }
   }else if(img){
     if(!validImage(d.signature)){img.remove();if(!sign.querySelector('.receipt-sign-missing'))sign.insertAdjacentHTML('afterbegin','<div class="receipt-sign-missing">Assinatura eletrônica não disponível neste aparelho.</div>')}
     else {const broken=()=>{img.remove();if(!sign.querySelector('.receipt-sign-missing'))sign.insertAdjacentHTML('afterbegin','<div class="receipt-sign-missing">Assinatura eletrônica não pôde ser exibida.</div>')};if(img.complete&&img.naturalWidth===0)broken();else img.addEventListener('error',broken,{once:true})}
   }
 }
 const trace=content.querySelector('.flow360-trace');
 if(trace){
   const delivered=[...trace.querySelectorAll('div')].find(x=>/^Entregue por/i.test(x.textContent||''));
   const who=d.warehouseDeliveredBy?.name||d.warehouseDeliveredBy?.username||d.registeredBy?.name||d.registeredBy?.username||d.responsible||'';
   if(delivered&&!who)delivered.innerHTML='<b>Entregue por</b><br>Não registrado<br><small>'+new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(d.warehouseDeliveredAt||d.createdAt||Date.now()))+'</small>';
 }
}
function enrichNewest(){
 const root=data(),d=(root.deliveries||[])[0];if(!d||Date.now()-Date.parse(d.createdAt||0)>12000)return;
 if(!d.registeredBy){
   const u=user();if(u?.username||u?.name){d.registeredBy={username:String(u.username||''),name:String(u.name||u.username||'')};d.registeredAt=d.createdAt||new Date().toISOString();d.updatedAt=new Date().toISOString();localStorage.setItem(APP,JSON.stringify(root));document.dispatchEvent(new CustomEvent('auditar-epi-data-changed',{detail:{source:'receipt-fix-v380'}}))}
 }
}
function nativePrintPlugin(){
 try{
  if(window.Capacitor?.registerPlugin)return window.Capacitor.registerPlugin('NativePrint');
 }catch(_){}
 return window.Capacitor?.Plugins?.NativePrint||null;
}
function dateLabel(iso){
 if(!iso)return '';
 try{return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date(iso))}
 catch(_){return String(iso)}
}
function documentData(){
 const root=data(),id=currentReceiptId||($('#receipt')?.classList.contains('active')?root.deliveries?.[0]?.id:'');
 const d=(root.deliveries||[]).find(x=>String(x.id)===String(id));
 if(!d)throw new Error('Abra um comprovante de entrega antes de gerar o PDF.');
 const w=(root.workers||[]).find(x=>x.id===d.workerId)||{};
 const c=(root.companies||[]).find(x=>x.id===d.companyId)||{};
 const items=(d.items||[]).filter(i=>Number(i.qty)>0).map(i=>{
   const e=(root.epis||[]).find(x=>x.id===i.epiId)||{};
   return {name:String(e.name||'EPI'),ca:String(e.ca||''),model:String(e.model||''),size:String(e.size||''),qty:String(i.qty||1)};
 });
 if(!w.name||!items.length)throw new Error('Registro incompleto: colaborador ou itens não encontrados.');
 const a=(root.auditLog||[]).find(x=>x.type==='epi_authorization'&&x.id===d.authorizationId);
 const review=(root.auditLog||[]).find(x=>x.type==='epi_direct_delivery'&&x.deliveryId===d.id);
 const flow=d.deliveryFlow==='authorized'||d.authorizationId?'Entrega com liberação do TST':d.deliveryFlow==='direct'?'Entrega direta do almoxarifado':'Entrega padrão';
 const actor=x=>typeof x==='string'?x:(x?.name||x?.username||'');
 const biometric=d.confirmationMethod==='face-biometric'||d.biometricVerified===true;
 const content=$('#receiptContent');
 const hasLegal=content?.dataset?.legalV320===String(d.id);
 const codes=hasLegal?[...content.querySelectorAll('.legal-v320-code')].map(x=>x.textContent?.trim()||''):[];
 return {
  deliveryId:String(d.id||''),company:String(c.name||''),cnpj:String(c.cnpj||''),
  worker:String(w.name||''),cpf:String(w.cpf||''),registration:String(w.reg||''),
  roleSector:[w.role,w.sector].filter(Boolean).join(' / '),
  date:dateLabel(d.createdAt),items,
  type:flow,reason:String(d.reason||''),notes:String(d.notes||''),
  responsible:String(d.responsible||''),deliveredBy:String(actor(d.warehouseDeliveredBy)||actor(d.registeredBy)||d.responsible||'Não informado — registro anterior'),
  authorizationCode:flow==='Entrega com liberação do TST'?String(a?.code||'Não informado — registro anterior'):'',
  authorizedBy:flow==='Entrega com liberação do TST'?String(actor(a?.authorizedBy)||'Não informado — registro anterior'):'',
  reviewStatus:flow==='Entrega direta do almoxarifado'?String(review?.reviewStatus==='reviewed'?'Revisada por '+(actor(review?.reviewedBy)||'responsável não informado'):'Pendente de revisão'):'',
  facial:biometric,method:biometric?'Biometria facial verificada':validImage(d.signature)?'Assinatura eletrônica':'Confirmação sem imagem de assinatura',
  signature:biometric?'':validImage(d.signature)?d.signature:'',
  similarity:biometric&&Number(d.biometricSimilarity)>0?Math.round(Number(d.biometricSimilarity)*100)+'%':'',
  verifiedAt:biometric?dateLabel(d.biometricVerifiedAt||d.createdAt):'',
  evidenceId:biometric?String(d.biometricEvidenceId||''):'',
  evidenceHash:biometric?String(d.biometricEvidenceHash||''):'',
  evidenceRecordId:'EPI-'+String(d.id||'').toUpperCase(),
  receiptHash:codes[1]||''
 };
}
function setPdfBusy(value){
 for(const el of ['#btnPrint','#btnShareReceiptPdf']){
  const button=$(el);if(!button)continue;button.disabled=value;button.setAttribute('aria-busy',value?'true':'false');
 }
}
async function exportReceiptPdf(share=false){
 if(!window.Capacitor?.isNativePlatform?.()) {
   toast('A geração e o compartilhamento nativos de PDF estão disponíveis no aplicativo Android.');
   return;
 }
 let receipt;
 try{
   if(currentReceiptId)repairReceipt(currentReceiptId);
   receipt=documentData();
 }catch(error){toast(error?.message||'Não foi possível montar o comprovante.');return}
 const plugin=nativePrintPlugin();
 const fn=share?'sharePdf':'print';
 if(typeof plugin?.[fn]!=='function'){
   toast('Atualize o aplicativo Android para usar '+(share?'Compartilhar PDF.':'Imprimir PDF.'));
   return;
 }
 setPdfBusy(true);
 try{
   await plugin[fn]({receipt,jobName:'Comprovante de Entrega de EPI'});
 }catch(error){
   toast('Erro ao gerar PDF: '+String(error?.message||'verifique o registro').slice(0,110));
 }finally{
   setPdfBusy(false);
 }
}
function shareButton(){
 if($('#btnShareReceiptPdf')||!$('#btnPrint'))return;
 const button=document.createElement('button');
 button.id='btnShareReceiptPdf';
 button.type='button';
 button.className='secondary';
 button.textContent='↗ Compartilhar PDF';
 button.setAttribute('aria-label','Compartilhar comprovante de entrega em PDF');
 $('#btnPrint').insertAdjacentElement('afterend',button);
}

function bindPrint(){
 document.addEventListener('click',e=>{
   const r=e.target.closest?.('[data-receipt]');if(r){currentReceiptId=r.dataset.receipt;setTimeout(()=>repairReceipt(currentReceiptId),80)}
   if(e.target.closest?.('#btnPrint')){e.preventDefault();e.stopImmediatePropagation();exportReceiptPdf(false)}
   if(e.target.closest?.('#btnShareReceiptPdf')){e.preventDefault();e.stopImmediatePropagation();exportReceiptPdf(true)}
   if(e.target.closest?.('#flow360PrintReport')){e.preventDefault();e.stopImmediatePropagation();try{window.print()}catch(_){toast('Não foi possível imprimir este relatório.')}}
   if(e.target.closest?.('#btnSaveDelivery'))setTimeout(()=>{enrichNewest();if($('#receipt')?.classList.contains('active')){const id=data().deliveries?.[0]?.id||'';if(id){currentReceiptId=id;repairReceipt(id)}}},220);
 },true);
 document.addEventListener('auditar-epi-data-changed',()=>setTimeout(()=>{enrichNewest();if($('#receipt')?.classList.contains('active')){const root=data(),id=currentReceiptId||root.deliveries?.[0]?.id;if(id)repairReceipt(id)}},100));
}
function stopScan(){if(scanTimer){clearInterval(scanTimer);scanTimer=null}if(scanStream){scanStream.getTracks().forEach(t=>t.stop());scanStream=null}}
function findWorker(code){
 const root=data(),raw=String(code||'').trim();
 if(!raw)return null;
 let candidate=raw;
 try{
   const url=new URL(raw);
   candidate=url.searchParams.get('workerId')||url.searchParams.get('worker')||url.searchParams.get('cpf')||url.searchParams.get('matricula')||url.searchParams.get('id')||raw;
 }catch(_){}
 const clean=String(candidate).trim(),digits=clean.replace(/\D/g,'');
 return (root.workers||[]).find(w=>String(w.id||'')===clean||String(w.reg||'')===clean||(
   digits.length===11&&String(w.cpf||'').replace(/\D/g,'')===digits
 ))||null;
}
function openWorker(w){
 if(!w)return toast('Trabalhador não encontrado nesta conta.');
 // O delegado data-ux-worker abre a ficha 360°. Nunca acionar data-del-worker: ele exclui registros!
 const trigger=document.createElement('button');trigger.type='button';trigger.hidden=true;trigger.dataset.uxWorker=String(w.id);
 document.body.appendChild(trigger);
 try{trigger.click()}finally{trigger.remove()}
}
function scanFallback(){
 const code=prompt('Informe CPF, matrícula ou código do trabalhador:');
 if(!code)return;
 openWorker(findWorker(code));
}
function nativeQrPlugin(){
 try{if(window.Capacitor?.registerPlugin)return window.Capacitor.registerPlugin('NativeQr')}catch(_){}
 return window.Capacitor?.Plugins?.NativeQr||null;
}
async function scanWorkerQr(){
 const native=nativeQrPlugin();
 if(window.Capacitor?.isNativePlatform?.()&&native?.scan){
   try{
     const result=await native.scan();
     if(result?.rawValue)openWorker(findWorker(result.rawValue));
     return;
   }catch(e){
     if(String(e?.message||e||'').toLowerCase().includes('cancel'))return;
     toast('Leitor nativo indisponível. Tentando câmera alternativa.');
   }
 }
 if(!('BarcodeDetector'in window)||!navigator.mediaDevices?.getUserMedia)return scanFallback();
 let modal=$('#receipt380QrModal');
 if(!modal){
   modal=document.createElement('div');modal.id='receipt380QrModal';modal.className='receipt380-scan-modal';
   modal.innerHTML='<div class="receipt380-scan-card"><div class="receipt380-scan-head"><b>Ler QR do trabalhador</b><button type="button" id="receipt380ScanClose" aria-label="Fechar">×</button></div><video id="receipt380ScanVideo" autoplay playsinline></video><small>Aponte a câmera para o QR. Se não conseguir, use o código manual.</small><button type="button" id="receipt380Manual" class="primary">Digitar código</button></div>';
   document.body.appendChild(modal);
   $('#receipt380ScanClose').onclick=()=>{stopScan();modal.classList.remove('open')};
   $('#receipt380Manual').onclick=()=>{stopScan();modal.classList.remove('open');scanFallback()};
 }
 modal.classList.add('open');
 try{
   scanStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});
   const video=$('#receipt380ScanVideo');video.srcObject=scanStream;await video.play();
   const detector=new BarcodeDetector({formats:['qr_code']});
   scanTimer=setInterval(async()=>{try{
     const rows=await detector.detect(video),raw=rows?.[0]?.rawValue;
     if(!raw)return;
     const w=findWorker(raw);if(!w){toast('QR lido, mas trabalhador não encontrado nesta conta.');return}
     stopScan();modal.classList.remove('open');openWorker(w);
   }catch(_){}},400);
 }catch(_){stopScan();modal.classList.remove('open');scanFallback()}
}

function bindQr(){
 document.addEventListener('click',e=>{if(e.target.closest?.('#ux300Qr')){e.preventDefault();e.stopImmediatePropagation();scanWorkerQr()}},true)
}
function styles(){
 if($('#receipt380Style'))return;const s=document.createElement('style');s.id='receipt380Style';s.textContent=`
.receipt-actions{flex-wrap:wrap}.receipt-actions>button{flex:1 1 140px;min-height:48px}.receipt-face-details{font-size:11px;color:#425c58;line-height:1.5}.receipt-face-proof{font-size:42px;line-height:1;margin:14px auto 8px}.receipt-sign-missing{font-size:11px;color:#6b817d;margin:12px auto;max-width:320px}.receipt380-scan-modal{display:none;position:fixed;inset:0;z-index:12000;background:rgba(0,0,0,.66);padding:18px;align-items:center;justify-content:center}.receipt380-scan-modal.open{display:flex}.receipt380-scan-card{width:min(100%,520px);background:#fff;border-radius:18px;padding:14px}.receipt380-scan-head{display:flex;justify-content:space-between;align-items:center;font-size:17px;margin-bottom:10px}.receipt380-scan-head button{border:0;background:#eef5f4;border-radius:10px;width:38px;height:38px;font-size:24px}.receipt380-scan-card video{width:100%;min-height:270px;max-height:60vh;object-fit:cover;border-radius:14px;background:#111}.receipt380-scan-card small{display:block;color:#667f7a;line-height:1.45;margin:9px 0}.receipt380-scan-card .primary{width:100%;min-height:48px}
#receipt.active{padding-bottom:calc(105px + env(safe-area-inset-bottom,0px))}
body:has(#receipt.active) #bottomNav{display:none!important}
body:has(.receipt380-scan-modal.open) #bottomNav{display:none!important}
@media(max-width:520px){#home:has(#ux300Quick) .hero-card{display:none!important}#home:has(#ux300Quick)>.notice{display:none!important}}
@media print{
 #bottomNav,.bottom-nav,.view-head,.receipt-actions,.no-print,#toast{display:none!important}
 html[data-epi-print-mode="receipt"] #receipt{display:block!important}
 html[data-epi-print-mode="report"] #receipt{display:none!important}
 .app-shell{padding:0!important}
 .receipt-card,#receiptContent{box-shadow:none!important;border:0!important;margin:0!important;padding:0!important}
}
`;document.head.appendChild(s)
}
function boot(){styles();shareButton();bindPrint();bindQr();enrichNewest()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();