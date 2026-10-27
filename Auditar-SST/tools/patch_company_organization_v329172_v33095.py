#!/usr/bin/env python3
"""Organização local de empresas; nenhum schema, sync ou acesso é modificado."""
from pathlib import Path
import hashlib, shutil, sys
root=Path(sys.argv[1]); platform=sys.argv[2]; repo=Path(__file__).resolve().parents[1]
protected=[p for p in (root/'lib').rglob('*.dart') if p.name in ['database.dart','models.dart','auth_service.dart','device_sync_service.dart','apps_script_http.dart','sync_coordinator.dart','media_sync_service.dart','drive_service.dart','ai_assistant_service.dart'] or 'pdf' in p.name]+list((root/'painel_web_google_apps_script').glob('*'))
before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
p=root/'lib/screens/companies_screen.dart'; s=p.read_text(encoding="utf-8")
if 'CompanyOrganizationEditor' in s: raise RuntimeError('patch já aplicado')
def replace(old,new):
 global s
 if s.count(old)!=1: raise RuntimeError('âncora ambígua ou ausente: '+old[:90])
 s=s.replace(old,new,1)
replace("import '../models.dart';", "import '../models.dart';\nimport '../widgets/company_organization.dart';")
replace('  bool loading = true;', """  CompanyOrganization _organization = CompanyOrganization();
  bool _organizationReady = false;
  String _groupFilter = '*';
  String _typeFilter = '*';
  String _activityFilter = 'active';
  bool _favoritesOnly = false;
  bool _grouped = false;
  final Set<String> _collapsedGroups = {};
  bool loading = true;""")
replace('    final loadedStats = <String, Map<String, int>>{};', """    try {
      _organization = await CompanyOrganization.load();
      _organizationReady = true;
    } catch (_) {
      _organizationReady = false;
      // Não sobrescrever dados locais caso a leitura falhe.
    }
    final loadedStats = <String, Map<String, int>>{};""")
replace("    final name = TextEditingController(text: company?.name ?? '');", """    var organizationGroup = _organization.group(company?.id ?? '');
    var organizationType = _organization.type(company?.id ?? '');
    final name = TextEditingController(text: company?.name ?? '');""")
replace('                          controller: name,', '                          controller: name,') # valida a âncora original
replace('                        TextField(\n                          controller: name,', """                        if (_organizationReady)
                          CompanyOrganizationEditor(
                            organization: _organization,
                            initialGroup: organizationGroup,
                            initialType: organizationType,
                            onChanged: (group, type) {
                              organizationGroup = group;
                              organizationType = type;
                            },
                          ),
                        TextField(
                          controller: name,""")
replace('      await AppDatabase.instance.updateCompany(updated);\n    }\n    await _load();', """      await AppDatabase.instance.updateCompany(updated);
    }
    if (_organizationReady) {
      try {
        await _organization.assign([updated.id], organizationGroup, type: organizationType);
      } catch (_) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Empresa salva. Não foi possível salvar a organização local; tente novamente.')),
        );
      }
    }
    await _load();""")
start=s.index('  List<Company> get _filtered {'); end=s.index('\n  @override',start)
s=s[:start]+'''  List<Company> get _filtered {
    final q = CompanyOrganization.normalized(searchController.text);
    final result = companies.where((c) {
      final group = _organization.group(c.id);
      final type = _organization.type(c.id);
      if (_groupFilter != '*' && group != _groupFilter) return false;
      if (_typeFilter != '*' && type != _typeFilter) return false;
      if (_activityFilter == 'active' && !c.active) return false;
      if (_activityFilter == 'inactive' && c.active) return false;
      if (_favoritesOnly && !_organization.favorite(c.id)) return false;
      return q.isEmpty || [c.name, c.city ?? '', c.cnpj ?? '', group, type]
          .any((v) => CompanyOrganization.normalized(v).contains(q));
    }).toList();
    result.sort((a, b) {
      final favorite = (_organization.favorite(b.id) ? 1 : 0) - (_organization.favorite(a.id) ? 1 : 0);
      return favorite != 0 ? favorite : CompanyOrganization.normalized(a.name).compareTo(CompanyOrganization.normalized(b.name));
    });
    return result;
  }

  Future<void> _organizeCompanies() async {
    if (!_organizationReady) return;
    final selected = <String>{};
    var group = '';
    var type = '';
    var busy = false;
    await showDialog<void>(context: context, barrierDismissible: false, builder: (dialogContext) => StatefulBuilder(
      builder: (context, update) => AlertDialog(
        title: const Text('Organizar empresas'),
        content: SizedBox(width: 480, child: SingleChildScrollView(child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CompanyOrganizationEditor(organization: _organization, initialGroup: '', initialType: '', onChanged: (g, t) { group = g; type = t; }),
            const Text('Selecione as empresas para mover. Tipo não informado preserva o tipo atual.'),
            ..._filtered.map((c) => CheckboxListTile(
              title: Text(c.name, maxLines: 2, overflow: TextOverflow.ellipsis),
              subtitle: Text(_organization.group(c.id).isEmpty ? 'Sem grupo' : _organization.group(c.id)),
              value: selected.contains(c.id),
              onChanged: busy ? null : (v) => update(() { if (v == true) { selected.add(c.id); } else { selected.remove(c.id); } }),
            )),
          ],
        ))),
        actions: [
          TextButton(onPressed: busy ? null : () => Navigator.pop(dialogContext), child: const Text('Cancelar')),
          FilledButton(onPressed: busy || selected.isEmpty ? null : () async {
            update(() => busy = true);
            try {
              await _organization.assign(selected.toList(), group, type: type.isEmpty ? null : type);
              if (dialogContext.mounted) Navigator.pop(dialogContext);
              if (mounted) setState(() {});
            } catch (_) {
              if (context.mounted) { update(() => busy = false); ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Não foi possível salvar. Tente novamente.'))); }
            }
          }, child: Text(busy ? 'Salvando...' : 'Mover selecionadas')),
        ],
      ),
    ));
  }

  Widget _organizationFilters() => Padding(
    padding: const EdgeInsets.symmetric(vertical: 8),
    child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      if (!_organizationReady) const Text('Organização local indisponível. Atualize a lista para tentar novamente.'),
      if (_organizationReady) DropdownButtonFormField<String>(
        initialValue: _groupFilter, isExpanded: true,
        decoration: const InputDecoration(labelText: 'Grupo empresarial'),
        items: [const DropdownMenuItem(value: '*', child: Text('Todos os grupos')), const DropdownMenuItem(value: '', child: Text('Sem grupo')), ..._organization.groups.map((g) => DropdownMenuItem(value: g, child: Text(g, overflow: TextOverflow.ellipsis)))],
        onChanged: (v) => setState(() => _groupFilter = v ?? '*'),
      ),
      Wrap(spacing: 8, runSpacing: 4, children: [
        FilterChip(label: const Text('Por grupo'), selected: _grouped, onSelected: _organizationReady ? (v) => setState(() => _grouped = v) : null),
        FilterChip(label: const Text('Favoritos'), selected: _favoritesOnly, onSelected: _organizationReady ? (v) => setState(() => _favoritesOnly = v) : null),
        PopupMenuButton<String>(tooltip: 'Filtrar tipo', onSelected: (v) => setState(() => _typeFilter = v), itemBuilder: (_) => [const PopupMenuItem(value: '*', child: Text('Todos os tipos')), ...CompanyOrganization.types.map((t) => PopupMenuItem(value: t, child: Text(t)))], child: Chip(label: Text(_typeFilter == '*' ? 'Todos os tipos ▾' : '$_typeFilter ▾'))),
        PopupMenuButton<String>(tooltip: 'Filtrar situação', onSelected: (v) => setState(() => _activityFilter = v), itemBuilder: (_) => const [PopupMenuItem(value: 'active', child: Text('Ativas')), PopupMenuItem(value: 'inactive', child: Text('Desativadas')), PopupMenuItem(value: '*', child: Text('Todas'))], child: Chip(label: Text(_activityFilter == 'active' ? 'Ativas ▾' : _activityFilter == 'inactive' ? 'Desativadas ▾' : 'Todas ▾'))),
      ]),
      if (_organizationReady) Align(alignment: Alignment.centerLeft, child: TextButton.icon(onPressed: _organizeCompanies, icon: const Icon(Icons.folder_copy_outlined), label: const Text('Organizar empresas'))),
    ]),
  );

  Widget _organizedCard(Company company) {
    final group = _organization.group(company.id);
    final type = _organization.type(company.id);
    return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
      Row(children: [
        Expanded(child: Text([group.isEmpty ? 'Sem grupo' : group, if (type.isNotEmpty) type].join(' • '), maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12))),
        IconButton(tooltip: 'Favoritar empresa', icon: Icon(_organization.favorite(company.id) ? Icons.star_rounded : Icons.star_border_rounded), onPressed: !_organizationReady ? null : () async {
          try { await _organization.assign([company.id], group, favorite: !_organization.favorite(company.id)); if (mounted) setState(() {}); }
          catch (_) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Não foi possível salvar o favorito.'))); }
        }),
      ]),
      _companyCard(company),
    ]);
  }

  List<Widget> _organizedCards(List<Company> visible) {
    if (!_grouped) return visible.map(_organizedCard).toList();
    final groups = <String, List<Company>>{};
    for (final c in visible) { groups.putIfAbsent(_organization.group(c.id), () => []).add(c); }
    final keys = groups.keys.toList()..sort((a, b) => a.isEmpty ? 1 : b.isEmpty ? -1 : CompanyOrganization.normalized(a).compareTo(CompanyOrganization.normalized(b)));
    return [for (final key in keys) ...[
      ListTile(title: Text('${key.isEmpty ? 'Sem grupo' : key} — ${groups[key]!.length}'), trailing: Icon(_collapsedGroups.contains(key) ? Icons.expand_more : Icons.expand_less), onTap: () => setState(() { if (!_collapsedGroups.add(key)) _collapsedGroups.remove(key); })),
      if (!_collapsedGroups.contains(key) || searchController.text.trim().isNotEmpty) ...groups[key]!.map(_organizedCard),
    ]];
  }
''' +s[end:]
replace("hintText: 'Buscar empresa, cidade ou CNPJ'", "hintText: 'Buscar empresa, grupo, tipo, cidade ou CNPJ'")
replace('                    const SizedBox(height: 12),\n                    Row(', '                    _organizationFilters(),\n                    const SizedBox(height: 12),\n                    Row(')
replace('...visible.map(_companyCard)', '..._organizedCards(visible)')
p.write_text(s, encoding="utf-8", newline="\n")
shutil.copyfile(repo/'feature_sources/company_organization_v329172_v33095.dart',root/'lib/widgets/company_organization.dart')
for path,digest in before.items():
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest, str(path)
shutil.copyfile(repo/'feature_sources/company_organization_test_v329172_v33095.dart', root/'test/company_organization_test.dart')
pub=root/'pubspec.yaml'; old,new=('3.29.171+313','3.29.172+314') if platform=='android' else ('3.30.94+281','3.30.95+282')
text=pub.read_text(encoding="utf-8"); assert text.count('version: '+old)==1; pub.write_text(text.replace('version: '+old,'version: '+new), encoding='utf-8', newline='\n')
print('COMPANY_ORGANIZATION_OK; PROTECTED_CORE_BYTE_IDENTICAL', platform)
