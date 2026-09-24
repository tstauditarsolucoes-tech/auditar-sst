#!/usr/bin/env python3
"""Add per-company document sending and delivery history, without touching sync/AI.
Sources live in build_sources/v3.29.115-document-dispatch/."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
source=Path(__file__).resolve().parents[1]/'build_sources/v3.29.115-document-dispatch'

def read(rel):return (root/rel).read_text(encoding='utf-8')
def write(rel,s):
 p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8',newline='\n')
def one(s,a,b,where):
 assert s.count(a)==1,(where,s.count(a),a[:90]);return s.replace(a,b,1)
def add_import(s,path):
 assert path not in s;return "import '"+path+"';\n"+s

for name in ('document_delivery_service.dart','document_dispatch_dialog.dart','document_dispatch_center_screen.dart'):
 target=('lib/services/' if name=='document_delivery_service.dart' else 'lib/widgets/' if name=='document_dispatch_dialog.dart' else 'lib/screens/')+name
 write(target,(source/name).read_text(encoding='utf-8'))

rel='lib/services/report_email_service.dart';s=read(rel)
s=one(s,'    required String inspectionId,','    required String inspectionId,\n    String? requestId,','report email request ID param')
s=one(s,"'requestId': const Uuid().v4(),","'requestId': requestId ?? const Uuid().v4(),",'report email request ID pass')
write(rel,s)

# New Home menu entry, Windows navigation, and mobile module grid.
rel='lib/screens/home_screen.dart';s=add_import(read(rel),'document_dispatch_center_screen.dart')
needle="    _ModuleData(\n      title: 'Vistorias',"
item="""    _ModuleData(
      title: 'Central de documentos',
      tutorialId: 'document_delivery',
      subtitle: 'Escolha o que enviar e consulte o histórico por empresa',
      icon: Icons.forward_to_inbox_outlined,
      color: AuditarBrand.greenDark,
      page: () => const DocumentDispatchCenterScreen(),
    ),
"""
s=one(s,needle,item+needle,'Home document menu')
s=one(s,"      'history',\n      'workers',","      'history',\n      'document_delivery',\n      'workers',",'desktop support')
write(rel,s)

# Make existing inspection send button use the same local/central delivery history.
rel='lib/screens/report_screen.dart';s=add_import(read(rel),'../services/document_delivery_service.dart')
s=one(s,'final message = await ReportEmailService.send(', 'final message = await DocumentDeliveryService.send(', 'existing inspection send')
s=one(s,"        inspectionId: widget.inspectionId,\n        to: to,", "        documentId: widget.inspectionId,\n        category: 'Vistoria',\n        title: 'Relatório de vistoria • ${widget.title}',\n        to: to,", 'inspection local audit')
write(rel,s)

# Ronda: button shares the same generated PDF (including images and signatures).
rel='lib/screens/express_round_screen.dart';s=add_import(read(rel),'../widgets/document_dispatch_dialog.dart')
needle='      await Printing.sharePdf(\n        bytes: bytes,'
assert s.count(needle)==1
s=one(s,needle,"""      final delivery = await showDialog<bool>(context: context, builder: (dialogContext) => AlertDialog(
        title: const Text('Documento da Ronda Expressa'),
        content: const Text('Como deseja utilizar este relatório?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Compartilhar')),
          FilledButton.icon(onPressed: () => Navigator.pop(dialogContext, true),
            icon: const Icon(Icons.mark_email_read_outlined), child: const Text('Enviar por e-mail')),
        ],
      ));
      if (!mounted || delivery == null) return;
      if (delivery) {
        await DocumentDispatchDialog.send(context, company: widget.company,
          documentId: 'round:$roundId', category: 'Ronda Expressa',
          title: 'Ronda Expressa', fileName: 'Ronda_Expressa_${widget.company.id}.pdf',
          generatePdf: () async => bytes);
        return;
      }
      await Printing.sharePdf(
        bytes: bytes,""",'round direct mail')
write(rel,s)

# Acts/unsafe conditions existing report (not a simulated document).
rel='lib/screens/safety_observations_screen.dart';s=add_import(read(rel),'../widgets/document_dispatch_dialog.dart')
anchor='          IconButton(\n            tooltip: \'Gerar relatório PDF\','
assert s.count(anchor)==1
s=one(s,anchor,"""          IconButton(
            tooltip: 'Enviar relatório de atos e condições por e-mail',
            icon: const Icon(Icons.mark_email_read_outlined),
            onPressed: records.isEmpty || generatingReport ? null : () async {
              await DocumentDispatchDialog.send(context, company: widget.company,
                documentId: 'safety:${widget.company.id}', category: 'Atos e condições inseguras',
                title: 'Relatório de atos e condições inseguras',
                fileName: 'Atos_Condicoes_${widget.company.id}.pdf',
                generatePdf: () => SafetyObservationPdfService.generate(
                  company: widget.company, records: records, sectors: sectors));
            },
          ),
"""+anchor,'unsafe conditions button')
write(rel,s)

# DDS fiche -- generated from the same full participant/signature PDF.
rel='lib/screens/sst_records_screen.dart';s=add_import(read(rel),'../widgets/document_dispatch_dialog.dart')
needle="                    if (record.type == 'DDS') ...["
assert s.count(needle)==1
s=one(s,needle,needle+"""
                      Padding(padding: const EdgeInsets.only(top: 8),
                        child: OutlinedButton.icon(
                          onPressed: () async {
                            final companies = await AppDatabase.instance.getCompanies(onlyActive: false);
                            final matches = companies.where((c) => c.id == record.companyId);
                            if (matches.isEmpty || !mounted) return;
                            await DocumentDispatchDialog.send(context, company: matches.first,
                              documentId: 'dds:${record.id}', category: 'DDS',
                              title: 'Ficha de DDS • ${record.title}',
                              fileName: 'Ficha_DDS_${record.id}.pdf',
                              generatePdf: () => DdsPdfService.generate(record));
                          },
                          icon: const Icon(Icons.mark_email_read_outlined),
                          label: const Text('Enviar ficha do DDS por e-mail'),
                        )),
""",'DDS button')
write(rel,s)

# Training record fiche. Reuse its _pdfBytes, preserving signatures and photos.
rel='lib/screens/training_records_screen.dart';s=add_import(read(rel),'../widgets/document_dispatch_dialog.dart')
anchor="          IconButton(\n            onPressed: busy ? null : _sharePdf,"
assert s.count(anchor)==1
s=one(s,anchor,"""          IconButton(
            onPressed: busy ? null : () async {
              await DocumentDispatchDialog.send(context, company: widget.company,
                documentId: 'training:${current.id}', category: 'Treinamento',
                title: 'Ficha de treinamento • ${current.title}',
                fileName: _fileName(), generatePdf: _pdfBytes);
            },
            tooltip: 'Enviar ficha de treinamento por e-mail',
            icon: const Icon(Icons.mark_email_read_outlined),
          ),
"""+anchor,'training button')
write(rel,s)

# NC detail PDF (with existing photo evidence).
rel='lib/screens/non_conformity_detail_screen.dart';s=add_import(read(rel),'../widgets/document_dispatch_dialog.dart')
# Only inject into the appbar actions before the existing share action when possible.
needle='            onPressed: _sharePdf,'
assert s.count(needle)==1
s=one(s,needle,"""            onPressed: _sharePdf,""",'NC anchor for context')
# Catalogue offers NC direct send; detail retains its own PDF button and no unintended navigation changes.
write(rel,s)

# New version in separate patch step after all existing baseline assertions.
pub=read('pubspec.yaml');expected='3.29.115+257' if platform=='android' else '3.30.39+227'
assert 'version: '+expected in pub,(expected,pub.splitlines()[:10])
new='3.29.116+258' if platform=='android' else '3.30.40+228'
write('pubspec.yaml',pub.replace('version: '+expected,'version: '+new,1))
print('DOCUMENT_DELIVERY_UI_AND_HISTORY_PATCH_OK',platform,new)