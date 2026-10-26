import 'dart:convert';

import '../database.dart';
import 'auth_service.dart';

class TutorialService {
  TutorialService._();

  static const String tutorialVersion = '1';

  static String get _scope {
    final raw = (AuthService.currentUser?.id ?? 'local').trim();
    final safe = raw.replaceAll(RegExp(r'[^A-Za-z0-9_-]'), '_');
    return safe.isEmpty ? 'local' : safe;
  }

  static String get _seenKey =>
      'mini_tutorial_${tutorialVersion}_seen_$_scope';
  static String get _disabledKey =>
      'mini_tutorial_${tutorialVersion}_disabled_$_scope';

  static Future<Set<String>> _readSeen() async {
    final raw = await AppDatabase.instance.getSetting(_seenKey, fallback: '[]');
    if (raw.trim().isEmpty) return <String>{};
    try {
      final decoded = jsonDecode(raw);
      if (decoded is List) {
        return decoded.map((item) => '$item').toSet();
      }
    } catch (_) {}
    return <String>{};
  }

  static Future<bool> shouldShow(String screenId) async {
    final disabled = await AppDatabase.instance.getSetting(
      _disabledKey,
      fallback: 'false',
    );
    if (disabled == 'true') return false;
    final seen = await _readSeen();
    return !seen.contains(screenId);
  }

  static Future<void> markSeen(String screenId) async {
    final seen = await _readSeen();
    if (seen.add(screenId)) {
      final ordered = seen.toList()..sort();
      await AppDatabase.instance.setSetting(_seenKey, jsonEncode(ordered));
    }
  }

  static Future<void> disableAll() async {
    await AppDatabase.instance.setSetting(_disabledKey, 'true');
  }

  static Future<void> resetForCurrentAccount() async {
    await AppDatabase.instance.setSetting(_seenKey, '[]');
    await AppDatabase.instance.setSetting(_disabledKey, 'false');
  }
}
