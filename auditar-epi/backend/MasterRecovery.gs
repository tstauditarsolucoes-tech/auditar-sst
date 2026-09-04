// Recuperação segura do acesso ao Painel Mestre.
// Valida a mesma chave de instalação do Apps Script e preserva todos os clientes e dados.

var __gestaoEpiRecoveryBaseDoPost = doPost;

doPost = function(e) {
  try {
    var request = JSON.parse((e.postData && e.postData.contents) || '{}');
    if (String(request.action || '') === 'master_recover_access') {
      return jsonResponse_(masterRecoverAccessExt_(request));
    }
  } catch (error) {
    return jsonResponse_({ok:false,message:String(error)});
  }
  return __gestaoEpiRecoveryBaseDoPost(e);
};

function masterRecoverAccessExt_(request) {
  var props = PropertiesService.getScriptProperties();
  var expected = String(props.getProperty('AUDITAR_EPI_SYNC_KEY') || '').trim();
  var supplied = String(request.setupKey || '').trim();
  if (!expected || supplied !== expected) {
    Utilities.sleep(350);
    return {ok:false,message:'Chave de instalação inválida.'};
  }

  var username = commercialNormalizeUsername_(request.username);
  var password = String(request.password || '');
  var name = String(request.name || '').trim() || username;
  commercialValidateUsernamePassword_(username,password);

  var lock = LockService.getScriptLock();
  lock.waitLock(12000);
  try {
    var system = commercialLoadSystem_();
    var user = commercialNewUser_(username,name,'master',password);

    // Substitui somente os administradores do Painel Mestre.
    // Clientes, empresas, usuários dos clientes e dados operacionais permanecem intactos.
    system.masterUsers = [user];
    system.updatedAt = new Date().toISOString();

    // Invalida sessões antigas após uma recuperação de credenciais.
    var newSecret = Utilities.getUuid().replace(/-/g,'') + Utilities.getUuid().replace(/-/g,'');
    props.setProperty(GESTAO_COM_AUTH_SECRET_PROP,newSecret);

    commercialSaveSystem_(system);
    return {
      ok:true,
      message:'Acesso do Painel Mestre redefinido.',
      token:commercialCreateToken_({scope:'master',user:user}),
      user:commercialPublicUser_(user)
    };
  } catch (error) {
    return {ok:false,message:'Não foi possível redefinir o acesso: ' + String(error)};
  } finally {
    lock.releaseLock();
  }
}
