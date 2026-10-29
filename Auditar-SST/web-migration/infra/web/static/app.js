(async function verifySandboxApi() {
  const status = document.getElementById('api-status');
  const panel = status && status.closest('.status');
  if (!status || !panel) return;
  try {
    const response = await fetch('/api/v1/health', { cache: 'no-store', credentials: 'omit' });
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const data = await response.json();
    if (!data.ok || data.productionDataConnected !== false) throw new Error('Resposta inesperada');
    status.textContent = 'API de homologação operacional — sem dados reais.';
    panel.classList.add('ok');
  } catch (_) {
    status.textContent = 'API de homologação indisponível. Verifique os contêineres.';
    panel.classList.add('fail');
  }
})();
