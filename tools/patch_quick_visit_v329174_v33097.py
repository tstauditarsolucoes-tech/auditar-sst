#!/usr/bin/env python3
"""Navigation-only quick visit entry. Preserve all services, storage and Central."""
from pathlib import Path
import hashlib, shutil, sys
root=Path(sys.argv[1]); platform=sys.argv[2]; repo=Path(__file__).resolve().parents[1]
protected=[root/'lib/database.dart', root/'lib/models.dart']+list((root/'lib/services').glob('*'))+list((root/'painel_web_google_apps_script').glob('*'))
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.is_file()}
p=root/'lib/screens/home_screen.dart'; s=p.read_text(encoding='utf-8')
assert 'QuickVisitScreen' not in s
for imp in ["import '../models.dart';", "import 'quick_visit_screen.dart';"]:
 if imp not in s: s=imp+'\n'+s
anchor='  Widget _mobileBody() {'; assert s.count(anchor)==1
s=s.replace(anchor,'  Widget _completeMobileBody() {',1)
anchor='  Widget _desktopBody() {'; assert s.count(anchor)==1
s=s.replace(anchor,'  Widget _completeDesktopBody() {',1)
start=s.index('  Future<void> _showModules() async {'); brace=s.index('{',start); depth=0
for end in range(brace,len(s)):
 if s[end]=='{': depth+=1
 if s[end]=='}':
  depth-=1
  if depth==0: break
s=s[:start]+'''  Company? _visitCompany;

  Future<void> _showModules() async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => Scaffold(
      appBar: AppBar(title: const Text('Mais opções')),
      body: LayoutBuilder(builder: (context, box) => box.maxWidth >= 1000
        ? _completeDesktopBody() : _completeMobileBody()),
    )));
    if (mounted) await _refresh();
  }

  Future<void> _startVisit(VisitIntent intent, {bool changeCompany = false}) async {
    await _open(QuickVisitScreen(
      intent: intent,
      initialCompany: changeCompany ? null : _visitCompany,
      onSelected: (company) { if (mounted) setState(() => _visitCompany = company); },
    ));
  }

  Widget _quickBody({required bool desktop}) {
    final main = ListView(children: [
      VisitStartPanel(
        companyName: _visitCompany?.name,
        onOpen: (intent) => _startVisit(intent),
        onChange: () => _startVisit(VisitIntent.visit, changeCompany: true),
        onMore: _showModules,
      ),
    ]);
    if (!desktop) return main;
    return Row(children: [
      SizedBox(width: 264, child: ListView(padding: const EdgeInsets.all(12), children: [
        const ListTile(title: Text('AUDITAR SST', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)), subtitle: Text('Acesso rápido')),
        ListTile(leading: const Icon(Icons.business_outlined), title: const Text('Empresas e obras'), onTap: () => _startVisit(VisitIntent.visit, changeCompany: true)),
        ListTile(leading: const Icon(Icons.search), title: const Text('Buscar empresa'), onTap: () => _startVisit(VisitIntent.visit, changeCompany: true)),
        const Divider(),
        for (final module in _modules)
          ListTile(leading: Icon(module.icon, color: module.color), title: Text(module.title), onTap: () => _open(module.page())),
        const Divider(),
        ListTile(leading: const Icon(Icons.apps), title: const Text('Mais opções e indicadores'), onTap: _showModules),
        ListTile(leading: const Icon(Icons.settings_outlined), title: const Text('Configurações'), onTap: () => _open(const SettingsScreen())),
      ])),
      const VerticalDivider(width: 1),
      Expanded(child: Align(alignment: Alignment.topCenter, child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 820), child: main))),
    ]);
  }
  Widget _mobileBody() => _quickBody(desktop: false);
  Widget _desktopBody() => _quickBody(desktop: true);
''' +s[end+1:]
p.write_text(s,encoding='utf-8',newline='\n')
# Company detail retains every module and adds a direct entry with this company.
p=root/'lib/screens/company_detail_screen.dart'; s=p.read_text(encoding='utf-8')
s="import 'quick_visit_screen.dart';\n"+s
# Reuse the existing AppBar actions so no content or routes are removed.
anchor='appBar: AppBar('; assert s.count(anchor)==1
pos=s.index(anchor); actions=s.find('actions: [',pos)
if actions!=-1 and actions < s.find('body:',pos):
 s=s[:actions]+s[actions:].replace('actions: [', "actions: [\n          IconButton(tooltip: 'Iniciar visita nesta empresa', icon: const Icon(Icons.add_location_alt_outlined), onPressed: () => _open(QuickVisitScreen(initialCompany: widget.company))),",1)
else:
 s=s.replace(anchor,anchor+"\n        actions: [IconButton(tooltip: 'Iniciar visita nesta empresa', icon: const Icon(Icons.add_location_alt_outlined), onPressed: () => _open(QuickVisitScreen(initialCompany: widget.company)))],",1)
p.write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(repo/'feature_sources/quick_visit_screen_v329174_v33097.dart',root/'lib/screens/quick_visit_screen.dart')
shutil.copyfile(repo/'feature_sources/quick_visit_test_v329174_v33097.dart',root/'test/quick_visit_test.dart')
p=root/'pubspec.yaml';s=p.read_text(); old,new=('3.29.173+315','3.29.174+316') if platform=='android' else ('3.30.96+283','3.30.97+284');assert s.count('version: '+old)==1;p.write_text(s.replace('version: '+old,'version: '+new))
for path,digest in before.items(): assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,str(path)
print('QUICK_VISIT_NAVIGATION_READY; ALL_SERVICES_DATABASE_MODELS_CENTRAL_BYTE_IDENTICAL',platform)
