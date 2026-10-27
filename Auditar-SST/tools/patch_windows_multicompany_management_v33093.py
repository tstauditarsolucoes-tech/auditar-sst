#!/usr/bin/env python3
"""Auditar SST Windows v3.30.93 — Gestão Multempresa.

Somente leitura e navegação:
- copia a tela de carteira multempresa;
- destaca o acesso na Home desktop;
- preserva mobile e núcleo protegido;
- não altera schema, sincronização, autenticação, HTTP, mídia, IA ou Apps Script.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_windows_multicompany_management_v33093.py <APP_DIR>")

root = Path(sys.argv[1])
repo = Path(__file__).resolve().parents[1]

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

protected = [
    "lib/database.dart",
    "lib/models.dart",
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "lib/services/offline_report_knowledge_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected if (root / name).exists()
}

source = repo / "feature_sources/company_portfolio_management_screen_v33093.dart"
target = root / "lib/screens/company_portfolio_management_screen.dart"
if not source.exists():
    raise RuntimeError("fonte Gestão Multempresa ausente")
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, target)

rel = "lib/screens/home_screen.dart"
home = read(rel)

imp = "import 'company_portfolio_management_screen.dart';\n"
if imp not in home:
    anchor = "import 'companies_screen.dart';\n"
    if anchor not in home:
        raise RuntimeError("anchor companies_screen ausente")
    home = home.replace(anchor, anchor + imp, 1)

# Botão principal da lateral: carteira multempresa.
if "label: const Text('Gestão Multempresa')" not in home:
    marker = "label: const Text('Central de Gestão'),"
    pos = home.find(marker)
    if pos < 0:
        raise RuntimeError("botão lateral da Home Executiva não encontrado")
    route = "const FieldOperationalControlScreen()"
    route_pos = home.rfind(route, max(0, pos - 500), pos)
    if route_pos < 0:
        raise RuntimeError("rota lateral da Central de Gestão não encontrada")
    home = (
        home[:route_pos]
        + "const CompanyPortfolioManagementScreen()"
        + home[route_pos + len(route):]
    )
    icon_pos = home.rfind(
        "Icons.query_stats_rounded",
        max(0, pos - 500),
        pos + 200,
    )
    if icon_pos >= 0:
        home = (
            home[:icon_pos]
            + "Icons.apartment_rounded"
            + home[icon_pos + len("Icons.query_stats_rounded"):]
        )
    home = home.replace(
        "label: const Text('Central de Gestão'),",
        "label: const Text('Gestão Multempresa'),",
        1,
    )

# Item gerencial logo no topo da navegação.
if "Todas as empresas por prioridade" not in home:
    title_pos = home.find("'Painel executivo'")
    if title_pos < 0:
        raise RuntimeError("item Painel executivo da navegação não encontrado")
    tile_pos = home.rfind("ListTile(", max(0, title_pos - 500), title_pos)
    if tile_pos < 0:
        raise RuntimeError("início do item Painel executivo não encontrado")
    multempresa_tile = """ListTile(
                      dense: true,
                      leading: const Icon(
                        Icons.apartment_rounded,
                        color: AuditarBrand.greenDark,
                      ),
                      title: const Text(
                        'Gestão Multempresa',
                        style: TextStyle(fontWeight: FontWeight.w900),
                      ),
                      subtitle: const Text(
                        'Todas as empresas por prioridade',
                        style: TextStyle(fontSize: 10),
                      ),
                      onTap: () => _open(
                        const CompanyPortfolioManagementScreen(),
                      ),
                    ),
                    """
    home = home[:tile_pos] + multempresa_tile + home[tile_pos:]

# CTA principal no hero passa a abrir a carteira completa.
if "'Ver todas as empresas'" not in home:
    label_marker = "'Abrir Central de Gestão'"
    label_pos = home.find(label_marker)
    if label_pos < 0:
        raise RuntimeError("CTA principal da Home não encontrado")
    route = "const FieldOperationalControlScreen()"
    route_pos = home.rfind(route, max(0, label_pos - 900), label_pos)
    if route_pos < 0:
        raise RuntimeError("rota do CTA principal não encontrada")
    home = (
        home[:route_pos]
        + "const CompanyPortfolioManagementScreen()"
        + home[route_pos + len(route):]
    )
    icon_pos = home.rfind(
        "Icons.present_to_all_rounded",
        max(0, label_pos - 900),
        label_pos,
    )
    if icon_pos >= 0:
        home = (
            home[:icon_pos]
            + "Icons.apartment_rounded"
            + home[icon_pos + len("Icons.present_to_all_rounded"):]
        )
    home = home.replace(
        "'Abrir Central de Gestão'",
        "'Ver todas as empresas'",
        1,
    )

old_hint = "Selecione a empresa para abrir o Painel Executivo"
new_hint = "Carteira geral com prioridades de todas as empresas"
if old_hint in home:
    home = home.replace(old_hint, new_hint, 1)

home = home.replace(
    "Auditar SST para Windows • versão 3.30.92",
    "Auditar SST para Windows • versão 3.30.93",
)
write(rel, home)

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old = "version: 3.30.92+279"
new = "version: 3.30.93+280"
if pub.count(old) != 1:
    raise RuntimeError("versão base v3.30.92 não encontrada")
write(pub_rel, pub.replace(old, new, 1))

screen = read("lib/screens/company_portfolio_management_screen.dart")
required = [
    "Gestão Multempresa",
    "Visão gerencial de todas as empresas acompanhadas",
    "Prioridade alta",
    "Ações vencidas",
    "Trein. vencidos",
    "Última vistoria",
    "FieldOperationalControlScreen",
]
missing = [item for item in required if item not in screen]
if missing:
    raise RuntimeError("Gestão Multempresa incompleta: " + repr(missing))

after = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected if (root / name).exists()
}
changed = [name for name in before if before[name] != after[name]]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

final_home = read(rel)
assert "CompanyPortfolioManagementScreen" in final_home
assert "Gestão Multempresa" in final_home
assert "Ver todas as empresas" in final_home
assert "Widget _mobileBody()" in final_home
assert "version: 3.30.93+280" in read(pub_rel)

print("WINDOWS_MULTICOMPANY_MANAGEMENT_OK")
print("PORTFOLIO_READ_ONLY_OK")
print("MOBILE_PATH_PRESERVED_OK")
print("PROTECTED_CORE_BYTE_IDENTICAL_OK")
