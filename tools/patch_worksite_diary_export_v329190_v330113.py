#!/usr/bin/env python3
"""Add on-demand, local-only full worksite diary copy. Never touch sync or GS."""
from pathlib import Path
import hashlib
import re
import sys

root=Path(sys.argv[1])
platform=sys.argv[2]
assert platform in ('android','windows')
old,new=(('3.29.189+331','3.29.190+332') if platform=='android'
         else ('3.30.112+299','3.30.113+300'))
screen=root/'lib/screens/worksite_followup_screen.dart'
assert screen.is_file()
src=screen.read_text(encoding='utf-8')
assert src.count('class WorksiteDiaryArchive')==1
assert '_copyCompleteDiary' not in src
pub=root/'pubspec.yaml'
pv=pub.read_text(encoding='utf-8')
assert pv.count('version: '+old)==1
protected=[p for folder in ('lib','painel_web_google_apps_script')
 for p in (root/folder).rglob('*') if p.is_file() and p!=screen]
checks={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
# Clipboard is activated exclusively by a user's button press.
anchor="import 'package:flutter/material.dart';"
assert src.count(anchor)==1
src=src.replace(anchor,anchor+"\nimport 'package:flutter/services.dart';",1)

class_anchor=re.compile(r'WorksiteDiaryArchive\._\(\)\s*;')
assert len(class_anchor.findall(src))==1
fmt="""  /// Explicit text copy, including entries older than the Central V1 window.
  /// Export doesn't mutate records, archive, cloud revision or permissions.
  static String exportText(String company,String phase,
      List<WorksiteLog> current,List<WorksiteLog> archived) {
    // Cloud and local archive may overlap after manual retrieval.
    // Deduplicate only in this copy; never modify the saved SST diary.
    final history=WorksiteDiaryArchive.unique(current,archived)
      ..sort((a,b)=>b.at.compareTo(a.at));
    final lines=<String>[
      'DIÁRIO COMPLETO DA OBRA — AUDITAR SST',
      'Obra: '+company,
      'Etapa registrada: '+phase,
      'Total de lançamentos: '+history.length.toString(),
      'Cópia local: registros anteriores podem não estar na Central V1.',
      '',
    ];
    if(history.isEmpty)lines.add('Nenhum lançamento registrado.');
    for(var i=0;i<history.length;i++){
      final item=history[i];
      lines.add((i+1).toString()+'. '+item.at+' | '+item.type);
      lines.add(item.note);
      lines.add('');
    }
    lines.add('Este diário não substitui os registros formais de NC ou os relatórios SST.');
    return lines.join('\\n');
  }
"""
match=class_anchor.search(src)
src=src[:match.end()]+"\n"+fmt+src[match.end():]

# Insert a method within WorksiteFollowupScreen, before existing archive viewer.
method_anchor=re.compile(r'(?m)^[ \t]*Future<void>[ \t]+_openArchivedDiary[ \t]*\(')
hits=list(method_anchor.finditer(src))
assert len(hits)==1,'archive viewer not uniquely found'
method="""  Future<void> _copyCompleteDiary() async {
    if(!AuthService.canAccessCompany(widget.company.id))return;
    final user=AppDatabase.activeUserId.toString();
    try {
      final older=await WorksiteDiaryArchive.load(widget.company.id,user);
      if(!mounted || user!=AppDatabase.activeUserId.toString() ||
          !AuthService.canAccessCompany(widget.company.id))return;
      final full=WorksiteDiaryArchive.exportText(
        widget.company.name,_record.phase,_record.log,older);
      await Clipboard.setData(ClipboardData(text:full));
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content:Text('Diário completo copiado ('+
          WorksiteDiaryArchive.unique(_record.log,older).length.toString()+
          ' registros). Confira antes de compartilhar.')));
    } catch (_) {
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content:Text(
          'Não foi possível copiar o diário. Os registros foram preservados.')));
    }
  }

"""
pos=hits[0].start()
src=src[:pos]+method+src[pos:]

# Show an explicitly named button alongside the existing archived-view action.
button_anchor=re.compile(r'(?m)^(?P<indent>[ \t]*)if\s*\(\s*_record\.log\.isEmpty\s*\)')
matches=list(button_anchor.finditer(src))
assert len(matches)==1,'diary list not uniquely found'
indent=matches[0].group('indent')
button=('\n'.join([
 indent+'OutlinedButton.icon(',
 indent+'  onPressed:_copyCompleteDiary,',
 indent+'  icon:const Icon(Icons.copy_all_outlined),',
 indent+"  label:const Text('Copiar diário completo'),",
 indent+'),',
 '']))
src=src[:matches[0].start()]+button+src[matches[0].start():]
screen.write_text(src,encoding='utf-8')
pub.write_text(pv.replace('version: '+old,'version: '+new),encoding='utf-8')
for p,digest in checks.items():
  assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,str(p)
print('FULL_WORKSITE_DIARY_EXPORT_READY',platform,new,'SST_CORE_GS_UNCHANGED')
