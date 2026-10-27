"""Add document hub/navigation without touching sync, AI, database schema or GS."""
from pathlib import Path
import shutil, sys

root = Path(sys.argv[1])
feature = Path(__file__).resolve().parent.parent / "feature_sources"
for name, subdir in (
    ("document_center_screen.dart", "screens"),
    ("document_delivery_service.dart", "services"),
):
    source = feature / name
    assert source.is_file(), name
    target = root / "lib" / subdir / name
    target.write_bytes(source.read_bytes())

def update(relative, old, new):
    p = root / relative
    text = p.read_text(encoding="utf-8")
    assert text.count(old) == 1, (relative, old[:85], text.count(old))
    p.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")

# Enterprise detail: company-specific central, not a global mixing of tenants.
update("lib/screens/company_detail_screen.dart",
       "import 'action_plan_screen.dart';",
       "import 'document_center_screen.dart';\nimport 'action_plan_screen.dart';")
update("lib/screens/company_detail_screen.dart",
       """          _shortcut(
            icon: Icons.monitor_heart_outlined,
            title: 'Painel Gerencial',""",
       """          _shortcut(
            icon: Icons.folder_copy_outlined,
            title: 'Central de Documentos e Envios',
            subtitle: 'Vistorias, rondas, fichas, PDFs e histórico desta empresa',
            onTap: () => _open(DocumentCenterScreen(company: widget.company)),
          ),
          const SizedBox(height: 10),
          _shortcut(
            icon: Icons.monitor_heart_outlined,
            title: 'Painel Gerencial',""")

# Existing report button uses same Gmail route but records success in local ledger.
update("lib/screens/report_screen.dart",
       "import '../services/report_email_service.dart';",
       "import '../services/report_email_service.dart';\nimport '../services/document_delivery_service.dart';")
update("lib/screens/report_screen.dart",
       """      final message = await ReportEmailService.send(
        companyId: company.id,
        companyName: company.name,
        inspectionId: widget.inspectionId,""",
       """      final message = await DocumentDeliveryService.send(
        company: company,
        documentId: 'inspection:' + widget.inspectionId,
        documentType: 'Vistorias',
        title: 'Relatório de vistoria',""")

# Direct per-module access opens the hub pre-selecting the current document.
update("lib/screens/document_center_screen.dart",
       "  final Company company;\n  const DocumentCenterScreen({super.key, required this.company});",
       "  final Company company;\n  final String? initialDocumentId;\n  const DocumentCenterScreen({super.key, required this.company, this.initialDocumentId});")
update("lib/screens/document_center_screen.dart",
       """        (value)=>!items.any((i)=>i.id==value));loading=false; });""",
       """        (value)=>!items.any((i)=>i.id==value));
        if (widget.initialDocumentId != null &&
          items.any((i)=>i.id==widget.initialDocumentId)) {
          chosen.add(widget.initialDocumentId!);
        }
        loading=false; });""")

update("lib/screens/safety_observations_screen.dart",
       "import '../services/safety_observation_pdf_service.dart';",
       "import '../services/safety_observation_pdf_service.dart';\nimport 'document_center_screen.dart';")
update("lib/screens/safety_observations_screen.dart",
       """            tooltip: 'Gerar relatório PDF',
            onPressed:
                records.isEmpty || generatingReport ? null : _shareReport,""",
       """            tooltip: 'Gerar relatório PDF',
            onPressed:
                records.isEmpty || generatingReport ? null : _shareReport,""")
# Put a separate send icon next to existing PDF, without replacing it.
p = root / "lib/screens/safety_observations_screen.dart"
text = p.read_text(encoding="utf-8")
start = text.index("title: const Text(\n          'Atos e condições inseguras',")
point = text.index("        actions: [", start) + len("        actions: [")
text = text[:point] + """
          IconButton(
            tooltip: 'Selecionar e enviar documentos desta empresa',
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => DocumentCenterScreen(
                company: widget.company, initialDocumentId: 'observations:all'))),
            icon: const Icon(Icons.outgoing_mail_outlined),
          ),""" + text[point:]
p.write_text(text, encoding="utf-8", newline="\n")

update("lib/screens/express_round_screen.dart",
       "import '../services/express_round_pdf_service.dart';",
       "import '../services/express_round_pdf_service.dart';\nimport 'document_center_screen.dart';")
update("lib/screens/express_round_screen.dart",
       """            tooltip: 'Histórico de rondas',
            onPressed: _showRoundsArchive,""",
       """            tooltip: 'Histórico de rondas',
            onPressed: _showRoundsArchive,""")
p = root / "lib/screens/express_round_screen.dart"
text = p.read_text(encoding="utf-8")
start = text.index("      appBar: AppBar(\n        title: Text(\n          viewingHistoricalRound")
point = text.index("        actions: [", start) + len("        actions: [")
text = text[:point] + """
          IconButton(
            tooltip: 'Enviar relatório desta ronda',
            onPressed: roundRecords.isEmpty ? null : () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => DocumentCenterScreen(
                company: widget.company, initialDocumentId: 'round:' + roundId))),
            icon: const Icon(Icons.outgoing_mail_outlined),
          ),""" + text[point:]
p.write_text(text, encoding="utf-8", newline="\n")

update("lib/screens/training_records_screen.dart",
       "import '../services/training_record_pdf_service.dart';",
       "import '../services/training_record_pdf_service.dart';\nimport 'document_center_screen.dart';")
update("lib/screens/training_records_screen.dart",
       """            tooltip: 'Pré-admissão / integração',
            onPressed: _managePreAdmissions,""",
       """            tooltip: 'Pré-admissão / integração',
            onPressed: _managePreAdmissions,""")
p = root / "lib/screens/training_records_screen.dart"
text = p.read_text(encoding="utf-8")
start = text.index("      appBar: AppBar(\n        title: const Text('Treinamentos realizados')")
point = text.index("        actions: [",start)+len("        actions: [")
text = text[:point] + """
          if (current != null) IconButton(
            tooltip: 'Enviar fichas e consultar histórico',
            onPressed: () => Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => DocumentCenterScreen(company: current))),
            icon: const Icon(Icons.outgoing_mail_outlined),
          ),""" + text[point:]
start = text.index("      appBar: AppBar(\n        title: const Text('Registro do treinamento'),\n        actions: [")
point = text.index("        actions: [",start)+len("        actions: [")
text = text[:point] + """
          IconButton(
            tooltip: 'Enviar esta ficha de treinamento',
            onPressed: busy ? null : () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => DocumentCenterScreen(
                company: widget.company, initialDocumentId: 'training:' + widget.recordId))),
            icon: const Icon(Icons.outgoing_mail_outlined),
          ),""" + text[point:]
p.write_text(text, encoding="utf-8", newline="\n")

# DDS: email action selects the current signed attendance sheet, other
# document categories reach the same central from the company detail.
update("lib/screens/sst_records_screen.dart",
       "import '../services/dds_pdf_service.dart';",
       "import '../services/dds_pdf_service.dart';\nimport 'document_center_screen.dart';")
p = root / "lib/screens/sst_records_screen.dart"
text = p.read_text(encoding="utf-8")
needle = "if (value == 'pdf') _generateDdsPdf(record);"
assert text.count(needle) == 1
text = text.replace(needle, needle + """
                  if (value == 'email') _openDdsDelivery(record);""",1)
needle = """                      if (record.type == 'DDS')
                        const PopupMenuItem(
                          value: 'pdf',"""
assert text.count(needle) == 1
text = text.replace(needle, """                      if (record.type == 'DDS')
                        const PopupMenuItem(
                          value: 'email',
                          child: Text('Enviar ficha por e-mail'),
                        ),
""" + needle,1)
needle = "  Future<void> _generateDdsPdf(SstRecord record) async {"
assert text.count(needle) == 1
text = text.replace(needle, """  Future<void> _openDdsDelivery(SstRecord record) async {
    final companies = await AppDatabase.instance.getCompanies(onlyActive: false);
    for (final company in companies) {
      if (company.id != record.companyId) continue;
      if (!mounted) return;
      await Navigator.of(context).push(MaterialPageRoute(
        builder: (_) => DocumentCenterScreen(
          company: company, initialDocumentId: 'dds:' + record.id)));
      return;
    }
  }

""" + needle,1)
p.write_text(text, encoding="utf-8", newline="\n")

assert not any(f in (root / "lib/services/document_delivery_service.dart").read_text()
               for f in ("device_sync_push", "media_manifest", "GEMINI_API_KEY"))
print("DOCUMENT_CENTER_NAVIGATION_AND_GMAIL_LEDGER_OK")
