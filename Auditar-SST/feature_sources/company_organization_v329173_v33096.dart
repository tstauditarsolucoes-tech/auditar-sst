import 'dart:convert';
import 'package:flutter/material.dart';
import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/apps_script_http.dart';

// Organização pessoal local. Não participa do snapshot ou das permissões.
class CompanyOrganization {
  List<dynamic>? remoteConflict;
  String syncMessage = '';
  static const key = 'company_organization_local_v1';
  static const types = ['Padaria', 'Obra', 'Indústria', 'Outros'];
  final List<String> groups;
  final Map<String, Map<String, dynamic>> entries;
  CompanyOrganization({List<String>? groups, Map<String, Map<String, dynamic>>? entries})
      : groups = groups ?? [], entries = entries ?? {};
  static String normalized(String value) => value.trim().replaceAll(RegExp(r'\s+'), ' ').toLowerCase();
  static Future<CompanyOrganization> load() async {
    final raw = await AppDatabase.instance.getSetting(key);
    if (raw.isEmpty) return CompanyOrganization();
    final decoded = jsonDecode(raw) as Map<String, dynamic>;
    return CompanyOrganization(
      groups: (decoded['groups'] as List).cast<String>(),
      entries: (decoded['entries'] as Map<String, dynamic>).map((k, v) => MapEntry(k, Map<String, dynamic>.from(v as Map))),
    );
  }
  String group(String id) => entries[id]?['group'] as String? ?? '';
  String type(String id) => entries[id]?['type'] as String? ?? '';
  String alias(String id) => entries[id]?['alias'] as String? ?? '';
  bool favorite(String id) => entries[id]?['favorite'] == true;
  Future<void> _pending = Future<void>.value();
  Future<void> assign(List<String> ids, String group, {String? type, bool? favorite, String? alias}) {
    final operation = _pending.then((_) => _assign(ids, group, type: type, favorite: favorite, alias: alias));
    _pending = operation.catchError((Object _) {});
    return operation;
  }
  Future<void> _assign(List<String> ids, String group, {String? type, bool? favorite, String? alias}) async {
    if (group.trim() == '*') throw ArgumentError('Nome reservado');
    final nextGroups = [...groups];
    final canonical = nextGroups.where((g) => normalized(g) == normalized(group)).firstOrNull;
    final selected = canonical ?? group.trim().replaceAll(RegExp(r'\s+'), ' ');
    if (selected.isNotEmpty && canonical == null) nextGroups.add(selected);
    nextGroups.sort((a, b) => normalized(a).compareTo(normalized(b)));
    final next = entries.map((k, v) => MapEntry(k, Map<String, dynamic>.from(v)));
    for (final id in ids) {
      final previous = next[id] ?? <String, dynamic>{};
      final sharedChanged = (previous['group'] ?? '') != selected ||
          (type != null && type != (previous['type'] ?? '')) ||
          (alias != null && alias != (previous['alias'] ?? ''));
      next[id] = {...previous, 'group': selected,
        if (sharedChanged) '_dirty': true,
        if (alias != null) 'alias': alias, if (type != null) 'type': type, if (favorite != null) 'favorite': favorite};
    }
    await AppDatabase.instance.setSetting(key, jsonEncode({'groups': nextGroups, 'entries': next}));
    groups..clear()..addAll(nextGroups);
    entries..clear()..addAll(next);
  }
  Future<void> save() => AppDatabase.instance.setSetting(key, jsonEncode({'groups': groups, 'entries': entries}));
  Future<void> renameGroup(String oldName, String newName, List<String> allowedIds) {
    final operation = _pending.then((_) => _renameGroup(oldName,newName,allowedIds));
    _pending = operation.catchError((Object _) {});
    return operation;
  }
  Future<void> _renameGroup(String oldName, String newName, List<String> allowedIds) async {
    final target = newName.trim().replaceAll(RegExp(r'\s+'), ' ');
    if (target == '*' || target.length > 80) throw ArgumentError('Nome inválido');
    final existing = groups.where((g) => g != oldName && normalized(g) == normalized(target)).firstOrNull;
    final selected = existing ?? target;
    final next = entries.map((k,v) => MapEntry(k, Map<String,dynamic>.from(v)));
    for (final id in allowedIds) { if (group(id) == oldName) next[id] = {...?next[id], 'group': selected, '_dirty': true}; }
    final nextGroups = [...groups];
    if (!next.values.any((e) => e['group'] == oldName)) nextGroups.remove(oldName);
    if (selected.isNotEmpty && !nextGroups.contains(selected)) nextGroups.add(selected);
    await AppDatabase.instance.setSetting(key, jsonEncode({'groups':nextGroups,'entries':next}));
    entries..clear()..addAll(next); groups..clear()..addAll(nextGroups);
  }
  String lastVisit(String id) => entries[id]?['_lastVisit'] as String? ?? '';
  Future<void> markVisited(String id) {
    final operation = _pending.then((_) => _markVisited(id));
    _pending = operation.catchError((Object _) {});
    return operation;
  }
  Future<void> _markVisited(String id) async {
    final next = entries.map((k,v) => MapEntry(k, Map<String,dynamic>.from(v)));
    next[id] = {...?next[id], '_lastVisit': DateTime.now().toUtc().toIso8601String()};
    await AppDatabase.instance.setSetting(key, jsonEncode({'groups':groups,'entries':next}));
    entries..clear()..addAll(next);
  }
  Future<void> sync(List<String> allowedIds) async {
    final operation = _pending.then((_) => _sync(allowedIds));
    _pending = operation.catchError((Object _) {});
    return operation;
  }
  Future<void> _sync(List<String> allowedIds) async {
    if (!AuthService.isSignedIn) throw StateError('Entre online para compartilhar os grupos.');
    final userId = AppDatabase.activeUserId;
    final endpoint = await AppDatabase.instance.getSetting('management_panel_endpoint');
    final changes = <Map<String, Object?>>[];
    for (final id in allowedIds) {
      final entry = entries[id];
      if (entry == null) continue;
      final legacy = !entry.containsKey('_version') && (group(id).isNotEmpty || type(id).isNotEmpty || alias(id).isNotEmpty);
      if (entry['_dirty'] == true || legacy) changes.add({'companyId': id, 'group': group(id), 'type': type(id), 'alias': alias(id), 'baseVersion': entry['_version'] ?? 0});
    }
    final response = await AppsScriptHttp.postJson(Uri.parse(endpoint), {'action': 'company_groups_sync_v1', 'authToken': AuthService.sessionToken, 'changes': changes}, timeout: const Duration(seconds: 25));
    if (response.statusCode != 200) throw StateError('Não foi possível conectar a organização da Central.');
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    if (userId != AppDatabase.activeUserId) throw StateError('A conta foi alterada. Atualize a lista.');
    if (body['code'] == 'GROUP_CONFLICT') { remoteConflict = body['items'] as List; syncMessage = 'Conflito: a organização mudou em outro aparelho.'; return; }
    if (body['ok'] != true || body['items'] is! List) throw StateError('O módulo de grupos precisa estar instalado na Central. A organização local foi preservada.');
    await _acceptRemote(body['items'] as List, allowedIds);
    syncMessage = 'Grupos compartilhados com a Central.';
  }
  Future<void> acceptRemote(List<dynamic> items, List<String> allowedIds) {
    final operation = _pending.then((_) => _acceptRemote(items,allowedIds));
    _pending = operation.catchError((Object _) {});
    return operation;
  }
  Future<void> _acceptRemote(List<dynamic> items, List<String> allowedIds) async {
    final next = entries.map((k,v) => MapEntry(k, Map<String,dynamic>.from(v)));
    final nextGroups = [...groups];
    for (final raw in items) {
      if (raw is! Map || !allowedIds.contains(raw['companyId'])) continue;
      final id = raw['companyId'] as String;
      next[id] = {...?next[id], 'group': raw['group'], 'type': raw['type'], 'alias': raw['alias'], '_version': raw['version'], '_dirty': false};
      final name = raw['group'] as String;
      if (name.isNotEmpty && !nextGroups.contains(name)) nextGroups.add(name);
    }
    await AppDatabase.instance.setSetting(key, jsonEncode({'groups':nextGroups,'entries':next}));
    entries..clear()..addAll(next); groups..clear()..addAll(nextGroups); remoteConflict = null;
  }

}

class CompanyOrganizationEditor extends StatefulWidget {
  final CompanyOrganization organization;
  final String initialGroup;
  final String initialType;
  final void Function(String, String) onChanged;
  const CompanyOrganizationEditor({super.key, required this.organization, required this.initialGroup, required this.initialType, required this.onChanged});
  @override
  State<CompanyOrganizationEditor> createState() => _CompanyOrganizationEditorState();
}
class _CompanyOrganizationEditorState extends State<CompanyOrganizationEditor> {
  late String group = widget.initialGroup;
  late String type = widget.initialType;
  late List<String> groups = [...widget.organization.groups];
  Future<void> create() async {
    final controller = TextEditingController();
    final value = await showDialog<String>(context: context, builder: (context) => AlertDialog(
      title: const Text('Criar grupo'),
      content: TextField(controller: controller, maxLength: 80, autofocus: true, decoration: const InputDecoration(labelText: 'Nome do grupo', hintText: 'Ex.: Construtora Quality')),
      actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')), FilledButton(onPressed: () { if (controller.text.trim().isNotEmpty) Navigator.pop(context, controller.text.trim()); }, child: const Text('Criar'))],
    ));
    // O campo é desmontado antes de descartar seu controller.
    WidgetsBinding.instance.addPostFrameCallback((_) => controller.dispose());
    if (value == null || !mounted) return;
    if (value == '*') {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Escolha um nome para o grupo.')));
      return;
    }
    final existing = groups.where((g) => CompanyOrganization.normalized(g) == CompanyOrganization.normalized(value)).firstOrNull;
    setState(() { group = existing ?? value; if (existing == null) groups.add(group); });
    widget.onChanged(group, type);
    if (existing != null) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Grupo já existente selecionado.')));
  }
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
    DropdownButtonFormField<String>(key: ValueKey(group), initialValue: group, isExpanded: true, decoration: const InputDecoration(labelText: 'Grupo empresarial'), items: [const DropdownMenuItem(value: '', child: Text('Sem grupo — independente', overflow: TextOverflow.ellipsis)), ...groups.map((g) => DropdownMenuItem(value: g, child: Text(g, overflow: TextOverflow.ellipsis)))], onChanged: (v) { setState(() => group = v ?? ''); widget.onChanged(group, type); }),
    Align(alignment: Alignment.centerLeft, child: TextButton.icon(onPressed: create, icon: const Icon(Icons.create_new_folder_outlined), label: const Text('Criar novo grupo'))),
    DropdownButtonFormField<String>(initialValue: type, isExpanded: true, decoration: const InputDecoration(labelText: 'Tipo de empresa'), items: [const DropdownMenuItem(value: '', child: Text('Não informado')), ...CompanyOrganization.types.map((t) => DropdownMenuItem(value: t, child: Text(t)))], onChanged: (v) { setState(() => type = v ?? ''); widget.onChanged(group, type); }),
    const Padding(padding: EdgeInsets.symmetric(vertical: 8), child: Text('Funciona offline. Use Compartilhar grupos para enviar à Central. Os acessos continuam individuais.', style: TextStyle(fontSize: 12))),
  ]);
}
