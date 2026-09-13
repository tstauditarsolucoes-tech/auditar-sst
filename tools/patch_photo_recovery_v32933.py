from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')

# Device sync: preserve local media paths on updates.
p = root / 'lib/services/device_sync_service.dart'
text = p.read_text(encoding='utf-8')
old = """          final payload = <String, Object?>{};\n          rawPayload.forEach((key, value) {\n            final name = '$key';\n            if (columns!.contains(name) &&\n                !(_localOnlyColumns[table] ?? const <String>{})\n                    .contains(name)) {\n              payload[name] = value as Object?;\n            }\n          });\n          payload['id'] = recordId;\n          if ((table == 'evidence_photos' || table == 'completion_photos') &&\n              !payload.containsKey('path')) {\n            payload['path'] = '';\n          }\n\n          final updated = await txn.update(\n            table,\n            payload,\n            where: 'id = ?',\n            whereArgs: [recordId],\n          );\n          if (updated == 0) {\n            await txn.insert(\n              table,\n              payload,\n              conflictAlgorithm: ConflictAlgorithm.replace,\n            );\n          }\n"""
new = """          final payload = <String, Object?>{};\n          rawPayload.forEach((key, value) {\n            final name = '$key';\n            if (columns!.contains(name) &&\n                !(_localOnlyColumns[table] ?? const <String>{})\n                    .contains(name)) {\n              payload[name] = value as Object?;\n            }\n          });\n          payload['id'] = recordId;\n\n          // Caminhos de fotos/assinaturas são locais de cada dispositivo.\n          // Ao atualizar um registro já existente, nunca substitua um caminho\n          // local válido por vazio vindo da sincronização estruturada.\n          final updated = await txn.update(\n            table,\n            payload,\n            where: 'id = ?',\n            whereArgs: [recordId],\n          );\n          if (updated == 0) {\n            if ((table == 'evidence_photos' || table == 'completion_photos') &&\n                !payload.containsKey('path')) {\n              // A coluna é obrigatória no SQLite. Para um registro novo vindo\n              // de outro dispositivo, o caminho será preenchido pelo sync de\n              // mídia assim que a evidência for recuperada do Drive.\n              payload['path'] = '';\n            }\n            await txn.insert(\n              table,\n              payload,\n              conflictAlgorithm: ConflictAlgorithm.replace,\n            );\n          }\n"""
if old not in text:
    raise SystemExit('Bloco de device sync não encontrado')
p.write_text(text.replace(old, new, 1), encoding='utf-8')

# Media sync: relink known local files before trying Drive.
p = root / 'lib/services/media_sync_service.dart'
text = p.read_text(encoding='utf-8')
old = """  static Future<MediaSyncSummary> downloadMissing() async {\n    if (!AuthService.isSignedIn) return const MediaSyncSummary();\n\n    final appDb = AppDatabase.instance;\n    final db = await appDb.database;\n    final rows = await db.query(\n"""
new = """  static Future<MediaSyncSummary> downloadMissing() async {\n    if (!AuthService.isSignedIn) return const MediaSyncSummary();\n\n    final appDb = AppDatabase.instance;\n    final db = await appDb.database;\n\n    // Repara primeiro vínculos locais que já existem no dispositivo.\n    await repairKnownLocalPaths();\n\n    final rows = await db.query(\n"""
if old not in text:
    raise SystemExit('Bloco downloadMissing não encontrado')
text = text.replace(old, new, 1)
marker = "  static Future<void> registerCompanyLogo({required String companyId, required String localPath}) async {\n"
insert = """  static Future<int> repairKnownLocalPaths() async {\n    final db = await AppDatabase.instance.database;\n    final rows = await db.query(\n      'media_assets',\n      where: 'local_path IS NOT NULL AND local_path <> \"\"',\n      orderBy: 'updated_at DESC',\n      limit: 600,\n    );\n\n    var repaired = 0;\n    for (final raw in rows) {\n      final row = Map<String, Object?>.from(raw);\n      final localPath = '${row['local_path'] ?? ''}'.trim();\n      if (localPath.isEmpty) continue;\n      final file = File(localPath);\n      if (!await file.exists()) continue;\n      await _applyEntityPath(db, row, localPath);\n      repaired++;\n    }\n    return repaired;\n  }\n\n"""
if marker not in text:
    raise SystemExit('Marcador de media sync não encontrado')
text = text.replace(marker, insert + marker, 1)
p.write_text(text, encoding='utf-8')

# Historical checklist: repair local paths and fetch missing media only when needed.
p = root / 'lib/screens/checklist_screen.dart'
text = p.read_text(encoding='utf-8')
if "import '../services/media_sync_service.dart';" not in text:
    text = text.replace("import '../services/checklist_validation_service.dart';\n", "import '../services/checklist_validation_service.dart';\nimport '../services/media_sync_service.dart';\n")
old = """  Future<void> _loadExistingData() async {\n    final db = AppDatabase.instance;\n    final answers = await db.getAnswers(widget.inspection.id);\n\n    for (final answer in answers) {\n"""
new = """  Future<void> _loadExistingData() async {\n    final db = AppDatabase.instance;\n\n    try {\n      await MediaSyncService.repairKnownLocalPaths();\n    } catch (_) {}\n\n    final answers = await db.getAnswers(widget.inspection.id);\n    var needsMediaRecovery = false;\n\n    for (final answer in answers) {\n"""
if old not in text:
    raise SystemExit('Início de _loadExistingData não encontrado')
text = text.replace(old, new, 1)
old = """      final evidence = await db.getPhotosForAnswer(answer.id);\n      photos[answer.questionId] =\n          evidence.map((photo) => photo.path).toList();\n\n      final ncs = await db.getNonConformitiesForAnswer(answer.id);\n"""
new = """      final evidence = await db.getPhotosForAnswer(answer.id);\n      photos[answer.questionId] =\n          evidence.map((photo) => photo.path).toList();\n      if (evidence.any((photo) =>\n          photo.path.trim().isEmpty || !File(photo.path).existsSync())) {\n        needsMediaRecovery = true;\n      }\n\n      final ncs = await db.getNonConformitiesForAnswer(answer.id);\n"""
if old not in text:
    raise SystemExit('Bloco de evidências não encontrado')
text = text.replace(old, new, 1)
old = """    if (!mounted) return;\n    setState(() => loadingExisting = false);\n  }\n"""
new = """    if (needsMediaRecovery) {\n      try {\n        await MediaSyncService.downloadMissing();\n        for (final answer in answers) {\n          if (!photos.containsKey(answer.questionId)) continue;\n          final refreshed = await db.getPhotosForAnswer(answer.id);\n          photos[answer.questionId] =\n              refreshed.map((photo) => photo.path).toList();\n        }\n      } catch (_) {\n        // Mantém a vistoria acessível offline.\n      }\n    }\n\n    if (!mounted) return;\n    setState(() => loadingExisting = false);\n  }\n"""
if old not in text:
    raise SystemExit('Final de _loadExistingData não encontrado')
text = text.replace(old, new, 1)
p.write_text(text, encoding='utf-8')

# Version.
p = root / 'pubspec.yaml'
text = p.read_text(encoding='utf-8').replace('version: 3.29.32+174', 'version: 3.29.33+175')
p.write_text(text, encoding='utf-8')
p = root / 'lib/screens/home_screen.dart'
text = p.read_text(encoding='utf-8').replace('versão 3.29.32', 'versão 3.29.33')
p.write_text(text, encoding='utf-8')

print('v3.29.33 photo recovery aplicado com sucesso')
