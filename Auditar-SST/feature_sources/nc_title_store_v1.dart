import 'dart:convert';

import '../database.dart';
import 'auth_service.dart';

/// Nome amigável local. Nunca substitui código, ID ou descrição original da NC.
class NcTitleStore {
  static String? get _storageKey {
    final userId = AuthService.currentUser?.id.trim() ?? '';
    return userId.isEmpty ? null : 'nc_display_names_v1_$userId';
  }

  static Future<Map<String, String>> load() async {
    final key = _storageKey;
    if (key == null) return <String, String>{};
    try {
      final raw = await AppDatabase.instance.getSetting(key);
      if (raw.trim().isEmpty) return <String, String>{};
      final value = jsonDecode(raw);
      if (value is! Map) return <String, String>{};
      return <String, String>{
        for (final entry in value.entries)
          if (entry.key is String && entry.value is String)
            entry.key as String: entry.value as String,
      };
    } catch (_) {
      return <String, String>{};
    }
  }

  static Future<void> save(String id, String value) async {
    final key = _storageKey;
    if (key == null || id.trim().isEmpty) {
      throw StateError('Usuário ou NC indisponível.');
    }
    final name = value.replaceAll(RegExp(r'\s+'), ' ').trim();
    if (name.length > 80) throw ArgumentError('Máximo de 80 caracteres.');
    final names = await load();
    if (name.isEmpty) {
      names.remove(id);
    } else {
      names[id] = name;
    }
    // Uso somente da chave de configuração local já existente; sem migração.
    await AppDatabase.instance.setSetting(key, jsonEncode(names));
  }

  static String displayTitle(
    Map<String, Object?> row,
    Map<String, String> names,
  ) {
    final id = '${row['id'] ?? ''}';
    final alias = (names[id] ?? '').trim();
    if (alias.isNotEmpty) return alias;
    final description = '${row['description'] ?? ''}'
        .replaceAll(RegExp(r'\s+'), ' ').trim();
    final question = '${row['question_text'] ?? ''}'
        .replaceAll(RegExp(r'\s+'), ' ').trim();
    final source = description.isNotEmpty ? description : question;
    if (source.isEmpty) return 'Não conformidade sem título';
    final first = source.split(RegExp(r'[.;!?]')).first.trim();
    final title = first.isEmpty ? source : first;
    return title.length <= 76 ? title : '${title.substring(0, 73).trimRight()}…';
  }
}
