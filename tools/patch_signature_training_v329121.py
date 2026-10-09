#!/usr/bin/env python3
"""Large training signature and visible DDS participant progress."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
def patch(name,old,new,label):
 p=root/'lib/screens'/name;s=p.read_text(encoding='utf-8')
 if s.count(old)!=1:raise RuntimeError(label+': '+str(s.count(old)))
 p.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')
p='training_records_screen.dart'
patch(p,"import '../services/storage_service.dart';",
 "import '../services/storage_service.dart';\nimport '../widgets/large_signature_capture.dart';",'training import')
patch(p,"  bool saving = false;\n\n  @override\n  void dispose() {",
"""  bool saving = false;

  @override
  void initState() {
    super.initState();
    if(Platform.isAndroid) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if(mounted && !saving)_openFullScreen();
      });
    }
  }

  @override
  void dispose() {""",'training auto-wide')
path=root/'lib/screens'/p
s=path.read_text(encoding='utf-8')
start="  Future<void> _openFullScreen() async {"
end="  Future<void> _save() async {"
a=s.find(start);b=s.find(end,a+len(start))
if a<0 or b<0:raise RuntimeError('training fullscreen anchors')
method="""  Future<void> _openFullScreen() async {
    if(saving)return;
    final name=(widget.participant['name'] ?? '').toString().trim();
    final progress=widget.participantIndex!=null &&
        widget.participantTotal!=null && widget.participantTotal!>0
      ? 'Participante ' + widget.participantIndex.toString() +
        ' de ' + widget.participantTotal.toString() : '';
    final ok=await LargeSignatureCapturePage.open(context,
      controller:controller,title:'Assinatura de treinamento',
      signerName:name,contextLabel:widget.trainingTitle,
      progressLabel:progress);
    if(ok && mounted)await _save();
  }

"""
s=s[:a]+method+s[b:]
path.write_text(s,encoding='utf-8',newline='\n')
patch(p,"tooltip: 'Assinar em tela cheia',",
 "tooltip: 'Assinar em tela cheia, com área ampliada',",'training hint')

p='sst_record_form_screen.dart'
path=root/'lib/screens'/p;s=path.read_text(encoding='utf-8')
marker="    final result = await Navigator.of(context).push<DdsSignatureCaptureResult>("
assert s.count(marker)==1
s=s.replace(marker,"""    final ddsNames=_ddsParticipantNames();
    final position=ddsNames.indexWhere(
      (value)=>value.toLowerCase()==initialName.toLowerCase());
"""+marker,1)
old="builder: (_) => DdsSignatureCaptureScreen(initialName: initialName),"
new="""builder: (_) => DdsSignatureCaptureScreen(
          initialName: initialName,
          participantIndex: position>=0 ? position+1 : null,
          participantTotal: ddsNames.length,
        ),"""
assert s.count(old)==1
path.write_text(s.replace(old,new,1),encoding='utf-8',newline='\n')

v=root/'pubspec.yaml';text=v.read_text(encoding='utf-8')
old,new=('3.29.120+262','3.29.121+263') if platform=='android' else ('3.30.44+231','3.30.45+232')
assert text.count('version: '+old)==1,[x for x in text.splitlines() if x.startswith('version:')]
v.write_text(text.replace('version: '+old,'version: '+new,1),encoding='utf-8',newline='\n')
print('WIDE_SIGNATURE_TRAINING_DDS_PROGRESS_OK',platform,new)
