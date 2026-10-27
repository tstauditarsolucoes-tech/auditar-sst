#!/usr/bin/env python3
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / 'app' / 'Auditar_SST_v1_5_dashboard'


def rep(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


# Remove a duplicação temporária do SyncCoordinator. O DeviceSyncService já é
# o dono do fluxo de mídia e respeita a janela de sincronização existente.
p = APP / 'lib/services/sync_coordinator.dart'
t = p.read_text(encoding='utf-8')
t = rep(
    t,
    "import 'management_panel_service.dart';\nimport 'media_sync_service.dart';\n",
    "import 'management_panel_service.dart';\n",
    'import duplicado no coordenador',
)
t = rep(
    t,
    '''      // Protege online logos antigas antes de enviar os metadados.
      try {
        await MediaSyncService.uploadPendingCompanyLogos().timeout(
          const Duration(seconds: 25),
        );
      } catch (_) {}

      DeviceSyncResult? result;
''',
    '''      DeviceSyncResult? result;
''',
    'upload duplicado no coordenador',
)
t = rep(
    t,
    '''      if (result != null) {
        // Após receber os metadados, restaura do Drive as logos ausentes.
        try {
          await MediaSyncService.downloadCompanyLogos().timeout(
            const Duration(seconds: 25),
          );
        } catch (_) {}
        _setDesktopStatus(
''',
    '''      if (result != null) {
        _setDesktopStatus(
''',
    'download duplicado no coordenador',
)
p.write_text(t, encoding='utf-8')


# Coloca a migração de logos antigas exatamente antes da fila geral de mídias.
p = APP / 'lib/services/device_sync_service.dart'
t = p.read_text(encoding='utf-8')
t = rep(
    t,
    '''      try {
        await MediaSyncService.uploadPending();
      } catch (_) {
        // A falha de uma foto não bloqueia a sincronização dos demais dados.
      }
''',
    '''      try {
        // Logos ficam na frente da fila geral. Isso garante que uma logo já
        // existente em versões anteriores seja protegida online mesmo quando
        // há muitas fotos pendentes para envio.
        await MediaSyncService.uploadPendingCompanyLogos();
        await MediaSyncService.uploadPending();
      } catch (_) {
        // A falha de uma mídia não bloqueia a sincronização dos demais dados.
      }
''',
    'prioridade de upload da logo',
)
p.write_text(t, encoding='utf-8')


media = (APP / 'lib/services/media_sync_service.dart').read_text(encoding='utf-8')
device = (APP / 'lib/services/device_sync_service.dart').read_text(encoding='utf-8')
coord = (APP / 'lib/services/sync_coordinator.dart').read_text(encoding='utf-8')
if 'uploadCompanyLogoNow' not in media:
    raise RuntimeError('Upload imediato da logo foi perdido')
if 'await MediaSyncService.uploadPendingCompanyLogos();' not in device:
    raise RuntimeError('Prioridade da logo não entrou no DeviceSyncService')
# A v3.29.17 já prioriza company_logo em downloadMissing(). A restauração usa
# essa fila geral existente, evitando criar uma segunda rotina concorrente.
if 'MediaSyncService.downloadMissing' not in device:
    raise RuntimeError('Fila de restauração de mídias após sincronização foi perdida')
if "CASE WHEN entity_type = 'company_logo' THEN 0 ELSE 1 END" not in media:
    raise RuntimeError('Prioridade da logo na restauração foi perdida')
if "import 'media_sync_service.dart';" in coord:
    raise RuntimeError('SyncCoordinator ainda contém sincronização de mídia duplicada')

print('v3.29.19: upload imediato e recuperação priorizada da logo integrados sem duplicar o coordenador.')
