#!/usr/bin/env python3
"""Montar em /tmp um Flutter *fake* de teste APR/AR/PT/PET/assinaturas.

Usa fontes reais de serviço, telas e PDFs da feature branch, porém
substitui banco, autenticação e modelos da empresa por STUBS. Não há
conexão com servidor, banco de clientes, telefone ou apps instalados.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Uso: stage_sst_risk_docs_fixture_v1.py <DIRETORIO_FLUTTER>")

repo = Path(__file__).resolve().parents[1]
app = Path(sys.argv[1]).resolve()
pubspec = app / "pubspec.yaml"
if not pubspec.is_file() or "name: auditar_sst" not in pubspec.read_text():
    raise SystemExit("Projeto Flutter de teste inválido")
if not (app / "lib").is_dir() or not (app / "test").is_dir():
    raise SystemExit("Estrutura Flutter de teste incompleta")
if "/tmp/" not in str(app) and not str(app).startswith("/tmp"):
    raise SystemExit("Somente diretórios temporários são permitidos")

raw = pubspec.read_text(encoding="utf-8")
anchor = "\ndependencies:\n"
assert raw.count(anchor) == 1
raw = raw.replace(anchor, anchor + """  pdf: ^3.11.1
  printing: ^5.13.4
  signature: ^5.5.0
""", 1)
pubspec.write_text(raw, encoding="utf-8")

sources = {
    "sst_scope_key_v1.dart": "lib/services/sst_scope_key.dart",
    "sst_risk_documents_models_v1.dart":
        "lib/services/sst_risk_documents_models.dart",
    "sst_risk_documents_pdf_v1.dart":
        "lib/services/sst_risk_documents_pdf.dart",
    "sst_risk_documents_screen_v1.dart":
        "lib/screens/sst_risk_documents_screen.dart",
    "sst_risk_documents_test_v1.dart":
        "test/sst_risk_documents_test.dart",
    "sst_pet_nr33_models_v1.dart":
        "lib/services/sst_pet_nr33_models.dart",
    "sst_pet_nr33_pdf_v1.dart":
        "lib/services/sst_pet_nr33_pdf.dart",
    "sst_pet_nr33_screen_v1.dart":
        "lib/screens/sst_pet_nr33_screen.dart",
    "sst_pet_nr33_test_v1.dart":
        "test/sst_pet_nr33_test.dart",
    "sst_activity_guide_models_v1.dart":
        "lib/services/sst_activity_guide_models.dart",
    "sst_activity_guide_screen_v1.dart":
        "lib/screens/sst_activity_guide_screen.dart",
    "sst_activity_guide_test_v1.dart":
        "test/sst_activity_guide_test.dart",
    "sst_document_signature_models_v1.dart":
        "lib/services/sst_document_signature_models.dart",
    "sst_document_signature_panel_v1.dart":
        "lib/screens/sst_document_signature_panel.dart",
    "sst_document_signature_test_v1.dart":
        "test/sst_document_signature_test.dart",
    "sst_scope_key_test_v1.dart":
        "test/sst_scope_key_test.dart",
    "sst_risk_docs_widget_smoke_test_v1.dart":
        "test/sst_risk_docs_widget_smoke_test.dart",
}
for filename, relative in sources.items():
    source = repo / "feature_sources" / filename
    if not source.is_file():
        raise SystemExit("Fonte faltante: " + filename)
    dest = app / relative
    if dest.exists():
        raise SystemExit("Recusar sobrescrever arquivo existente: " + relative)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

stubs = {
    "lib/models.dart": """class Company {
  const Company({required this.id, required this.name});
  final String id, name;
}
""",
    "lib/database.dart": """class AppDatabase {
  AppDatabase._();
  static final instance = AppDatabase._();
  static String activeUserId = 'test-user';
  static final Map<String, String> _settings = <String, String>{};

  Future<String> getSetting(String key) async => _settings[key] ?? '';

  Future<void> setSetting(String key, String value) async {
    _settings[key] = value;
  }
}
""",
    "lib/services/auth_service.dart": """class AuthService {
  static bool canAccessCompany(String id) => id == 'company-A';
}
""",
}
for relative, source in stubs.items():
    file = app / relative
    if file.exists():
        raise SystemExit("Stub sobrescreveria fonte real: " + relative)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(source, encoding="utf-8")

widget = app / "test/widget_test.dart"
if widget.exists():
    widget.unlink()

# A assinatura PDF precisa manter fallback quando a logomarca não estiver
# disponível nesta fixture (não incluímos assets de clientes).
print("SST_RISK_DOCS_FIXTURE_READY: projeto temporario e stubs sem backend")
