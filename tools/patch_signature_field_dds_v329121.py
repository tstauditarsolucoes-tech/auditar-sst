#!/usr/bin/env python3
"""Wide signature capture for checklist and DDS; no schema or sync changes."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
shared=Path(__file__).resolve().parents[1]/'feature_sources/large_signature_capture.dart'
assert shared.exists()
(root/'lib/widgets/large_signature_capture.dart').write_bytes(shared.read_bytes())

def patch(rel,old,new,label):
 p=root/'lib'/rel
 s=p.read_text(encoding='utf-8')
 if s.count(old)!=1:raise RuntimeError(label+': '+str(s.count(old)))
 p.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')

def block(rel,start,end,new,label):
 p=root/'lib'/rel
 s=p.read_text(encoding='utf-8')
 a=s.find(start);b=s.find(end,a+len(start))
 if a<0 or b<0:raise RuntimeError(label+' anchors')
 p.write_text(s[:a]+new+s[b:],encoding='utf-8',newline='\n')

p='screens/signature_screen.dart'
patch(p,"import 'package:signature/signature.dart';",
 "import 'package:signature/signature.dart';\nimport '../widgets/large_signature_capture.dart';",'checklist import')
block(p,"  Future<void> _openFullScreenSignature({","  Widget _signatureCard({",
"""  Future<void> _openFullScreenSignature({
    required SignatureController controller,
    required String title,
  }) async {
    final who=title.contains('técnico')
        ? technicianName.text.trim():responsibleName.text.trim();
    await LargeSignatureCapturePage.open(
      context,controller:controller,title:title,signerName:who,
      contextLabel:widget.companyName);
    if(mounted)setState((){});
  }

""",'checklist fullscreen')
patch(p,"height: 180,\n                backgroundColor: Colors.white,",
 "height: 220,\n                backgroundColor: Colors.white,",'checklist larger fallback')
patch(p,"label: const Text('Assinar em tela cheia'),",
 "label: const Text('ASSINAR EM TELA CHEIA • ÁREA MAIOR'),",'checklist main action')
path=root/'lib'/p
s=path.read_text(encoding='utf-8')
marker='\nclass _FullScreenSignaturePage extends StatelessWidget {'
assert s.count(marker)==1
s=s[:s.index(marker)].rstrip()+'\n'
s=s.replace("import 'package:flutter/services.dart';\n","")
path.write_text(s,encoding='utf-8',newline='\n')

p='screens/dds_signature_capture_screen.dart'
patch(p,"import '../services/storage_service.dart';",
 "import '../services/storage_service.dart';\nimport '../widgets/large_signature_capture.dart';",'DDS import')
patch(p,"  const DdsSignatureCaptureScreen({super.key, this.initialName = ''});",
"""  final int? participantIndex;
  final int? participantTotal;
  const DdsSignatureCaptureScreen({
    super.key, this.initialName = '', this.participantIndex,
    this.participantTotal,
  });""",'DDS progress')
patch(p,"    nameController = TextEditingController(text: widget.initialName);",
"""    nameController = TextEditingController(text: widget.initialName);
    if(Platform.isAndroid && widget.initialName.trim().isNotEmpty) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if(mounted && !saving)_openFullScreen();
      });
    }""",'DDS start wide')
block(p,"  Future<void> _openFullScreen() async {","  Future<void> _confirm() async {",
"""  Future<void> _openFullScreen() async {
    if(saving)return;
    final name=nameController.text.trim();
    if(name.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content:Text('Informe o nome do participante.')));
      return;
    }
    final progress=widget.participantIndex!=null &&
        widget.participantTotal!=null && widget.participantTotal!>0
      ? 'Participante ' + widget.participantIndex.toString() +
        ' de ' + widget.participantTotal.toString() : '';
    final ok=await LargeSignatureCapturePage.open(context,
      controller:signatureController,title:'Assinatura de DDS',
      signerName:name,contextLabel:'Presença no DDS',
      progressLabel:progress);
    if(ok && mounted)await _confirm();
  }

""",'DDS fullscreen')
patch(p,"height: 250,","height: 290,",'DDS fallback height')
patch(p,"label: const Text('Tela cheia'),",
 "label: const Text('Área ampliada'),",'DDS action')
path=root/'lib'/p;s=path.read_text(encoding='utf-8')
marker='\nclass _DdsFullSignatureCanvas extends StatelessWidget {'
assert s.count(marker)==1
s=s[:s.index(marker)].rstrip()+'\n'
s=s.replace("import 'package:flutter/services.dart';\n","")
path.write_text(s,encoding='utf-8',newline='\n')
print('WIDE_SIGNATURE_CHECKLIST_DDS_OK')
