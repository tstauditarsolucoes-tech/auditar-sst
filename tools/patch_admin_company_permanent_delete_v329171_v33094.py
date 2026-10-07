#!/usr/bin/env python3
"""Auditar SST v3.29.171 / v3.30.94 — exclusão definitiva somente ADM.

Autorização expressa do usuário:
- manter deleteCompanyIfUnused e seu bloqueio exatamente iguais para conta normal;
- adicionar uma segunda rotina destrutiva, acessível somente quando AuthService.isAdmin;
- usar os tombstones já existentes da sincronização, sem alterar o motor de sync;
- sem mudança de schema, autenticação, Apps Script, mídia ou transporte.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_admin_company_permanent_delete_v329171_v33094.py "
        "<APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
repo = Path(__file__).resolve().parents[1]

if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")

def method_bounds(text, signature):
    start = text.find(signature)
    if start < 0:
        raise RuntimeError("metodo ausente: " + signature)
    brace = text.find("{", start)
    if brace < 0:
        raise RuntimeError("abertura do metodo ausente: " + signature)
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
    raise RuntimeError("fim do metodo ausente: " + signature)

protected = [
    "lib/services/device_sync_service.dart",
    "lib/services/apps_script_http.dart",
    "lib/services/sync_coordinator.dart",
    "lib/services/auth_service.dart",
    "lib/services/drive_service.dart",
    "lib/services/media_sync_service.dart",
    "lib/services/ai_assistant_service.dart",
    "painel_web_google_apps_script/Code.gs",
    "painel_web_google_apps_script/MultiUser.gs",
    "painel_web_google_apps_script/ClientPortal.gs",
    "painel_web_google_apps_script/ClientPortal.html",
    "painel_web_google_apps_script/ReportEmail.gs",
]
before = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}

# Serviço de autorização ADM isolado.
src = repo / "feature_sources/admin_company_deletion_service_v329171_v33094.dart"
dst = root / "lib/services/admin_company_deletion_service.dart"
if not src.exists():
    raise RuntimeError("fonte do servico ADM ausente")
shutil.copyfile(src, dst)

# Banco: preserva o método comum exatamente e adiciona uma rotina separada.
db_rel = "lib/database.dart"
db = read(db_rel)
normal_signature = "  Future<bool> deleteCompanyIfUnused(String companyId) async {"
normal_start, normal_end = method_bounds(db, normal_signature)
normal_before = db[normal_start:normal_end]

admin_signature = "  Future<int> deleteCompanyPermanentlyAdmin(String companyId) async {"
if admin_signature not in db:
    admin_method = r'''

  /// Exclusão destrutiva usada somente pelo fluxo administrativo autorizado.
  ///
  /// Não substitui [deleteCompanyIfUnused]. O fluxo normal continua protegido
  /// contra exclusão de empresas com histórico.
  Future<int> deleteCompanyPermanentlyAdmin(String companyId) async {
    final id = companyId.trim();
    if (id.isEmpty) return 0;

    final db = await database;

    final tableRows = await db.rawQuery(
      "SELECT name FROM sqlite_master "
      "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'",
    );
    final tables = tableRows
        .map((row) => '${row['name'] ?? ''}'.trim())
        .where((name) => name.isNotEmpty)
        .toList(growable: false);

    final columnsByTable = <String, Set<String>>{};
    for (final table in tables) {
      final escaped = table.replaceAll('"', '""');
      try {
        final info = await db.rawQuery('PRAGMA table_info("$escaped")');
        columnsByTable[table] = info
            .map((row) => '${row['name'] ?? ''}'.trim())
            .where((name) => name.isNotEmpty)
            .toSet();
      } catch (_) {
        columnsByTable[table] = <String>{};
      }
    }

    Future<List<String>> idsWhere(
      String table,
      String where,
      List<Object?> whereArgs,
    ) async {
      if (!tables.contains(table) ||
          !(columnsByTable[table] ?? const <String>{}).contains('id')) {
        return <String>[];
      }
      try {
        final rows = await db.query(
          table,
          columns: const ['id'],
          where: where,
          whereArgs: whereArgs,
        );
        return rows
            .map((row) => '${row['id'] ?? ''}'.trim())
            .where((value) => value.isNotEmpty)
            .toList(growable: false);
      } catch (_) {
        return <String>[];
      }
    }

    Future<List<String>> idsIn(
      String table,
      String column,
      List<String> parentIds,
    ) async {
      if (parentIds.isEmpty) return <String>[];
      final columns = columnsByTable[table] ?? const <String>{};
      if (!tables.contains(table) ||
          !columns.contains('id') ||
          !columns.contains(column)) {
        return <String>[];
      }
      final placeholders = List.filled(parentIds.length, '?').join(',');
      return idsWhere(
        table,
        '$column IN ($placeholders)',
        List<Object?>.from(parentIds),
      );
    }

    final inspectionIds = await idsWhere(
      'inspections',
      'company_id = ?',
      <Object?>[id],
    );
    final answerIds = await idsIn(
      'answers',
      'inspection_id',
      inspectionIds,
    );
    final actionIds = await idsIn(
      'action_plans',
      'inspection_id',
      inspectionIds,
    );
    final workerIds = await idsWhere(
      'workers',
      'company_id = ?',
      <Object?>[id],
    );
    final electionIds = await idsWhere(
      'cipa_elections',
      'company_id = ?',
      <Object?>[id],
    );

    var removed = 0;

    await db.transaction((txn) async {
      Future<void> deleteIn(
        String table,
        String column,
        List<String> parentIds,
      ) async {
        if (parentIds.isEmpty) return;
        final columns = columnsByTable[table] ?? const <String>{};
        if (!columns.contains(column)) return;
        final placeholders = List.filled(parentIds.length, '?').join(',');
        try {
          removed += await txn.delete(
            table,
            where: '$column IN ($placeholders)',
            whereArgs: List<Object?>.from(parentIds),
          );
        } catch (_) {}
      }

      // Primeiro removemos filhos indiretos. Isso cobre também tabelas
      // adicionadas no futuro que usem estas chaves relacionais conhecidas.
      for (final table in tables) {
        if (table.startsWith('device_sync_')) continue;
        await deleteIn(table, 'action_id', actionIds);
      }
      for (final table in tables) {
        if (table.startsWith('device_sync_')) continue;
        await deleteIn(table, 'answer_id', answerIds);
      }
      for (final table in tables) {
        if (table.startsWith('device_sync_')) continue;
        await deleteIn(table, 'inspection_id', inspectionIds);
      }
      for (final table in tables) {
        if (table.startsWith('device_sync_')) continue;
        await deleteIn(table, 'worker_id', workerIds);
      }
      for (final table in tables) {
        if (table.startsWith('device_sync_')) continue;
        await deleteIn(table, 'election_id', electionIds);
      }

      // Depois removemos qualquer tabela diretamente vinculada à empresa.
      // device_sync_scopes é preservada para que tombstones já existentes
      // mantenham o companyId durante o próximo envio à Central.
      for (final table in tables) {
        if (table == 'companies' || table.startsWith('device_sync_')) {
          continue;
        }
        final columns = columnsByTable[table] ?? const <String>{};
        if (!columns.contains('company_id')) continue;
        try {
          removed += await txn.delete(
            table,
            where: 'company_id = ?',
            whereArgs: <Object?>[id],
          );
        } catch (_) {}
      }

      removed += await txn.delete(
        'companies',
        where: 'id = ?',
        whereArgs: <Object?>[id],
      );
    });

    return removed;
  }
'''
    db = db[:normal_end] + admin_method + db[normal_end:]
    write(db_rel, db)

# Garante que o método comum ficou byte a byte igual no texto.
db_after = read(db_rel)
check_start, check_end = method_bounds(db_after, normal_signature)
if db_after[check_start:check_end] != normal_before:
    raise RuntimeError("deleteCompanyIfUnused foi alterado; bloqueio normal deve permanecer")

# Tela Empresas: adiciona opção separada apenas para ADM.
screen_rel = "lib/screens/companies_screen.dart"
screen = read(screen_rel)
normal_ui_start, normal_ui_end = method_bounds(
    screen,
    "  Future<void> _deleteCompany(Company company) async {",
)
normal_ui_before = screen[normal_ui_start:normal_ui_end]

if "admin_company_deletion_service.dart" not in screen:
    import_anchor = "import '../services/device_sync_service.dart';\n"
    if import_anchor not in screen:
        raise RuntimeError("import DeviceSyncService ausente na tela Empresas")
    extra = ""
    if "auth_service.dart" not in screen:
        extra += "import '../services/auth_service.dart';\n"
    extra += "import '../services/admin_company_deletion_service.dart';\n"
    screen = screen.replace(import_anchor, import_anchor + extra, 1)

if "Future<void> _deleteCompanyPermanentlyAdmin" not in screen:
    _, delete_end = method_bounds(
        screen,
        "  Future<void> _deleteCompany(Company company) async {",
    )
    admin_ui = r'''

  Future<void> _deleteCompanyPermanentlyAdmin(Company company) async {
    if (!AuthService.isAdmin) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'A exclusão definitiva é exclusiva da conta administradora.',
          ),
        ),
      );
      return;
    }

    final typedName = TextEditingController();
    var exactName = false;
    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (dialogContext) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Excluir empresa definitivamente?'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Você está prestes a excluir “${company.name}” e os registros '
                  'vinculados a ela no Auditar SST.',
                ),
                const SizedBox(height: 10),
                const Text(
                  'Serão removidos, quando existirem: vistorias, respostas, '
                  'não conformidades, planos de ação, trabalhadores, '
                  'treinamentos, registros SST, CIPA e demais dados vinculados.',
                  style: TextStyle(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 10),
                const Text(
                  'Esta ação não pode ser desfeita. Para confirmar, digite '
                  'exatamente o nome da empresa abaixo.',
                ),
                const SizedBox(height: 14),
                TextField(
                  controller: typedName,
                  autofocus: true,
                  onChanged: (value) {
                    final matches = value.trim() == company.name.trim();
                    if (matches != exactName) {
                      setDialogState(() => exactName = matches);
                    }
                  },
                  decoration: InputDecoration(
                    labelText: 'Digite exatamente: ${company.name}',
                    border: const OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext, false),
              child: const Text('Cancelar'),
            ),
            FilledButton.icon(
              style: FilledButton.styleFrom(
                backgroundColor: Theme.of(context).colorScheme.error,
                foregroundColor: Theme.of(context).colorScheme.onError,
              ),
              onPressed: exactName
                  ? () => Navigator.pop(dialogContext, true)
                  : null,
              icon: const Icon(Icons.delete_forever_rounded),
              label: const Text('Excluir definitivamente'),
            ),
          ],
        ),
      ),
    );
    typedName.dispose();

    if (confirmed != true) return;

    try {
      final removed =
          await AdminCompanyDeletionService.deletePermanently(company.id);

      var synchronized = false;
      try {
        await DeviceSyncService.synchronize(force: true);
        synchronized = true;
      } catch (_) {
        // Os tombstones permanecem na fila e serão enviados na próxima sync.
      }

      await _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            synchronized
                ? 'Empresa excluída definitivamente. $removed registro(s) '
                    'removido(s) e exclusão enviada para a Central.'
                : 'Empresa excluída neste aparelho. $removed registro(s) '
                    'removido(s); a exclusão online ficará pendente até a '
                    'próxima sincronização.',
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'Não foi possível excluir definitivamente: '
            '${e.toString().replaceFirst('Bad state: ', '')}',
          ),
        ),
      );
    }
  }
'''
    screen = screen[:delete_end] + admin_ui + screen[delete_end:]

if "delete_permanent_admin" not in screen:
    selected_anchor = "                        if (value == 'delete') _deleteCompany(company);"
    if selected_anchor not in screen:
        raise RuntimeError("acao delete normal ausente na tela Empresas")
    screen = screen.replace(
        selected_anchor,
        selected_anchor
        + "\n"
        + "                        if (value == 'delete_permanent_admin') {\n"
        + "                          _deleteCompanyPermanentlyAdmin(company);\n"
        + "                        }",
        1,
    )

    item_anchor = (
        "                        const PopupMenuItem("
        "value: 'delete', child: Text('Excluir')),"
    )
    if item_anchor not in screen:
        raise RuntimeError("item Excluir normal ausente na tela Empresas")
    admin_item = r'''
                        if (AuthService.isAdmin)
                          const PopupMenuItem(
                            value: 'delete_permanent_admin',
                            child: Row(
                              children: [
                                Icon(
                                  Icons.delete_forever_rounded,
                                  color: Colors.red,
                                  size: 19,
                                ),
                                SizedBox(width: 8),
                                Text(
                                  'Excluir definitivamente (ADM)',
                                  style: TextStyle(
                                    color: Colors.red,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                              ],
                            ),
                          ),'''
    screen = screen.replace(item_anchor, item_anchor + admin_item, 1)

write(screen_rel, screen)

# Confirma que o fluxo normal da tela também permaneceu textual e funcionalmente igual.
screen_after = read(screen_rel)
ui_start, ui_end = method_bounds(
    screen_after,
    "  Future<void> _deleteCompany(Company company) async {",
)
if screen_after[ui_start:ui_end] != normal_ui_before:
    raise RuntimeError("_deleteCompany normal foi alterado")

# Versionamento final.
pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_version, new_version = (
    ("3.29.170+312", "3.29.171+313")
    if platform == "android"
    else ("3.30.93+280", "3.30.94+281")
)
marker = "version: " + old_version
if pub.count(marker) != 1:
    raise RuntimeError("versao base esperada ausente: " + old_version)
write(pub_rel, pub.replace(marker, "version: " + new_version, 1))

# Proteções: sync/auth/transporte/mídia/IA/GS não podem mudar.
after = {
    name: hashlib.sha256((root / name).read_bytes()).hexdigest()
    for name in protected
}
changed = [name for name in protected if before[name] != after[name]]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

db_final = read(db_rel)
screen_final = read(screen_rel)
service_final = read("lib/services/admin_company_deletion_service.dart")

assert normal_before in db_final
assert normal_ui_before in screen_final
assert admin_signature in db_final
assert "if (!AuthService.isAdmin)" in service_final
assert "delete_permanent_admin" in screen_final
assert "if (AuthService.isAdmin)" in screen_final
assert "Digite exatamente:" in screen_final
assert "device_sync_" in db_final
assert "version: " + new_version in read(pub_rel)

print("ADMIN_PERMANENT_COMPANY_DELETE_OK", platform, new_version)
print("NORMAL_ACCOUNT_DELETE_BLOCK_PRESERVED_OK")
print("ADMIN_DOUBLE_GUARD_OK")
print("EXACT_NAME_CONFIRMATION_OK")
print("SYNC_AUTH_HTTP_MEDIA_AI_GS_BYTE_IDENTICAL_OK")
