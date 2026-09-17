#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')

# Arquivos cujo conteúdo funcional de sincronização não deve ser reescrito.
PROTECTED_CORE = {
    'lib/services/device_sync_service.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/apps_script_http.dart',
    'lib/services/sync_coordinator.dart',
    'lib/services/drive_service.dart',
}


def rel(path: Path) -> str:
    return str(path.relative_to(root)).replace('\\', '/')


def replace_text(path: Path, replacements: list[tuple[str, str]]) -> None:
    if not path.exists() or rel(path) in PROTECTED_CORE:
        return
    text = path.read_text(encoding='utf-8')
    original = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding='utf-8', newline='\n')


# Neutralização de identificadores que não fazem parte do protocolo de sync.
common = [
    ('AuditarSstApp', 'SstGestaoApp'),
    ('AuditarUser', 'SstUser'),
    ('AuditarBrandLogo', 'SstBrandLogo'),
    ('auditarBackgroundSyncDispatcher', 'sstGestaoBackgroundSyncDispatcher'),
    ('auditarLogo', 'systemLogo'),
    ('auditarIcon', 'systemIcon'),
    ('Central de Gestão Auditar', 'Central de Gestão SST'),
    ('Central de Gestao Auditar', 'Central de Gestão SST'),
    ('E-mail: auditarsolucoes@gmail.com / Telefone: (86) 3221-1549',
     'SST Gestão • Segurança e Saúde no Trabalho'),
    ('auditarsolucoes@gmail.com', ''),
    ('(86) 3221-1549', ''),
    ('o Auditar', 'o sistema SST'),
    ('O Auditar', 'O sistema SST'),
    ("'auditar_atual'", "'sst_atual'"),
    ("'auditar_executivo'", "'sst_executivo'"),
    ("'auditar_fotografico'", "'sst_fotografico'"),
    ("'auditar_obra'", "'sst_obra'"),
    ("'auditar_tecnico_clean'", "'sst_tecnico_clean'"),
    ("'auditar_nr12'", "'sst_nr12'"),
    ('"auditar_atual"', '"sst_atual"'),
    ('"auditar_executivo"', '"sst_executivo"'),
    ('"auditar_fotografico"', '"sst_fotografico"'),
    ('"auditar_obra"', '"sst_obra"'),
    ('"auditar_tecnico_clean"', '"sst_tecnico_clean"'),
    ('"auditar_nr12"', '"sst_nr12"'),
    ("mode == 'auditar'", "mode == 'sistema'"),
    ("value: 'auditar'", "value: 'sistema'"),
    ("logoMode: 'auditar'", "logoMode: 'sistema'"),
    ("'auditar_brand_logo.dart'", "'sst_brand_logo.dart'"),
    ('"auditar_brand_logo.dart"', '"sst_brand_logo.dart"'),
    ('../widgets/auditar_brand_logo.dart', '../widgets/sst_brand_logo.dart'),
    ('widgets/auditar_brand_logo.dart', 'widgets/sst_brand_logo.dart'),
]

for path in (root / 'lib').rglob('*.dart'):
    replace_text(path, common)

# A edição neutra não deve procurar/manipular bancos da edição antiga.
main_path = root / 'lib/main.dart'
replace_text(main_path, [
    ("startsWith('auditar_sst')", "startsWith('sst_gestao')"),
    ('startsWith("auditar_sst")', 'startsWith("sst_gestao")'),
])

# Renomeia o arquivo do componente de marca para remover o nome antigo das URIs
# de fonte que podem ser preservadas no binário release.
old_widget = root / 'lib/widgets/auditar_brand_logo.dart'
new_widget = root / 'lib/widgets/sst_brand_logo.dart'
if old_widget.exists():
    if new_widget.exists():
        new_widget.unlink()
    old_widget.rename(new_widget)

# Garante que não restem contatos ou textos comerciais visíveis da edição antiga.
visible_forbidden = [
    'auditarsolucoes@gmail.com',
    '3221-1549',
    'Central de Gestão Auditar',
    'Central de Gestao Auditar',
    'Auditar SST',
    'AUDITAR SST',
    'Auditar Soluções',
    'Auditar Solucoes',
    'Logo Auditar',
    'Padrão Auditar',
]
issues: list[str] = []
for path in (root / 'lib').rglob('*.dart'):
    data = path.read_text(encoding='utf-8', errors='ignore')
    for phrase in visible_forbidden:
        if phrase.lower() in data.lower():
            issues.append(f'{rel(path)}: {phrase}')

# Identificadores seguros que devem ter sido neutralizados fora do núcleo protegido.
internal_forbidden = [
    'AuditarSstApp',
    'AuditarUser',
    'AuditarBrandLogo',
    'auditarBackgroundSyncDispatcher',
    'auditar_atual',
    'auditar_executivo',
    'auditar_fotografico',
    'auditar_obra',
    'auditar_tecnico_clean',
    'auditar_nr12',
]
for path in (root / 'lib').rglob('*.dart'):
    if rel(path) in PROTECTED_CORE:
        continue
    data = path.read_text(encoding='utf-8', errors='ignore')
    for token in internal_forbidden:
        if token in data:
            issues.append(f'{rel(path)}: {token}')

if old_widget.exists():
    issues.append('arquivo legado lib/widgets/auditar_brand_logo.dart ainda existe')
if not new_widget.exists():
    issues.append('arquivo neutro lib/widgets/sst_brand_logo.dart ausente')

if issues:
    raise SystemExit('Neutralização final incompleta: ' + '; '.join(issues[:80]))

print('NEUTRAL_FINAL_IDENTITY_OK: contatos, textos, classes seguras, widget e IDs de relatório neutralizados; núcleo de sync preservado.')
