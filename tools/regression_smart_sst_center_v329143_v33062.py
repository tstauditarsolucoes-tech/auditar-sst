#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1])
home=(root/"lib/screens/home_screen.dart").read_text(encoding="utf-8")
center=(root/"lib/screens/smart_sst_center_screen.dart").read_text(encoding="utf-8")
for snippet in [
    "import 'smart_sst_center_screen.dart';",
    "tutorialId: 'smart_center'",
    "page: () => const SmartSstCenterScreen()",
]:
    assert snippet in home, snippet
for snippet in [
    "class SmartSstCenterScreen",
    "Buscar em todo o app",
    "O que precisa da sua atenção",
    "Atalhos favoritos",
    "Atuação recente da Auditar",
    "Linha do tempo",
    "Recorrências",
    "Evidências",
    "ACAO_AUDITAR",
    "smart_sst_center_favorites",
    "Diagnóstico técnico • ADM",
    "MediaSyncService.pendingCount()",
]:
    assert snippet in center, snippet
for forbidden in ["AppsScriptHttp","SyncCoordinator","media_upload","AUDITAR_SYNC_KEY"]:
    assert forbidden not in center, forbidden
print("SMART_SST_CENTER_REGRESSION_OK")
