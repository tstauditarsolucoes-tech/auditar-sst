#!/usr/bin/env python3
from pathlib import Path
import shutil,hashlib,sys
root=Path(sys.argv[1]);platform=sys.argv[2];repo=Path(__file__).resolve().parents[1]
protected=[root/'lib/database.dart',root/'lib/models.dart']+list((root/'lib/services').glob('*.dart'))
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
p=root/'lib/screens/companies_screen.dart';s=p.read_text(encoding='utf-8')
def replace(a,b):
 global s
 if s.count(a)!=1: raise RuntimeError('Âncora ausente ou ambígua: '+a[:100])
 s=s.replace(a,b,1)
replace('  bool _grouped = false;', '  bool _grouped = false;\n  bool _recentOnly = false;\n  bool _sharingGroups = false;')
replace("    final name = TextEditingController(text: company?.name ?? '');", "    final alias = TextEditingController(text: _organization.alias(company?.id ?? ''));\n    final name = TextEditingController(text: company?.name ?? '');")
replace('    await _organization.assign([updated.id], organizationGroup,', '    await _organization.assign([updated.id], organizationGroup, alias: alias.text.trim(),')
# O formulário utiliza a versão formatada do patch anterior.
anchor='                        TextField(\n                          controller: name,'
replace(anchor, """                        TextField(
                          controller: alias,
                          maxLength: 120,
                          decoration: const InputDecoration(labelText: 'Nome curto da unidade/obra', hintText: 'Ex.: Ideal — Saci'),
                        ),
"""+anchor)
replace('      if (_favoritesOnly && !_organization.favorite(c.id)) return false;', '      if (_favoritesOnly && !_organization.favorite(c.id)) return false;\n      if (_recentOnly && _organization.lastVisit(c.id).isEmpty) return false;')
replace("[c.name, c.city ?? '', c.cnpj ?? '', group, type]", "[c.name, _organization.alias(c.id), c.city ?? '', c.cnpj ?? '', group, type]")
replace('    result.sort((a, b) {', '    result.sort((a, b) {\n      if (_recentOnly) return _organization.lastVisit(b.id).compareTo(_organization.lastVisit(a.id));')
replace('  Widget _organizationFilters() =>', '''  Future<void> _shareGroups() async {
    if (_sharingGroups) return;
    setState(() => _sharingGroups = true);
    try {
      await _organization.sync(companies.map((c) => c.id).toList());
      if (!mounted) return;
      if (_organization.remoteConflict != null) {
        final accept = await showDialog<bool>(context: context, builder: (context) => AlertDialog(
          title: const Text('Organização alterada em outro aparelho'),
          content: const Text('Há alterações de grupos concorrentes. Você pode manter suas mudanças pendentes ou usar os vínculos da Central, substituindo a organização local. Registros SST e favoritos não serão alterados.'),
          actions: [TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Manter pendente')), FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Usar vínculos da Central'))],
        ));
        if (accept == true) await _organization.acceptRemote(_organization.remoteConflict!, companies.map((c) => c.id).toList());
      }
      if (mounted) setState(() { if (_groupFilter != '*' && _groupFilter.isNotEmpty && !_organization.groups.contains(_groupFilter)) _groupFilter = '*'; });
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_organization.remoteConflict == null ? 'Organização compartilhada com a Central.' : 'Alterações locais mantidas pendentes.')));
    } catch (_) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Não foi possível compartilhar. Confira a conexão e a instalação do módulo de grupos na Central. Seus grupos locais foram preservados.')));
    } finally { if (mounted) setState(() => _sharingGroups = false); }
  }

  Future<void> _manageGroups() async {
    if (_organization.groups.isEmpty) return;
    final old = await showDialog<String>(context: context, builder: (context) => SimpleDialog(title: const Text('Gerenciar grupos'), children: _organization.groups.map((g) => SimpleDialogOption(onPressed: () => Navigator.pop(context, g), child: Text(g))).toList()));
    if (old == null || !mounted) return;
    final name = TextEditingController(text: old);
    final next = await showDialog<String>(context: context, builder: (context) => AlertDialog(
      title: Text(old),
      content: Column(mainAxisSize: MainAxisSize.min, children: [TextField(controller: name, maxLength: 80, decoration: const InputDecoration(labelText: 'Novo nome ou nome do grupo de destino')), const Text('Usar um grupo existente une as empresas. Retirar o grupo mantém as empresas e seus registros em Sem grupo.')]),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')), TextButton(onPressed: () => Navigator.pop(context, ''), child: const Text('Retirar grupo')), FilledButton(onPressed: () { if (name.text.trim().isNotEmpty && name.text.trim() != '*') Navigator.pop(context, name.text.trim()); }, child: const Text('Salvar'))],
    ));
    if (next == null || !mounted) return;
    try { await _organization.renameGroup(old, next, companies.map((c) => c.id).toList()); if (mounted) setState(() => _groupFilter = '*'); }
    catch (_) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Não foi possível salvar o grupo.'))); }
  }

  Widget _organizationFilters() =>''')
replace("initialValue: _groupFilter,", "key: ValueKey(_groupFilter), initialValue: _groupFilter,")
replace("FilterChip(label: const Text('Favoritos'),", "FilterChip(label: const Text('Recentes'), selected: _recentOnly, onSelected: (v) => setState(() => _recentOnly = v)),\n        FilterChip(label: const Text('Favoritos'),")
replace("label: const Text('Organizar empresas')))", "label: const Text('Organizar empresas')))" )
anchor='      if (_organizationReady) Align('
pos=s.index(anchor);end=s.index('\n    ]),',pos)
s=s[:end]+'''
      if (_organizationReady) Wrap(spacing: 8, children: [
        TextButton.icon(onPressed: _sharingGroups ? null : _shareGroups, icon: const Icon(Icons.cloud_sync_outlined), label: Text(_sharingGroups ? 'Compartilhando...' : 'Compartilhar grupos')),
        TextButton.icon(onPressed: _sharingGroups ? null : _manageGroups, icon: const Icon(Icons.folder_outlined), label: const Text('Gerenciar grupos')),
      ]),
''' +s[end:]
replace("[group.isEmpty ? 'Sem grupo' : group,", "[if (_organization.alias(company.id).isNotEmpty) _organization.alias(company.id), group.isEmpty ? 'Sem grupo' : group,")
# Registrar navegação sem mudar a rota existente.
replace('() => Navigator.of(context)', '() {\n              unawaited(_organization.markVisited(company.id).catchError((Object _) {}));\n              Navigator.of(context)')
# Fecha o bloco adicionado no callback original.
start=s.index('unawaited(_organization.markVisited');end=s.index('.then((_) => _load()),',start)
s=s[:end]+s[end:].replace('.then((_) => _load()),', '.then((_) => _load());\n            },',1)
# Windows pode não ter dart:async antes desta extensão. Inclua apenas imports ausentes.
for module in ('dart:async', 'dart:convert'):
 statement = "import '"+module+"';"
 if s.count(statement)>1: raise RuntimeError('Import duplicado: '+module)
 if statement not in s: s=statement+'\n'+s
replace('  bool _recentOnly = false;', '  bool _recentOnly = false;\n  bool _viewLoaded = false;')
replace('    final loadedStats = <String, Map<String, int>>{};', """    if (!_viewLoaded) {
      try {
        final raw = await AppDatabase.instance.getSetting('company_groups_view_v1');
        if (raw.isNotEmpty) {
          final view = jsonDecode(raw) as Map<String,dynamic>;
          final group = view['group'] as String? ?? '*';
          _groupFilter = group == '*' || group.isEmpty || _organization.groups.contains(group) ? group : '*';
          final type = view['type'] as String? ?? '*';
          _typeFilter = type == '*' || CompanyOrganization.types.contains(type) ? type : '*';
          _activityFilter = ['active','inactive','*'].contains(view['activity']) ? view['activity'] as String : 'active';
          _grouped = view['grouped'] == true;
          _favoritesOnly = view['favorites'] == true;
          _recentOnly = view['recent'] == true;
        }
      } catch (_) {}
      _viewLoaded = true;
    }
    final loadedStats = <String, Map<String, int>>{};""")
replace("loadedStats[company.id] = {...summary, 'openNcs': ncs.length};", """final training = Platform.isWindows ? await AppDatabase.instance.getTrainingSummary(companyId: company.id) : <String,int>{};
      loadedStats[company.id] = {...summary, 'openNcs': ncs.length, 'expiredTraining': training['expired'] ?? 0};""")
replace('  Widget _organizationFilters() =>', """  void _changeView(VoidCallback update) {
    setState(update);
    unawaited(AppDatabase.instance.setSetting('company_groups_view_v1', jsonEncode({'group':_groupFilter,'type':_typeFilter,'activity':_activityFilter,'grouped':_grouped,'favorites':_favoritesOnly,'recent':_recentOnly})).catchError((Object _) {}));
  }
  String _groupSummary(List<Company> items) {
    int total(String key) => items.fold(0, (sum,c) => sum + (stats[c.id]?[key] ?? 0));
    return '${total('openNcs')} NCs abertas • ${total('overdue')} ações vencidas • ${total('expiredTraining')} treinamentos vencidos';
  }
  Widget _organizationFilters() =>""")
for field in ['_groupFilter','_typeFilter','_activityFilter','_grouped','_favoritesOnly','_recentOnly']:
 s=s.replace('setState(() => '+field, '_changeView(() => '+field)
replace('trailing: Icon(_collapsedGroups.contains(key)', 'subtitle: Platform.isWindows ? Text(_groupSummary(groups[key]!)) : null, trailing: Icon(_collapsedGroups.contains(key)')
p.write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(repo/'feature_sources/company_organization_v329173_v33096.dart',root/'lib/widgets/company_organization.dart')
shutil.copyfile(repo/'feature_sources/company_organization_test_v329173_v33096.dart',root/'test/company_organization_test.dart')
for path,digest in before.items(): assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,str(path)
# Preparar somente a integração da Central; nunca publicar.
code=root/'painel_web_google_apps_script/Code.gs';text=code.read_text(encoding='utf-8');anchor="    if (request.action === 'device_sync_push') {";assert text.count(anchor)==1
text=text.replace(anchor,"    if (request.action === 'company_groups_sync_v1') {\n      return jsonResponse_(companyGroupsSync_(request));\n    }\n\n"+anchor,1);code.write_text(text,encoding='utf-8',newline='\n')
shutil.copyfile(repo/'feature_sources/CompanyGroupsSync_v1.gs',code.parent/'CompanyGroupsSync.gs')
pub=root/'pubspec.yaml';old,new=('3.29.172+314','3.29.173+315') if platform=='android' else ('3.30.95+282','3.30.96+283');text=pub.read_text(encoding='utf-8');assert text.count('version: '+old)==1;pub.write_text(text.replace('version: '+old,'version: '+new),encoding='utf-8')
print('SHARED_GROUPS_PREPARED; DATABASE_SCHEMA_SYNC_AUTH_MEDIA_PDF_INTACT',platform)
