(()=>{
'use strict';
const APP='auditarEpiV1';
const $=(s,r=document)=>r.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function root(){try{return JSON.parse(localStorage.getItem(APP)||'{}')}catch{return {}}}
async function sha256(text){
  try{
    const data=new TextEncoder().encode(String(text||'')),hash=await crypto.subtle.digest('SHA-256',data);
    return Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
  }catch(_){return ''}
}
function stable(value){
  if(Array.isArray(value))return '['+value.map(stable).join(',')+']';
  if(value&&typeof value==='object'){
    return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',')+'}';
  }
  return JSON.stringify(value);
}
function methodLabel(d){
  if(d?.confirmationMethod==='face-biometric'||d?.biometricVerified)return 'Biometria facial 1:1';
  if(d?.confirmationMethod==='fingerprint')return 'Biometria digital';
  return 'Assinatura em tela';
}
function canonical(d,w,c,epis,signatureHash){
  return {
    schema:'gestao-epi-receipt-v1',
    deliveryId:String(d?.id||''),
    company:{id:String(d?.companyId||''),name:String(c?.name||''),cnpj:String(c?.cnpj||'')},
    worker:{id:String(d?.workerId||''),name:String(w?.name||''),cpf:String(w?.cpf||''),reg:String(w?.reg||''),role:String(w?.role||''),sector:String(w?.sector||'')},
    createdAt:String(d?.createdAt||''),
    reason:String(d?.reason||''),
    responsible:String(d?.responsible||''),
    notes:String(d?.notes||''),
    items:(d?.items||[]).map(i=>({
      epiId:String(i.epiId||''),
      name:String(epis.get(i.epiId)?.name||''),
      ca:String(epis.get(i.epiId)?.ca||''),
      model:String(epis.get(i.epiId)?.model||''),
      size:String(epis.get(i.epiId)?.size||''),
      qty:Number(i.qty||0)
    })),
    confirmation:{
      method:methodLabel(d),
      signatureHash:signatureHash||'',
      biometricVerifiedAt:String(d?.biometricVerifiedAt||''),
      biometricEvidenceId:String(d?.biometricEvidenceId||''),
      biometricEvidenceHash:String(d?.biometricEvidenceHash||''),
      biometricLivenessVerified:!!d?.biometricLivenessVerified
    }
  };
}
function styles(){
  if($('#legalEvidenceV320Style'))return;
  const s=document.createElement('style');s.id='legalEvidenceV320Style';s.textContent=`
    .legal-v320-box{margin:15px 0 0;border:1px solid #cfe2dd;border-radius:12px;background:#f6fbfa;padding:12px 13px;color:#284f49;font-size:10px;line-height:1.5}
    .legal-v320-box h4{margin:0 0 7px;font-size:11px;color:#173f39}
    .legal-v320-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:8px 0}
    .legal-v320-item{background:#fff;border:1px solid #e0ece9;border-radius:9px;padding:8px;min-width:0}
    .legal-v320-item b{display:block;font-size:8px;text-transform:uppercase;letter-spacing:.05em;color:#6b817d;margin-bottom:2px}
    .legal-v320-code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;word-break:break-all;font-size:8.5px;color:#345e57}
    .legal-v320-note{border-top:1px solid #dceae7;padding-top:7px;margin-top:7px;color:#637975}
    .legal-v320-bio-notice{display:block;margin-top:7px;padding:9px 10px;border-radius:11px;background:#eef8f5;color:#315d56;font-size:10px;line-height:1.45}
    @media print{.legal-v320-box{break-inside:avoid;background:#fff!important}.legal-v320-bio-notice{background:#fff!important}}
  `;document.head.appendChild(s);
}
function improveBiometricNotice(){
  const t=$('#bioConsentText');
  if(t&&t.dataset.legalV320!=='1'){
    t.dataset.legalV320='1';
    t.textContent='O colaborador foi informado de que a biometria facial é usada exclusivamente para confirmar sua identidade no registro de entrega de EPI. A assinatura em tela permanece disponível como alternativa.';
  }
  const panel=$('#bioDeliveryPanel');
  if(panel&&!panel.querySelector('.legal-v320-bio-notice')){
    const n=document.createElement('div');n.className='legal-v320-bio-notice';
    n.innerHTML='<b>Privacidade:</b> a comparação é 1:1 com o cadastro do próprio trabalhador. O comprovante não exibe o template biométrico nem a chave criptográfica.';
    panel.appendChild(n);
  }
}
async function patchReceipt(id){
  const content=$('#receiptContent');if(!content||content.dataset.legalV320===String(id||''))return;
  const r=root(),d=(r.deliveries||[]).find(x=>x.id===id);if(!d)return;
  const w=(r.workers||[]).find(x=>x.id===d.workerId)||{},c=(r.companies||[]).find(x=>x.id===d.companyId)||{};
  const epis=new Map((r.epis||[]).map(e=>[e.id,e]));
  const signatureHash=d.signature?await sha256(d.signature):'';
  const payload=canonical(d,w,c,epis,signatureHash),hash=await sha256(stable(payload));
  if(!hash)return;
  const evidenceId='EPI-'+String(d.id||'SEM-ID').toUpperCase();
  content.querySelector('.legal-v320-box')?.remove();
  const box=document.createElement('div');box.className='legal-v320-box';
  box.innerHTML=
    '<h4>Rastreabilidade do registro eletrônico</h4>'+
    '<div class="legal-v320-grid">'+
      '<div class="legal-v320-item"><b>Identificador da entrega</b><span class="legal-v320-code">'+esc(evidenceId)+'</span></div>'+
      '<div class="legal-v320-item"><b>Método de confirmação</b>'+esc(methodLabel(d))+'</div>'+
      '<div class="legal-v320-item"><b>Hash de integridade da ficha • SHA-256</b><span class="legal-v320-code">'+esc(hash)+'</span></div>'+
      '<div class="legal-v320-item"><b>Evidência biométrica</b>'+(d.biometricEvidenceId?'<span class="legal-v320-code">'+esc(d.biometricEvidenceId)+'</span>':'Não aplicável')+'</div>'+
    '</div>'+
    (d.biometricEvidenceHash?'<div><b>Hash da evidência biométrica:</b> <span class="legal-v320-code">'+esc(d.biometricEvidenceHash)+'</span></div>':'')+
    '<div class="legal-v320-note">O hash acima é calculado sobre os dados apresentados nesta ficha e suas referências de confirmação. Qualquer alteração nesses dados produz outro hash. Este registro apoia a rastreabilidade do fornecimento eletrônico de EPI e a extração de relatório; não representa certificação ICP-Brasil nem homologação por órgão público.</div>';
  content.appendChild(box);content.dataset.legalV320=String(id||'');
}
function receiptIdFromDom(){
  const active=document.querySelector('[data-receipt].legal-current,[data-receipt][aria-current="true"]');
  if(active?.dataset.receipt)return active.dataset.receipt;
  const r=root(),rows=Array.isArray(r.deliveries)?r.deliveries:[];
  const head=$('#receiptContent .receipt-head');
  if($('#receipt')?.classList.contains('active')&&head&&rows.length)return rows.find(d=>String($('#receiptContent')?.textContent||'').includes((r.workers||[]).find(w=>w.id===d.workerId)?.name||'__'))?.id||'';
  return '';
}
function bind(){
  document.addEventListener('click',e=>{
    const b=e.target.closest('[data-receipt]');
    if(b){document.querySelectorAll('[data-receipt]').forEach(x=>x.classList.remove('legal-current'));b.classList.add('legal-current');setTimeout(()=>patchReceipt(b.dataset.receipt),90)}
  });
  const print=$('#btnPrint');if(print&&!print.dataset.legalV320){print.dataset.legalV320='1';print.addEventListener('click',()=>{const id=receiptIdFromDom();if(id)patchReceipt(id)},true)}
}
let raf=0;
function pass(){styles();improveBiometricNotice();bind();const id=receiptIdFromDom();if(id)patchReceipt(id)}
function boot(){
  pass();
  new MutationObserver(()=>{if(raf)return;raf=requestAnimationFrame(()=>{raf=0;improveBiometricNotice()})}).observe(document.body,{childList:true,subtree:true});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();