#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard').resolve()

field_src = repo / 'auditar-epi'
management_src = repo / 'auditar-epi-gestao'
module_src = repo / 'neutral_modules' / 'epi'
assets_dir = root / 'assets' / 'epi_module'
pubspec_path = root / 'pubspec.yaml'
home_path = root / 'lib' / 'screens' / 'home_screen.dart'
screen_path = root / 'lib' / 'screens' / 'epi_module_screen.dart'

for path in [field_src, management_src, module_src, pubspec_path, home_path]:
    if not path.exists():
        raise SystemExit('Arquivo/fonte ausente para módulo EPI: ' + str(path))

assets_dir.mkdir(parents=True, exist_ok=True)


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore')


def neutralize(text: str) -> str:
    text = text.replace('AUDITAR', 'SST_GESTAO')
    text = text.replace('Auditar', 'SstGestao')
    text = text.replace('auditar', 'sstGestao')
    text = text.replace('SST_GESTAO EPI', 'GESTÃO EPI')
    text = text.replace('SstGestao EPI', 'Gestão EPI')
    text = text.replace('SstGestao SST', 'SST Gestão')
    return text


def patch_endpoint(js: str) -> str:
    return re.sub(
        r"const\s+ENDPOINT\s*=\s*['\"]https://script\.google\.com/macros/s/[^'\"]+/exec['\"]\s*;",
        "const ENDPOINT=window.SST_EPI_ENDPOINT||'';",
        js,
    )


def strip_local_script(html: str, filename: str) -> str:
    return re.sub(
        r'<script[^>]+src=["\']' + re.escape(filename) + r'["\'][^>]*>\s*</script>',
        '',
        html,
        flags=re.I,
    )


def strip_local_css(html: str) -> str:
    return re.sub(
        r'<link[^>]+href=["\'](?:styles|stock|import-workers|indicators)\.css["\'][^>]*>',
        '',
        html,
        flags=re.I,
    )


def inline_css(paths: list[Path]) -> str:
    css = '\n'.join(read(path) for path in paths if path.exists())
    return '<style>\n' + neutralize(css) + '\n</style>'


def prepare_js(path: Path, field: bool = False) -> str:
    js = patch_endpoint(neutralize(read(path)))

    if field and path.name == 'cloud-sync.js':
        js = js.replace('authToken:token', 'syncKey:token')
        js = js.replace("'Aguardando login'", "'Conectado ao SST Gestão'")

    if field and path.name == 'ai-workers.js':
        js = js.replace("action:'ai_assistant'", "action:'epi_ai_assistant'")

    if path.name == 'app.js' and path.parent.name == 'auditar-epi-gestao':
        js = js.replace(
            "app:{companies:[],workers:[],epis:[],deliveries:[]}",
            "app:{companies:[],workers:[],epis:[],deliveries:[],purchases:[],batches:[],auditLog:[]}",
        )
        js = js.replace(
            "deliveries:Array.isArray(app.deliveries)?app.deliveries:[]}",
            "deliveries:Array.isArray(app.deliveries)?app.deliveries:[],purchases:Array.isArray(app.purchases)?app.purchases:[],batches:Array.isArray(app.batches)?app.batches:[],auditLog:Array.isArray(app.auditLog)?app.auditLog:[]}",
        )

    return js


def build_field() -> str:
    local_scripts = [
        'app.js', 'import-workers.js', 'ai-workers.js', 'stock.js',
        'signature-assist.js', 'biometric-face.js', 'liveness-face.js',
        'company-branding.js', 'auth.js', 'cloud-sync.js',
    ]
    html = strip_local_css(read(field_src / 'index.html'))
    for name in local_scripts:
        html = strip_local_script(html, name)
    html = re.sub(r'<link[^>]+rel=["\']manifest["\'][^>]*>', '', html, flags=re.I)
    html = neutralize(html)
    html = html.replace(
        '</head>',
        inline_css([
            field_src / 'styles.css',
            field_src / 'import-workers.css',
            field_src / 'stock.css',
        ]) + '\n</head>',
        1,
    )

    scripts = [
        field_src / 'app.js',
        field_src / 'import-workers.js',
        field_src / 'ai-workers.js',
        field_src / 'stock.js',
        field_src / 'signature-assist.js',
        field_src / 'biometric-face.js',
        field_src / 'liveness-face.js',
        field_src / 'company-branding.js',
        field_src / 'cloud-sync.js',
    ]
    chunks = ['<script>' + read(module_src / 'bootstrap.js') + '</script>']
    for path in scripts:
        attr = ' data-company-branding="1"' if path.name == 'company-branding.js' else ''
        chunks.append('<script' + attr + '>\n' + prepare_js(path, field=True) + '\n</script>')
    chunks.append('<script>' + read(module_src / 'nf-module.js') + '</script>')
    chunks.append(
        "<script>setTimeout(function(){document.dispatchEvent(new CustomEvent('gestao-epi-auth-ready'));},150);</script>"
    )
    return html.replace('</body>', '\n'.join(chunks) + '\n</body>', 1)


def build_management() -> str:
    local_scripts = [
        'app.js', 'central-config.js', 'indicators.js',
        'auth-gestao.js', 'epi-tools.js', 'company-branding-gestao.js',
    ]
    html = strip_local_css(read(management_src / 'index.html'))
    for name in local_scripts:
        html = strip_local_script(html, name)
    html = neutralize(html)
    html = html.replace(
        '</head>',
        inline_css([
            management_src / 'styles.css',
            management_src / 'indicators.css',
        ]) + '\n</head>',
        1,
    )

    scripts = [
        management_src / 'app.js',
        management_src / 'indicators.js',
        management_src / 'epi-tools.js',
        management_src / 'company-branding-gestao.js',
    ]
    chunks = ['<script>' + read(module_src / 'bootstrap.js') + '</script>']
    for path in scripts:
        chunks.append('<script>\n' + prepare_js(path) + '\n</script>')
    chunks.append('<script>' + read(module_src / 'nf-module.js') + '</script>')
    chunks.append(
        "<script>document.addEventListener('DOMContentLoaded',function(){var x=document.getElementById('connectOverlay');if(x)x.classList.add('hidden');});</script>"
    )
    return html.replace('</body>', '\n'.join(chunks) + '\n</body>', 1)


for name, html in [
    ('field.html', build_field()),
    ('management.html', build_management()),
]:
    if re.search(r'Auditar|AUDITAR|auditar', html):
        raise SystemExit('Identidade antiga encontrada no bundle EPI: ' + name)
    if re.search(r'https://script\.google\.com/macros/s/[^"\']+/exec', html):
        raise SystemExit('Endpoint Apps Script fixo encontrado no bundle EPI: ' + name)
    (assets_dir / name).write_text(html, encoding='utf-8', newline='\n')

shutil.copy2(module_src / 'epi_module_screen.dart', screen_path)

pubspec = read(pubspec_path)
dep_marker = '  qr_flutter: ^4.1.0\n'
if 'webview_flutter:' not in pubspec:
    if dep_marker not in pubspec:
        raise SystemExit('Marcador de dependências não encontrado.')
    pubspec = pubspec.replace(
        dep_marker,
        dep_marker +
        '  webview_flutter: ^4.14.1\n'
        '  webview_flutter_android: ^4.14.1\n'
        '  webview_flutter_windows: ^1.2.0\n'
        '  permission_handler: ^12.0.3\n',
        1,
    )

if 'assets/epi_module/field.html' not in pubspec:
    asset_marker = '  assets:\n'
    if asset_marker not in pubspec:
        raise SystemExit('Bloco assets não encontrado.')
    pubspec = pubspec.replace(
        asset_marker,
        asset_marker +
        '    - assets/epi_module/field.html\n'
        '    - assets/epi_module/management.html\n',
        1,
    )
pubspec_path.write_text(pubspec, encoding='utf-8', newline='\n')

home = read(home_path)
if "import 'epi_module_screen.dart';" not in home:
    marker = "import 'dashboard_screen.dart';\n"
    if marker not in home:
        raise SystemExit('Marcador de imports da Home não encontrado.')
    home = home.replace(marker, marker + "import 'epi_module_screen.dart';\n", 1)

if "tutorialId: 'epi'" not in home:
    marker = """        _ModuleData(
          title: 'Treinamentos',"""
    module = """        _ModuleData(
          title: 'Gestão de EPI',
          tutorialId: 'epi',
          subtitle: 'Estoque, entregas, CA, NF com IA, assinatura e indicadores',
          icon: Icons.health_and_safety_outlined,
          color: const Color(0xFF16836B),
          page: () => const EpiModuleScreen(),
        ),
"""
    if marker not in home:
        raise SystemExit('Marcador de módulos da Home não encontrado.')
    home = home.replace(marker, module + marker, 1)

home = home.replace(
    "      'workers',\n      'trainings',",
    "      'workers',\n      'epi',\n      'trainings',",
)
home = home.replace(
    "      'workers',\n      'compliance_alerts',",
    "      'workers',\n      'epi',\n      'compliance_alerts',",
)
home_path.write_text(home, encoding='utf-8', newline='\n')

print(
    'NEUTRAL_EPI_MODULE_OK: módulo Campo + Gestão de EPI incorporado; '
    'fontes originais preservadas.'
)
