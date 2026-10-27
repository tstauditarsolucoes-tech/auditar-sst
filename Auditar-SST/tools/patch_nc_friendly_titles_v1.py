#!/usr/bin/env python3
"""Apelidos locais de NC no Android/Windows; preservar código, descrição, sync, PDF e esquema."""
from pathlib import Path
import hashlib
import re
import shutil
import sys

app = Path(sys.argv[1])
repo = Path(__file__).resolve().parents[1]

def once(source, needle, change, label):
    n = source.count(needle)
    assert n == 1, f'{label}: âncora esperada uma vez, encontrada {n}'
    return source.replace(needle, change, 1)

protected = [app/'lib/database.dart', app/'lib/models.dart',
             *(app/'lib/services').glob('*'),
             *(app/'painel_web_google_apps_script').glob('*')]
digests = {p: hashlib.sha256(p.read_bytes()).hexdigest()
           for p in protected if p.is_file()}

p = app/'lib/screens/non_conformities_screen.dart'
s = p.read_text(encoding='utf-8')
s = once(s, "import '../database.dart';",
         "import '../database.dart';\nimport '../services/nc_title_store.dart';", 'import NC')
s = once(s, '  Map<String, int> counts = {};',
         '  Map<String, int> counts = {};\n  Map<String, String> _ncDisplayNames = {};', 'estado NC')
s = once(s, '    if (!mounted) return;\n    setState(() {\n      rows = result;',
         '    final savedNames = await NcTitleStore.load();\n    if (!mounted) return;\n'
         '    setState(() {\n      _ncDisplayNames = savedNames;\n      rows = result;', 'leitura NC')
s = once(s, "        row['code'],\n        row['company_name'],",
         "        row['code'],\n        NcTitleStore.displayTitle(row, _ncDisplayNames),\n        row['company_name'],",
         'busca por nome')
editor = """  Future<void> _editDisplayName(Map<String, Object?> record) async {
    final id = '${record['id'] ?? ''}'.trim();
    if (id.isEmpty) return;
    final controller = TextEditingController(text: _ncDisplayNames[id] ?? '');
    final name = await showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Nome da não conformidade'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Ex.: Proteção removida ou Extintor vencido. '
                'O código e a descrição técnica não serão alterados.'),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              autofocus: true,
              maxLength: 80,
              maxLines: 2,
              textCapitalization: TextCapitalization.sentences,
              decoration: const InputDecoration(
                labelText: 'Nome curto',
                hintText: 'Ex.: Extintor vencido',
                border: OutlineInputBorder(),
              ),
            ),
            const Text('Deixe em branco para exibir a descrição automaticamente.'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(dialogContext).pop(controller.text.trim()),
            child: const Text('Salvar nome'),
          ),
        ],
      ),
    );
    if (!mounted || name == null) return;
    try {
      await NcTitleStore.save(id, name);
      final savedNames = await NcTitleStore.load();
      if (!mounted) return;
      setState(() => _ncDisplayNames = savedNames);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Nome salvo neste aparelho. Código original preservado.')),
      );
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Não foi possível salvar o nome desta NC.')),
      );
    }
  }

"""
s = once(s, '  Color _priorityColor(String priority) {',
         editor+'  Color _priorityColor(String priority) {', 'edição NC')
card_old = """                              Expanded(
                                child: Text(
                                  '${row['code'] ?? 'NC'}',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w800,
                                    color: AuditarBrand.navy,
                                  ),
                                ),
                              ),"""
card_new = """                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      NcTitleStore.displayTitle(row, _ncDisplayNames),
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                        color: AuditarBrand.navy,
                                      ),
                                    ),
                                    Text(
                                      'Código: ${row['code'] ?? 'NC'}',
                                      style: const TextStyle(fontSize: 11, color: Colors.black54),
                                    ),
                                  ],
                                ),
                              ),
                              IconButton(
                                tooltip: 'Nomear NC',
                                icon: const Icon(Icons.edit_outlined, size: 19),
                                onPressed: () => _editDisplayName(row),
                              ),"""
s = once(s, card_old, card_new, 'cartão NC')
p.write_text(s, encoding='utf-8', newline='\n')

p = app/'lib/screens/non_conformity_detail_screen.dart'
s = p.read_text(encoding='utf-8')
s = once(s, "import '../database.dart';",
         "import '../database.dart';\nimport '../services/nc_title_store.dart';", 'import detalhe')
s = once(s, '  bool resolvingNow = false;',
         "  bool resolvingNow = false;\n  String _localDisplayName = '';", 'estado detalhe')
s = once(s, '    final loadedActions = await db.getActionsForNonConformity(widget.ncId);',
         '    final loadedActions = await db.getActionsForNonConformity(widget.ncId);\n'
         '    final names = await NcTitleStore.load();', 'leitura detalhe')
s = once(s, '      actions = loadedActions;\n      loading = false;',
         '      actions = loadedActions;\n      _localDisplayName = names[widget.ncId] ?? \'\';\n'
         '      loading = false;', 'estado carregado detalhe')
s = once(s, '        title: Text(current.code, maxLines: 1, overflow: TextOverflow.ellipsis),',
         "        title: Text(_localDisplayName.isEmpty ? current.code : _localDisplayName,\n"
         "            maxLines: 1, overflow: TextOverflow.ellipsis),", 'cabeçalho detalhe')
p.write_text(s, encoding='utf-8', newline='\n')

# Lista de prioridades usa o mesmo nome salvo localmente.
p = app/'lib/screens/field_operational_control_screen.dart'
s = p.read_text(encoding='utf-8')
s = once(s, "import '../services/media_sync_service.dart';",
         "import '../services/media_sync_service.dart';\nimport '../services/nc_title_store.dart';", 'import pendências')
s = once(s, "  String lastSyncStatus = '';",
         "  String lastSyncStatus = '';\n  Map<String, String> _ncDisplayNames = {};", 'estado pendências')
s = once(s, "      final syncStatus = await db.getSetting('last_device_sync_status');",
         "      final syncStatus = await db.getSetting('last_device_sync_status');\n"
         "      final names = await NcTitleStore.load();", 'leitura pendências')
s = once(s, '        lastSyncStatus = syncStatus.trim();',
         '        lastSyncStatus = syncStatus.trim();\n        _ncDisplayNames = names;', 'estado pendências carregado')
pattern_mobile = re.compile(
    r"final\s+summary\s*=\s*_value\(row,\s*'code'\)\.isNotEmpty\s*"
    r"\?\s*_value\(row,\s*'code'\)\s*:\s*_value\(row,\s*'description'\)\s*;"
)
s, mobile = pattern_mobile.subn(
    'final summary = NcTitleStore.displayTitle(row, _ncDisplayNames);', s)
pattern_desktop = re.compile(
    r"title:\s*_value\(row,\s*'code'\)\.isNotEmpty\s*"
    r"\?\s*_value\(row,\s*'code'\)\s*:\s*_value\(row,\s*'description'\)\s*,"
)
s, desktop = pattern_desktop.subn(
    'title: NcTitleStore.displayTitle(row, _ncDisplayNames),', s)
assert mobile + desktop >= 1, 'Título de NC não encontrado na lista de pendências'
p.write_text(s, encoding='utf-8', newline='\n')

service = app/'lib/services/nc_title_store.dart'
assert not service.exists(), 'Módulo de nome de NC já instalado; não sobrescrever'
shutil.copyfile(repo/'feature_sources/nc_title_store_v1.dart', service)
shutil.copyfile(repo/'feature_sources/nc_title_store_test_v1.dart',
                app/'test/nc_title_store_test.dart')

for file, expected in digests.items():
    assert hashlib.sha256(file.read_bytes()).hexdigest() == expected, f'Núcleo modificado: {file}'
print('NC_TITLES_V1_OK: names local by account, identifiers and sync intact')
