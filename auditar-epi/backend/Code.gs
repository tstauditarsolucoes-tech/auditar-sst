function doPost(e) {
  try {
    const request = JSON.parse((e.postData && e.postData.contents) || '{}');
    const props = PropertiesService.getScriptProperties();
    const expectedKey = props.getProperty('AUDITAR_EPI_SYNC_KEY');

    if (!expectedKey) {
      return jsonResponse_({
        ok: false,
        message: 'Central Gestão EPI ainda não configurada.'
      });
    }

    if (request.syncKey !== expectedKey) {
      return jsonResponse_({
        ok: false,
        message: 'Chave da central inválida.'
      });
    }

    if (request.action === 'auth_status') {
      return jsonResponse_(authStatus_());
    }

    if (request.action === 'auth_bootstrap_admin') {
      return jsonResponse_(authBootstrapAdmin_(request));
    }

    if (request.action === 'auth_login') {
      return jsonResponse_(authLogin_(request));
    }

    if (request.action === 'auth_me') {
      return jsonResponse_(authMe_(request));
    }

    if (request.action === 'auth_list_users') {
      return jsonResponse_(authListUsers_(request));
    }

    if (request.action === 'auth_create_user') {
      return jsonResponse_(authCreateUser_(request));
    }

    if (request.action === 'auth_update_user') {
      return jsonResponse_(authUpdateUser_(request));
    }

    if (request.action === 'auth_change_password') {
      return jsonResponse_(authChangeOwnPassword_(request));
    }

    if (request.action === 'epi_sync_merge') {
      const session = authValidateToken_(request.authToken);
      if (!session.ok) return jsonResponse_(session);

      if (session.user.role === 'consulta') {
        const data = readEpiSnapshot_();
        return jsonResponse_({
          ok: true,
          revision: Number(data.revision || 0),
          updatedAt: String(data.updatedAt || ''),
          payload: data,
          readOnly: true,
          user: session.user,
          message: 'Consulta sincronizada em modo somente leitura.'
        });
      }

      const result = epiSyncMerge_(request);
      if (result && result.ok) result.user = session.user;
      return jsonResponse_(result);
    }

    return jsonResponse_({
      ok: false,
      message: 'Ação não reconhecida.'
    });
  } catch (error) {
    return jsonResponse_({
      ok: false,
      message: String(error)
    });
  }
}

function jsonResponse_(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
