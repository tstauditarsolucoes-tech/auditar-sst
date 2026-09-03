function doPost(e) {
  try {
    const request = JSON.parse((e.postData && e.postData.contents) || '{}');
    const props = PropertiesService.getScriptProperties();
    const expectedKey = props.getProperty('AUDITAR_EPI_SYNC_KEY');

    if (!expectedKey) {
      return jsonResponse_({
        ok: false,
        message: 'Central Auditar EPI ainda não configurada.'
      });
    }

    if (request.syncKey !== expectedKey) {
      return jsonResponse_({
        ok: false,
        message: 'Chave de sincronização inválida.'
      });
    }

    if (request.action === 'epi_sync_merge') {
      return jsonResponse_(epiSyncMerge_(request));
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
