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
   }else if(img){
     if(!validImage(d.signature)){img.remove();if(!sign.querySelector('.receipt-sign-missing'))sign.insertAdjacentHTML('afterbegin','<div class="receipt-sign-missing">Assinatura eletrônica não disponível neste aparelho.</div>')}
     else img.addEventListener('error',()=>{img.remove();if(!sign.querySelector('.receipt-sign-missing'))sign.insertAdjacentHTML('afterbegin','<div class="receipt-sign-missing">Assinatura eletrônica não pôde ser exibida.</div>')},{once:true});
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
async function nativePrint(){
 if(currentReceiptId)repairReceipt(currentReceiptId);
 const plugin=nativePrintPlugin();
 if(plugin?.print){
   try{await plugin.print({jobName:'Comprovante de Entrega de EPI'});return}catch(e){toast('Não foi possível abrir a impressão do Android.')}
 }
 try{window.print()}catch(_){toast('Impressão indisponível neste aparelho.')}
}
function bindPrint(){
 document.addEventListener('click',e=>{
   const r=e.target.closest?.('[data-receipt]');if(r){currentReceiptId=r.dataset.receipt;setTimeout(()=>repairReceipt(currentReceiptId),80)}
   if(e.target.closest?.('#btnPrint')){e.preventDefault();e.stopImmediatePropagation();nativePrint()}
   if(e.target.closest?.('#flow360PrintReport')){e.preventDefault();e.stopImmediatePropagation();nativePrint()}
   if(e.target.closest?.('#btnSaveDelivery'))setTimeout(enrichNewest,220);
 },true);
 document.addEventListener('auditar-epi-data-changed',()=>setTimeout(()=>{enrichNewest();if($('#receipt')?.classList.contains('active')){const root=data(),id=currentReceiptId||root.deliveries?.[0]?.id;if(id)repairReceipt(id)}},100));
}
function stopScan(){if(scanTimer){clearInterval(scanTimer);scanTimer=null}if(scanStream){scanStream.getTracks().forEach(t=>t.stop());scanStream=null}}
function findWorker(code){
 const a=data(),raw=String(code||'').trim(),digits=raw.replace(/\D/g,'');
 return (a.workers||[]).find(x=>String(x.id||'')===raw||String(x.reg||'')===raw||String(x.cpf||'').replace(/\D/g,'')===digits);
}
function openWorker(w){if(!w)return toast('Trabalhador não encontrado.');const go=document.querySelector('[data-go="workers"]');go?.click();setTimeout(()=>{const input=$('#workerSearch');if(input){input.value=w.name||w.reg||'';input.dispatchEvent(new Event('input',{bubbles:true}))}const openBtn=document.querySelector('[data-del-worker="'+CSS.escape(w.id)+'"]')||document.querySelector('[data-worker-sheet="'+CSS.escape(w.id)+'"]');openBtn?.click()},100)}
function scanFallback(){
 const code=prompt('Informe CPF, matrícula ou código do trabalhador:');if(!code)return;openWorker(findWorker(code))
}
async function scanWorkerQr(){
 if(!('BarcodeDetector'in window)||!navigator.mediaDevices?.getUserMedia)return scanFallback();
 let modal=$('#receipt380QrModal');
 if(!modal){modal=document.createElement('div');modal.id='receipt380QrModal';modal.className='receipt380-scan-modal';modal.innerHTML='<div class="receipt380-scan-card"><div class="receipt380-scan-head"><b>Ler QR do trabalhador</b><button id="receipt380ScanClose">×</button></div><video id="receipt380ScanVideo" autoplay playsinline></video><small>Aponte a câmera para o QR. Se não conseguir, use o código manual.</small><button id="receipt380Manual" class="primary">Digitar código</button></div>';document.body.appendChild(modal);$('#receipt380ScanClose').onclick=()=>{stopScan();modal.classList.remove('open')};$('#receipt380Manual').onclick=()=>{stopScan();modal.classList.remove('open');scanFallback()}}
 modal.classList.add('open');
 try{
  scanStream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false});const video=$('#receipt380ScanVideo');video.srcObject=scanStream;await video.play();const detector=new BarcodeDetector({formats:['qr_code']});
  scanTimer=setInterval(async()=>{try{const found=await detector.detect(video);const raw=found?.[0]?.rawValue;if(!raw)return;const w=findWorker(raw);if(!w)return;stopScan();modal.classList.remove('open');openWorker(w)}catch(_){}},400)
 }catch(_){stopScan();modal.classList.remove('open');scanFallback()}
}
function bindQr(){
 document.addEventListener('click',e=>{if(e.target.closest?.('#ux300Qr')){e.preventDefault();e.stopImmediatePropagation();scanWorkerQr()}},true)
}
function styles(){
 if($('#receipt380Style'))return;const s=document.createElement('style');s.id='receipt380Style';s.textContent=`
.receipt-face-proof{font-size:42px;line-height:1;margin:14px auto 8px}.receipt-sign-missing{font-size:11px;color:#6b817d;margin:12px auto;max-width:320px}.receipt380-scan-modal{display:none;position:fixed;inset:0;z-index:12000;background:rgba(0,0,0,.66);padding:18px;align-items:center;justify-content:center}.receipt380-scan-modal.open{display:flex}.receipt380-scan-card{width:min(100%,520px);background:#fff;border-radius:18px;padding:14px}.receipt380-scan-head{display:flex;justify-content:space-between;align-items:center;font-size:17px;margin-bottom:10px}.receipt380-scan-head button{border:0;background:#eef5f4;border-radius:10px;width:38px;height:38px;font-size:24px}.receipt380-scan-card video{width:100%;min-height:270px;max-height:60vh;object-fit:cover;border-radius:14px;background:#111}.receipt380-scan-card small{display:block;color:#667f7a;line-height:1.45;margin:9px 0}.receipt380-scan-card .primary{width:100%;min-height:48px}
@media print{#bottomNav,.bottom-nav,.view-head,.receipt-actions,.no-print,#toast{display:none!important}#receipt{display:block!important}.app-shell{padding:0!important}.receipt-card,#receiptContent{box-shadow:none!important;border:0!important;margin:0!important;padding:0!important}}
`;document.head.appendChild(s)
}
function boot(){styles();bindPrint();bindQr();enrichNewest()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();