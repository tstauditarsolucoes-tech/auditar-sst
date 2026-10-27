#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])
version=sys.argv[2]
pub=(root/'pubspec.yaml').read_text(encoding='utf-8')
screen=(root/'lib/screens/management_panel_screen.dart').read_text(encoding='utf-8')

assert f'version: {version}' in pub

for marker in [
    "import '../services/media_sync_service.dart';",
    'MediaSyncService.restoreCompanyLogos',
    'resolvedCompanyLogoPath',
    'companyLogoAspectRatio',
    'ui.instantiateImageCodec',
    "'Resumo executivo'",
    "'Itens que exigem prioridade'",
    "'PAINEL ATIVO'",
    '_headerMetaChip',
    'maxColumns: 6',
    'companyAccent',
    'companyAccentDark',
]:
    assert marker in screen, marker

for forbidden in [
    'DeviceSyncService.synchronize',
    'SyncCoordinator',
    'media_upload',
    'device_push',
    'device_pull',
]:
    assert forbidden not in screen, 'Painel alterou sincronizacao: '+forbidden

print('MANAGEMENT_PANEL_REFINED_REGRESSION_OK',version)
