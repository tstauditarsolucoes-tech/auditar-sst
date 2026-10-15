import 'dart:convert';
import 'package:flutter/material.dart';
import '../database.dart';
import '../models.dart';

// Organização pessoal local. Não participa do snapshot ou das permissões.
class CompanyOrganization {
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
  bool favorite(String id) => entries[id]?['favorite'] == true;
  Future<void> _pending = Future<void>.value();
  Future<void> assign(List<String> ids, String group, {String? type, bool? favorite}) {
    final operation = _pending.then((_) => _assign(ids, group, type: type, favorite: favorite));
    _pending = operation.catchError((Object _) {});
    return operation;
  }
  Future<void> _assign(List<String> ids, String group, {String? type, bool? favorite}) async {
    if (group.trim() == '*') throw ArgumentError('Nome reservado');
    final nextGroups = [...groups];
    final canonical = nextGroups.where((g) => normalized(g) == normalized(group)).firstOrNull;
    final selected = canonical ?? group.trim().replaceAll(RegExp(r'\s+'), ' ');
    if (selected.isNotEmpty && canonical == null) nextGroups.add(selected);
    nextGroups.sort((a, b) => normalized(a).compareTo(normalized(b)));
    final next = entries.map((k, v) => MapEntry(k, Map<String, dynamic>.from(v)));
    for (final id in ids) {
      next[id] = {...?next[id], 'group': selected, if (type != null) 'type': type, if (favorite != null) 'favorite': favorite};
    }
    await AppDatabase.instance.setSetting(key, jsonEncode({'groups': nextGroups, 'entries': next}));
    groups..clear()..addAll(nextGroups);
    entries..clear()..addAll(next);
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
    const Padding(padding: EdgeInsets.symmetric(vertical: 8), child: Text('Organização salva neste aparelho. Os acessos continuam individuais.', style: TextStyle(fontSize: 12))),
  ]);
}
