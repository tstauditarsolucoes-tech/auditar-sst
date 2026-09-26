import 'dart:convert';
import 'dart:io';

import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

/// Local, per-company/per-round unsent field notes. This is NOT a cloud backup.
///
/// Saved observations and their media continue through existing mechanisms.
/// The sidecar is deliberately outside the database and sync protocol.
class ExpressRoundDraftStorage {
  static String _safe(String value) =>
      value.replaceAll(RegExp(r'[^a-zA-Z0-9_-]'), '_');

  static Future<File> _file(
    String companyId,
    String roundId, {
    Directory? root,
  }) async {
    if (companyId.trim().isEmpty || roundId.trim().isEmpty) {
      throw ArgumentError('Company and round must be identified.');
    }
    final base = root ?? await getApplicationDocumentsDirectory();
    return File(p.join(
      base.path,
      'auditar_round_drafts',
      _safe(companyId),
      _safe(roundId) + '.json',
    ));
  }

  static Future<void> save(
    String companyId,
    String roundId,
    Map<String, dynamic> draft, {
    Directory? root,
  }) async {
    final target = await _file(companyId, roundId, root: root);
    await target.parent.create(recursive: true);
    final temp = File(target.path + '.tmp');
    final backup = File(target.path + '.bak');
    final document = <String, dynamic>{
      ...draft,
      'draftSchema': 1,
      'companyId': companyId,
      'roundId': roundId,
      'savedAt': DateTime.now().toUtc().toIso8601String(),
    };
    await temp.writeAsString(jsonEncode(document), flush: true);

    // A previous good draft stays recoverable if the process is killed between
    // renaming the current file and promoting the new snapshot.
    if (await target.exists()) {
      if (await backup.exists()) await backup.delete();
      await target.rename(backup.path);
    }
    try {
      await temp.rename(target.path);
      if (await backup.exists()) await backup.delete();
    } catch (_) {
      if (!await target.exists() && await backup.exists()) {
        await backup.rename(target.path);
      }
      rethrow;
    }
  }

  static Future<Map<String, dynamic>?> load(
    String companyId,
    String roundId, {
    Directory? root,
  }) async {
    final target = await _file(companyId, roundId, root: root);
    final backup = File(target.path + '.bak');
    for (final file in [target, backup]) {
      if (!await file.exists()) continue;
      try {
        final decoded = jsonDecode(await file.readAsString());
        if (decoded is! Map) continue;
        final draft = Map<String, dynamic>.from(decoded);
        if (draft['draftSchema'] != 1 ||
            draft['companyId'] != companyId ||
            draft['roundId'] != roundId) {
          continue;
        }
        return draft;
      } catch (_) {
        // A valid previous snapshot can still be present in .bak.
      }
    }
    return null;
  }

  static Future<void> clear(
    String companyId,
    String roundId, {
    Directory? root,
  }) async {
    final target = await _file(companyId, roundId, root: root);
    for (final path in [target.path, target.path + '.tmp', target.path + '.bak']) {
      final file = File(path);
      if (await file.exists()) await file.delete();
    }
  }
}
