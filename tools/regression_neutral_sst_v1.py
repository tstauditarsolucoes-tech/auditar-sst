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

assert 'name: sst_gestao' in pub
assert 'version: 1.0.0+1' in pub
assert "assets/branding/sst_icon.png" in brand
assert "assets/branding/sst_logo.png" in brand
assert 'SST Gestão' in (root / 'lib/widgets/auditar_brand_logo.dart').read_text(encoding='utf-8')
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

# Isolamento local. Android e Windows não possuem exatamente a mesma superfície
# de persistência da autenticação, então validamos apenas mecanismos realmente
# existentes em cada base, sem exigir uma chave exclusiva da outra plataforma.
assert 'sst_gestao.db' in database
assert 'auditar_sst.db' not in database
assert 'sst_gestao_auth.json' in auth
assert 'auditar_sst_auth.json' not in auth
assert 'auditar_offline_' not in auth
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

all_text = '\n'.join(
    p.read_text(encoding='utf-8', errors='ignore')
    for p in (root / 'lib').rglob('*.dart')
)
for forbidden in [
    'Auditar SST',
    'AUDITAR SST',
    'Central Auditar',
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
]:
    assert forbidden not in all_text, f'identidade visível remanescente: {forbidden}'

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
]:
    assert (root / rel).exists(), f'arquivo funcional ausente: {rel}'

print('NEUTRAL_REGRESSION_OK: SST Gestão sem identidade visual Auditar; persistência local isolada conforme a plataforma; recursos principais preservados.')
