#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')

pub = (root / 'pubspec.yaml').read_text(encoding='utf-8')
brand = (root / 'lib/brand.dart').read_text(encoding='utf-8')
report_templates = (root / 'lib/services/report_template_service.dart').read_text(encoding='utf-8')
database = (root / 'lib/database.dart').read_text(encoding='utf-8')
auth = (root / 'lib/services/auth_service.dart').read_text(encoding='utf-8')
secure_path = root / 'lib/services/auth_secure_store.dart'
secure = secure_path.read_text(encoding='utf-8') if secure_path.exists() else ''
web = (root / 'lib/services/web_service_config.dart').read_text(encoding='utf-8')
backup = (root / 'lib/services/backup_service.dart').read_text(encoding='utf-8')
main = (root / 'lib/main.dart').read_text(encoding='utf-8')

assert 'name: sst_gestao' in pub
assert 'version: 1.0.0+1' in pub
assert "assets/branding/sst_icon.png" in brand
assert "assets/branding/sst_logo.png" in brand
assert 'SST Gestão' in (root / 'lib/widgets/sst_brand_logo.dart').read_text(encoding='utf-8')
assert not (root / 'lib/widgets/auditar_brand_logo.dart').exists()
assert not (root / 'assets/branding/auditar_icon.png').exists()
assert not (root / 'assets/branding/auditar_icon_transparent.png').exists()
assert not (root / 'assets/branding/auditar_logo.jpg').exists()
assert (root / 'assets/branding/sst_icon.png').exists()
assert (root / 'assets/branding/sst_logo.png').exists()

assert "name: 'Padrão SST'" in report_templates
assert "name: 'Executivo SST'" in report_templates
assert "name: 'Fotográfico SST'" in report_templates
assert "name: 'Obra SST'" in report_templates
assert "name: 'Técnico Clean'" in report_templates
assert "name: 'NR-12 SST'" in report_templates
assert 'useLegacyRenderer: true' in report_templates
for expected in [
    'sst_atual',
    'sst_executivo',
    'sst_fotografico',
    'sst_obra',
    'sst_tecnico_clean',
    'sst_nr12',
]:
    assert expected in report_templates, f'ID neutro de relatório ausente: {expected}'
for legacy in [
    'auditar_atual',
    'auditar_executivo',
    'auditar_fotografico',
    'auditar_obra',
    'auditar_tecnico_clean',
    'auditar_nr12',
]:
    assert legacy not in report_templates, f'ID legado de relatório presente: {legacy}'

# Isolamento local. Android e Windows não possuem exatamente a mesma superfície
# de persistência da autenticação, então validamos apenas mecanismos realmente
# existentes em cada base, sem exigir uma chave exclusiva da outra plataforma.
assert 'sst_gestao.db' in database
assert 'auditar_sst.db' not in database
assert 'sst_gestao_auth.json' in auth
assert 'auditar_sst_auth.json' not in auth
assert 'auditar_offline_' not in auth
assert 'AuditarUser' not in auth
assert 'SstUser' in auth
if 'offline' in auth.lower():
    assert 'sst_gestao_' in auth
if secure:
    assert 'auditar_sst_session_token_v1' not in secure
    if 'session_token' in secure:
        assert 'sst_gestao_session_token_v1' in secure

assert 'SST_APPS_SCRIPT_URL' in web
assert 'SST_SYNC_KEY' in web
assert 'AUDITAR_APPS_SCRIPT_URL' not in web
assert 'AUDITAR_SYNC_KEY' not in web
assert 'SST_Gestao_AutoBackup_' in backup
assert 'SST_Gestao_Backup_Completo_' in backup
assert 'Auditar_SST_AutoBackup_' not in backup
assert 'Auditar_SST_Backup_Completo_' not in backup
assert 'AuditarSstApp' not in main
assert 'SstGestaoApp' in main
assert "startsWith('auditar_sst')" not in main

all_text = '\n'.join(
    p.read_text(encoding='utf-8', errors='ignore')
    for p in (root / 'lib').rglob('*.dart')
)
for forbidden in [
    'Auditar SST',
    'AUDITAR SST',
    'Central Auditar',
    'Central de Gestão Auditar',
    'Central de Gestao Auditar',
    'Padrão Auditar',
    'Auditar Executivo',
    'Auditar Fotográfico',
    'Auditar Obra',
    'Auditar Técnico Clean',
    'Auditar NR-12',
    'Logo Auditar',
    'Auditar + cliente',
    'Somente Auditar',
    'Substituído pela Auditar',
    'auditarsolucoes@gmail.com',
    '3221-1549',
    'AuditarSstApp',
    'AuditarBrandLogo',
    'AuditarUser',
    'auditarBackgroundSyncDispatcher',
    'auditar_brand_logo.dart',
]:
    assert forbidden.lower() not in all_text.lower(), f'identidade remanescente: {forbidden}'

# A edição neutra é um produto separado, mas o motor principal continua presente.
for rel in [
    'lib/services/device_sync_service.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/ai_assistant_service.dart',
    'lib/screens/express_round_screen.dart',
    'lib/screens/report_screen.dart',
    'lib/screens/report_template_library_screen.dart',
    'lib/screens/epi_module_screen.dart',
    'assets/epi_module/field.html',
    'assets/epi_module/management.html',
]:
    assert (root / rel).exists(), f'arquivo funcional ausente: {rel}'

home = (root / 'lib/screens/home_screen.dart').read_text(encoding='utf-8')
assert "tutorialId: 'epi'" in home
assert 'Gestão de EPI' in home
pubspec_text = (root / 'pubspec.yaml').read_text(encoding='utf-8')
assert 'webview_flutter:' in pubspec_text
assert 'webview_flutter_windows:' in pubspec_text
assert 'permission_handler:' in pubspec_text

print('NEUTRAL_REGRESSION_OK: SST Gestão v1.0 com identidade final neutra; persistência isolada; recursos principais preservados.')
