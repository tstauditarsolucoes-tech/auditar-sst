#!/usr/bin/env python3
"""Archive worksite diary overflow locally before the existing 80-row cloud snapshot."""
from pathlib import Path
import hashlib,re,sys

root=Path(sys.argv[1]);platform=sys.argv[2]
assert platform in ('android','windows')
old,new=(('3.29.188+330','3.29.189+331') if platform=='android'
         else ('3.30.111+298','3.30.112+299'))
screen=root/'lib/screens/worksite_followup_screen.dart'
pub=root/'pubspec.yaml'
version=pub.read_text(encoding='utf-8')
assert version.count('version: '+old)==1
s=screen.read_text(encoding='utf-8')
assert 'class WorksiteDiaryArchive' not in s
protected=[p for folder in ('lib','painel_web_google_apps_script')
           for p in (root/folder).rglob('*') if p.is_file() and p!=screen]
checks={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}

archive="""/// Older diary entries are local only; the Central V1 still receives at most 80.
class WorksiteDiaryArchive {
  WorksiteDiaryArchive._();
  static String key(String company,String user)=>
    'worksite_diary_archive_v1_'+Uri.encodeComponent(user)+'_'+Uri.encodeComponent(company);
  static String signature(WorksiteLog item)=>jsonEncode(item.toMap());
  static List<WorksiteLog> unique(List<WorksiteLog> before,List<WorksiteLog> later){
    final seen=<String>{};
    return [for(final v in [...before,...later]) if(seen.add(signature(v))) v];
  }
  static List<WorksiteLog> overflow(WorksiteFollowup record)=>
    record.log.skip(80).toList();
  static WorksiteFollowup recent(WorksiteFollowup record)=>
    record.copyWith(log:record.log.take(80).toList());
  static Future<List<WorksiteLog>> load(String company,String user)async{
    final raw=await AppDatabase.instance.getSetting(key(company,user));
    if(raw.isEmpty)return [];
    final data=jsonDecode(raw);
    if(data is! List)throw const FormatException('Arquivo anterior inválido');
    final result=<WorksiteLog>[];
    for(final entry in data){
      if(entry is! Map)throw const FormatException('Entrada anterior inválida');
      result.add(WorksiteLog.fromMap(Map<String,dynamic>.from(entry)));
    }
    return result;
  }
  static Future<void> preserve(String company,String user,List<WorksiteLog> older)async{
    if(older.isEmpty)return;
    final current=await load(company,user);
    final merged=unique(current,older);
    if(merged.length==current.length)return;
    await AppDatabase.instance.setSetting(key(company,user),
      jsonEncode(merged.map((x)=>x.toMap()).toList()));
  }
}
"""
anchor='class WorksiteFollowupStore {'
assert s.count(anchor)==1
s=s.replace(anchor,archive+'\n'+anchor,1)

start=s.index('  Future<void> _save(')
end=s.index('  Future<void> _addLog()',start)
part=s[start:end]
store=re.compile(r'await\s+WorksiteFollowupStore\.save\s*\(\s*widget\.company\.id\s*,\s*value\s*\)\s*;')
assert len(store.findall(part))==1
part=store.sub("""final account=AppDatabase.activeUserId.toString();
      final excess=WorksiteDiaryArchive.overflow(value);
      // If preservation fails, keep the active diary untouched.
      if(excess.isNotEmpty){
        await WorksiteDiaryArchive.preserve(widget.company.id,account,excess);
      }
      if(account!=AppDatabase.activeUserId.toString()||
          !AuthService.canAccessCompany(widget.company.id)){
        throw StateError('Conta ou permissão alterada durante a gravação');
      }
      final stored=WorksiteDiaryArchive.recent(value);
      await WorksiteFollowupStore.save(widget.company.id,stored);""",part,1)
update=re.compile(r'(_record\s*=\s*)value\b')
assert len(update.findall(part))==1
part=update.sub(r'\1stored',part,1)
s=s[:start]+part+s[end:]

start=s.index('  Future<void> _addLog() async {')
end=s.index('  WorksiteFollowup _currentForm()',start)
part=s[start:end]
cut=re.compile(r'(\[\s*result\s*,\s*\.\.\._record\.log\s*\])\s*\.take\s*\(\s*80\s*\)\s*\.toList\s*\(\s*\)')
assert len(cut.findall(part))==1, 'Old silent truncation changed'
part=cut.sub(r'\1',part,1)
s=s[:start]+part+s[end:]

viewer="""  Future<void> _openArchivedDiary()async{
    if(!AuthService.canAccessCompany(widget.company.id))return;
    final account=AppDatabase.activeUserId.toString();
    try{
      final old=await WorksiteDiaryArchive.load(widget.company.id,account);
      if(!mounted||account!=AppDatabase.activeUserId.toString()||
          !AuthService.canAccessCompany(widget.company.id))return;
      await showDialog<void>(context:context,builder:(dialog)=>AlertDialog(
        title:Text('Registros anteriores: '+old.length.toString()),
        content:SizedBox(width:560,height:390,child:old.isEmpty?
          const Center(child:Text('Nenhum registro anterior arquivado.')):
          ListView.builder(
            itemCount:old.length,
            itemBuilder:(context,index){
              final row=old[index];
              return ListTile(title:Text(row.type),
                subtitle:Text(row.at+'\\n'+row.note),isThreeLine:true);
            },
          )),
        actions:[TextButton(onPressed:()=>Navigator.pop(dialog),
          child:const Text('Fechar'))],
      ));
    }catch(_){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content:Text('Histórico anterior indisponível. Nenhum registro foi apagado.')));
    }
  }

"""
anchor='  WorksiteFollowup _currentForm()'
assert s.count(anchor)==1
s=s.replace(anchor,viewer+anchor,1)
found=re.compile(r'(?m)^(?P<spaces>\s*)if\s*\(\s*_record\.log\.isEmpty\s*\)')
match=found.search(s)
assert match and len(found.findall(s))==1
indent=match.group('spaces')
button=indent+"""OutlinedButton.icon(
"""+indent+"""  onPressed:_openArchivedDiary,
"""+indent+"""  icon:const Icon(Icons.inventory_2_outlined),
"""+indent+"""  label:const Text('Ver registros anteriores'),
"""+indent+"""),
"""
s=s[:match.start()]+button+s[match.start():]
screen.write_text(s,encoding='utf-8')
pub.write_text(version.replace('version: '+old,'version: '+new),encoding='utf-8')
for f,d in checks.items():
    assert hashlib.sha256(f.read_bytes()).hexdigest()==d,str(f)
print('WORKSITE_DIARY_OVERFLOW_PRESERVED',platform,new,'CORE_GS_UNCHANGED')
