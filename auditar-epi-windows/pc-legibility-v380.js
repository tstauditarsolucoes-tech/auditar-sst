(()=>{
'use strict';
const KEY='gestaoEpiPcTextSizeV380';
const $=(s,r=document)=>r.querySelector(s);
function mode(){return localStorage.getItem(KEY)||'comfortable'}
function apply(value){
 const v=['normal','comfortable','large'].includes(value)?value:'comfortable';
 document.body.classList.remove('pc380-text-normal','pc380-text-comfortable','pc380-text-large');
 document.body.classList.add('pc380-text-'+v);localStorage.setItem(KEY,v);
 const sel=$('#pc380TextSize');if(sel&&sel.value!==v)sel.value=v;
}
function style(){
 if($('#pc380LegibilityStyle'))return;
 const s=document.createElement('style');s.id='pc380LegibilityStyle';s.textContent=`
 @media(min-width:1000px){
  body.pc380-text-comfortable{font-size:15px!important}
  body.pc380-text-comfortable .sidebar{width:272px!important;min-width:272px!important;max-width:272px!important}
  body.pc380-text-comfortable .layout{grid-template-columns:272px minmax(0,1fr)!important}
  body.pc380-text-comfortable .sidebar .nav{min-height:43px!important;padding:10px 11px!important;font-size:15px!important}
  body.pc380-text-comfortable .sidebar .nav span{font-size:14px!important;line-height:1.3!important}
  body.pc380-text-comfortable .pc280-nav-group{font-size:10px!important;letter-spacing:.1em!important}
  body.pc380-text-comfortable .sidebar-brand .logo{font-size:20px!important}
  body.pc380-text-comfortable .sidebar-brand small{font-size:10px!important}
  body.pc380-text-comfortable .sidebar-foot b,body.pc380-text-comfortable .pc280-user b{font-size:12.5px!important}
  body.pc380-text-comfortable .sidebar-foot small,body.pc380-text-comfortable .pc280-user small{font-size:10.5px!important;line-height:1.35!important}
  body.pc380-text-comfortable .topbar{min-height:82px!important}
  body.pc380-text-comfortable #viewTitle{font-size:25px!important;line-height:1.2!important}
  body.pc380-text-comfortable #viewSub{font-size:12.5px!important;line-height:1.4!important}
  body.pc380-text-comfortable .main label{font-size:12.5px!important;line-height:1.35!important}
  body.pc380-text-comfortable .main input,body.pc380-text-comfortable .main select,body.pc380-text-comfortable .main textarea{font-size:14px!important;min-height:42px!important}
  body.pc380-text-comfortable .main button{font-size:12.5px!important;line-height:1.3!important}
  body.pc380-text-comfortable .main small{font-size:10.8px!important;line-height:1.45!important}
  body.pc380-text-comfortable .main p{font-size:12px!important;line-height:1.5!important}
  body.pc380-text-comfortable .main table{font-size:12px!important}
  body.pc380-text-comfortable .main th{font-size:10.8px!important;line-height:1.3!important}
  body.pc380-text-comfortable .main td{font-size:12px!important;line-height:1.4!important;padding-top:10px!important;padding-bottom:10px!important}
  body.pc380-text-comfortable .panel-head h2,body.pc380-text-comfortable .pc-modern-head h2,body.pc380-text-comfortable .v260-head h2,body.pc380-text-comfortable .v270-head h2{font-size:21px!important;line-height:1.25!important}
  body.pc380-text-comfortable .panel-head p,body.pc380-text-comfortable .pc-modern-head p,body.pc380-text-comfortable .v260-head p,body.pc380-text-comfortable .v270-head p{font-size:12px!important;line-height:1.45!important}
  body.pc380-text-comfortable .metric span,body.pc380-text-comfortable .pc310-kpi span,body.pc380-text-comfortable .v270-kpi span{font-size:11px!important}
  body.pc380-text-comfortable .metric strong{font-size:30px!important}
  body.pc380-text-comfortable .pc310-row b,body.pc380-text-comfortable .v260-row b,body.pc380-text-comfortable .v270-result b{font-size:12.5px!important}
  body.pc380-text-comfortable .pc310-row small,body.pc380-text-comfortable .v260-row small,body.pc380-text-comfortable .v270-result small{font-size:10.5px!important}
  
  body.pc380-text-large{font-size:16px!important}
  body.pc380-text-large .sidebar{width:292px!important;min-width:292px!important;max-width:292px!important}
  body.pc380-text-large .layout{grid-template-columns:292px minmax(0,1fr)!important}
  body.pc380-text-large .sidebar .nav{min-height:46px!important;padding:11px 12px!important;font-size:16px!important}
  body.pc380-text-large .sidebar .nav span{font-size:15px!important;line-height:1.35!important}
  body.pc380-text-large .pc280-nav-group{font-size:10.8px!important}
  body.pc380-text-large .sidebar-brand .logo{font-size:21px!important}
  body.pc380-text-large .sidebar-brand small{font-size:10.8px!important}
  body.pc380-text-large #viewTitle{font-size:27px!important}
  body.pc380-text-large #viewSub{font-size:13.5px!important}
  body.pc380-text-large .main label{font-size:13.5px!important}
  body.pc380-text-large .main input,body.pc380-text-large .main select,body.pc380-text-large .main textarea{font-size:15px!important;min-height:45px!important}
  body.pc380-text-large .main button{font-size:13.5px!important}
  body.pc380-text-large .main small{font-size:11.8px!important;line-height:1.5!important}
  body.pc380-text-large .main p{font-size:13px!important;line-height:1.55!important}
  body.pc380-text-large .main table{font-size:13px!important}
  body.pc380-text-large .main th{font-size:11.7px!important}
  body.pc380-text-large .main td{font-size:13px!important;line-height:1.45!important;padding-top:11px!important;padding-bottom:11px!important}
  body.pc380-text-large .panel-head h2,body.pc380-text-large .pc-modern-head h2,body.pc380-text-large .v260-head h2,body.pc380-text-large .v270-head h2{font-size:23px!important}
  body.pc380-text-large .panel-head p,body.pc380-text-large .pc-modern-head p,body.pc380-text-large .v260-head p,body.pc380-text-large .v270-head p{font-size:13px!important}
  body.pc380-text-large .metric span,body.pc380-text-large .pc310-kpi span,body.pc380-text-large .v270-kpi span{font-size:12px!important}
  body.pc380-text-large .metric strong{font-size:32px!important}
 }
 .pc380-text-control{display:flex;align-items:center;gap:7px;border:1px solid #d5e3e0;border-radius:10px;padding:6px 8px;background:#fff;white-space:nowrap}
 .pc380-text-control span{font-size:11px;font-weight:850;color:#56706b}
 .pc380-text-control select{min-height:32px!important;height:32px!important;font-size:11.5px!important;padding:4px 7px!important;border:1px solid #cbded9;border-radius:8px;background:#fff}
 `;document.head.appendChild(s)
}
function inject(){
 const top=$('.topbar');if(!top||$('#pc380TextControl'))return;
 const c=document.createElement('label');c.id='pc380TextControl';c.className='pc380-text-control';c.innerHTML='<span>Texto</span><select id="pc380TextSize"><option value="normal">Normal</option><option value="comfortable">Confortável</option><option value="large">Grande</option></select>';
 const right=top.lastElementChild;right?right.prepend(c):top.appendChild(c);
 $('#pc380TextSize').value=mode();$('#pc380TextSize').onchange=e=>apply(e.target.value);
}
function boot(){style();apply(mode());[200,700,1600,3000].forEach(ms=>setTimeout(()=>{inject();apply(mode())},ms))}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();