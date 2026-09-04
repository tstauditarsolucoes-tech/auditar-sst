(() => {
  const ENDPOINT='https://script.google.com/macros/s/AKfycbxqMnKiTlAJTFv3-odS2dB1NRcSD8wwvtNxxa-zCFhTM6GeNZszib_1N6eT9wSnOnOyjg/exec';
  const TOKEN_KEY='gestaoEpiMasterToken';
  const USER_KEY='gestaoEpiMasterUser';
  const $=(s,r=document)=>r.querySelector(s);
  const esc=(v='')=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function injectStyles(){
    if($('#masterRecoverStyle'))return;
    const s=document.createElement('style');s.id='masterRecoverStyle';s.textContent=`
      .recover-link{width:100%;margin-top:10px;border:0;background:transparent;color:#0f766e;font-weight:850;cursor:pointer;padding:8px}
      .recover-link:hover{text-decoration:underline}
      .recover-overlay{position:fixed;inset:0;z-index:50000;background:rgba(7,31,29,.78);display:none;align-items:center;justify-content:center;padding:22px}
      .recover-overlay.open{display:flex}.recover-card{width:min(460px,100%);background:#fff;border-radius:22px;padding:24px;box-shadow:0 30px 80px rgba(0,0,0,.28)}
      .recover-card h2{margin:0 0 6px;color:#173d39}.recover-card p{margin:0 0 14px;color:#647d79;font-size:13px;line-height:1.5}
      .recover-card label{display:grid;gap:5px;margin:10px 0;font-size:12px;font-weight:850;color:#355b57}.recover-card input{min-height:46px;border:1px solid #cfdfdc;border-radius:11px;padding:0 12px;font:inherit}
      .recover-actions{display:flex;gap:9px;margin-top:15px}.recover-actions button{flex:1;min-height:47px;border-radius:11px;font-weight:900;cursor:pointer}.recover-cancel{border:1px solid #cfdfdc;background:#fff;color:#355b57}.recover-save{border:0;background:#0f766e;color:#fff}.recover-error{min-height:18px;color:#b42318;font-size:12px;font-weight:800;margin-top:8px}
    `;document.head.appendChild(s);
  }

  function build(){
    injectStyles();
    const card=$('#loginOverlay .login-card');
    if(card&&!$('#btnRecoverMaster')){
      const b=document.createElement('button');b.id='btnRecoverMaster';b.type='button';b.className='recover-link';b.textContent='Esqueci meu acesso / Redefinir usuário e senha';
      card.appendChild(b);b.onclick=open;
    }
    if($('#masterRecoverOverlay'))return;
    const d=document.createElement('div');d.id='masterRecoverOverlay';d.className='recover-overlay';d.innerHTML=`<div class="recover-card"><h2>Redefinir acesso do Painel Mestre</h2><p>Use a chave de instalação do Apps Script. Clientes, empresas, trabalhadores e entregas não serão apagados.</p><label>Chave de instalação<input id="recoverSetupKey" type="password" autocomplete="off"></label><label>Seu nome<input id="recoverName" autocomplete="name"></label><label>Novo usuário<input id="recoverUser" autocomplete="username" autocapitalize="none"></label><label>Nova senha<input id="recoverPass" type="password" autocomplete="new-password" minlength="6"></label><label>Confirmar senha<input id="recoverPass2" type="password" autocomplete="new-password" minlength="6"></label><div id="recoverError" class="recover-error"></div><div class="recover-actions"><button id="recoverCancel" type="button" class="recover-cancel">Cancelar</button><button id="recoverSave" type="button" class="recover-save">Criar novo acesso</button></div></div>`;
    document.body.appendChild(d);$('#recoverCancel').onclick=close;$('#recoverSave').onclick=submit;$('#recoverPass2').addEventListener('keydown',e=>{if(e.key==='Enter')submit();});
  }
  function open(){build();$('#recoverError').textContent='';$('#masterRecoverOverlay').classList.add('open');setTimeout(()=>$('#recoverSetupKey')?.focus(),70);}
  function close(){$('#masterRecoverOverlay')?.classList.remove('open');}
  async function submit(){
    const setupKey=$('#recoverSetupKey').value.trim(),name=$('#recoverName').value.trim(),username=$('#recoverUser').value.trim(),password=$('#recoverPass').value,password2=$('#recoverPass2').value,err=$('#recoverError'),btn=$('#recoverSave');
    if(!setupKey||!username||!password){err.textContent='Preencha a chave, o usuário e a senha.';return;}if(password.length<6){err.textContent='A senha deve ter pelo menos 6 caracteres.';return;}if(password!==password2){err.textContent='As senhas não coincidem.';return;}
    btn.disabled=true;btn.textContent='Redefinindo…';err.textContent='';
    try{
      const res=await fetch(ENDPOINT,{method:'POST',headers:{'Content-Type':'text/plain;charset=utf-8'},body:JSON.stringify({action:'master_recover_access',setupKey,name,username,password})});
      const r=await res.json();if(!r?.ok)throw new Error(r?.message||'Não foi possível redefinir o acesso.');
      localStorage.setItem(TOKEN_KEY,r.token);localStorage.setItem(USER_KEY,JSON.stringify(r.user||{}));close();alert('Acesso redefinido com sucesso. Entre com o novo usuário e senha.');location.reload();
    }catch(e){err.textContent=esc(e.message||'Falha ao redefinir acesso.');}
    finally{btn.disabled=false;btn.textContent='Criar novo acesso';}
  }
  function init(){build();const obs=new MutationObserver(()=>{const card=$('#loginOverlay .login-card');if(card&&!$('#btnRecoverMaster'))build();});obs.observe(document.body,{childList:true,subtree:true});}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();