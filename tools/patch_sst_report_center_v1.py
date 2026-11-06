#!/usr/bin/env python3
"""Instala a Central de Relatórios SST (6 entradas) sem substituir relatórios atuais.

É necessário executar APÓS os patches gerenciais e da biblioteca técnica.
Modifica SOMENTE atalho da empresa e parâmetro inicial do relatório gerencial,
e adiciona arquivos novos. Não toca em banco, sincronização, fotos antigas,
login, autenticação, Apps Script, IA, PDF do relatório padrão ou registros.
"""
from pathlib import Path
import hashlib
import re
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_sst_report_center_v1.py <APP_DIR>")
app=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
company=app/"lib/screens/company_detail_screen.dart"
manager=app/"lib/screens/manager_reports_screen.dart"
for p in [company,manager]:
    assert p.is_file(), "App sem a tela existente: "+str(p)

files={
    "feature_sources/sst_report_center_models_v1.dart":
        app/"lib/services/sst_report_center_models.dart",
    "feature_sources/sst_report_center_pdf_v1.dart":
        app/"lib/services/sst_report_center_pdf.dart",
    "feature_sources/sst_report_center_screen_v1.dart":
        app/"lib/screens/sst_report_center_screen.dart",
    "feature_sources/sst_report_center_models_test_v1.dart":
        app/"test/sst_report_center_models_test.dart",
}
assert not any(p.exists() for p in files.values()), (
    "Central de Relatórios já instalada; recusar duplicação.")

allowed={company,manager,*files.values()}
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in [app/"lib",app/"test",app/"painel_web_google_apps_script"]
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in allowed
}
def once(text,old,new,label):
    count=text.count(old)
    if count!=1:raise RuntimeError(label+" distinto da origem: "+str(count))
    return text.replace(old,new,1)

s=company.read_text(encoding="utf-8")
s=once(s,"import 'manager_reports_screen.dart';",
    "import 'manager_reports_screen.dart';\n"
    "import 'sst_report_center_screen.dart';",
    "importação atalho empresa")
rx=re.compile(
    r"(?P<space>^[ \t]*)_shortcut\(\s*\n\s*icon:\s*"
    r"Icons\.summarize_outlined,\s*\n\s*title:\s*"
    r"'Relatórios gerenciais',",
    flags=re.M,
)
matches=list(rx.finditer(s))
if len(matches)!=1:raise RuntimeError(
    "Atalho de relatórios gerenciais esperado uma vez: "+str(len(matches)))
m=matches[0]
indent=m.group("space")
entry="""_shortcut(
  icon: Icons.library_books_outlined,
  title: 'Central de Relatórios SST',
  subtitle: 'Máquinas, obras, elétrica, altura, ocorrências e gerencial mensal',
  onTap: () => _open(SstReportCenterScreen(company: widget.company)),
),
"""
entry="\n".join(indent+line for line in entry.splitlines())+"\n"
s=s[:m.start()]+entry+s[m.start():]

g=manager.read_text(encoding="utf-8")
g=once(g,"  final Company company;\n  const ManagerReportsScreen({super.key, required this.company});",
    "  final Company company;\n  final ManagerReportKind initialKind;\n"
    "  const ManagerReportsScreen({super.key, required this.company,\n"
    "    this.initialKind = ManagerReportKind.pending});",
    "Relatório gerencial com seleção inicial")
g=once(g,"  ManagerReportKind kind = ManagerReportKind.pending;",
    "  late ManagerReportKind kind;",
    "Tipo gerencial inicial")
g=once(g,"  void initState() { super.initState(); _load(); }",
    "  void initState() {\n"
    "    super.initState();\n"
    "    kind=widget.initialKind;\n"
    "    _load();\n"
    "  }",
    "Carregar relatório mensal como padrão da central")

# Somente depois de validar TODOS os anchors copiamos os arquivos.
for source,target in files.items():
    content=(repo/source).read_text(encoding="utf-8")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(content,encoding="utf-8",newline="\n")
company.write_text(s,encoding="utf-8",newline="\n")
manager.write_text(g,encoding="utf-8",newline="\n")
for p,d in protected.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest()==d, (
        "Arquivo protegido alterado: "+str(p))
assert s.count("SstReportCenterScreen(company: widget.company)")==1
assert g.count("this.initialKind = ManagerReportKind.pending")==1
print("SST_REPORT_CENTER_SIX_ENTRY_READY_NO_CORE_CHANGES")
