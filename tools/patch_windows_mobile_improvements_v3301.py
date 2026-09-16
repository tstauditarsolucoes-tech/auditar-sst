#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
syncp = root / 'lib/services/device_sync_service.dart'
coordp = root / 'lib/services/sync_coordinator.dart'
listp = root / 'lib/screens/sst_records_screen.dart'
hubp = root / 'lib/screens/routine_hub_screen.dart'
dbp = root / 'lib/database.dart'
mediap = root / 'lib/services/media_sync_service.dart'

for p in (pubp, syncp, coordp, listp, hubp, dbp, mediap):
    if not p.exists():
        raise RuntimeError(f'Arquivo obrigatório ausente: {p}')

pub = pubp.read_text(encoding='utf-8')
sync = syncp.read_text(encoding='utf-8')
coord = coordp.read_text(encoding='utf-8')
listing = listp.read_text(encoding='utf-8')
hub = hubp.read_text(encoding='utf-8')
db = dbp.read_text(encoding='utf-8')
media = mediap.read_text(encoding='utf-8')


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)

# ---------------------------------------------------------------------------
# Versão Windows consolidada.
# ---------------------------------------------------------------------------
if 'version: 3.30.1+188' not in pub:
    pub = once(pub, 'version: 3.30.0+187', 'version: 3.30.1+188', 'versão 3.30.0')

# ---------------------------------------------------------------------------
# Sincronização: trazer para o PC os ganhos de latência do celular.
# Não copiamos DNS/IPv4 específico do Android.
# ---------------------------------------------------------------------------
# Lotes maiores no pull da Central.
sync = sync.replace("'limit': 100,", "'limit': 500,")
sync = sync.replace("'limit': 300,", "'limit': 500,")
sync = sync.replace('const pullPages = 12;', 'const pullPages = 60;')
sync = sync.replace('final pullPages = 12;', 'final pullPages = 60;')
sync = sync.replace('for (var page = 0; page < 12; page++) {', 'for (var page = 0; page < 60; page++) {')

# Protege edição local ainda não enviada contra sobrescrita por pull remoto.
apply_marker = """        final deleted = change['deleted'] == true;
        if (deleted) {
"""
apply_guard = """        final localDirty = await txn.query(
          _changesTable,
          columns: ['dirty'],
          where: 'table_name = ? AND record_id = ?',
          whereArgs: [table, recordId],
          limit: 1,
        );
        if (localDirty.isNotEmpty && _asInt(localDirty.first['dirty']) == 1) {
          // Mantém a edição local até o próximo envio; evita o PC perder
          // uma alteração feita localmente durante um pull da Central.
          continue;
        }

        final deleted = change['deleted'] == true;
        if (deleted) {
"""
if 'final localDirty = await txn.query(' not in sync and apply_marker in sync:
    sync = sync.replace(apply_marker, apply_guard, 1)

# O PC aberto consulta a Central com mais frequência. O timer limpo também pode
# executar pull remoto, sem exigir alteração local.
coord = coord.replace('const Duration(seconds: 20)', 'const Duration(seconds: 10)', 1)

# Há versões do coordenador com assinatura simples e outras com parâmetros extras.
old_sig = 'Future<void> _trySync({bool deviceOnly = false}) async {'
new_sig = '''Future<void> _trySync({
    bool deviceOnly = false,
    bool force = false,
    bool pullWhenClean = false,
  }) async {'''
if old_sig in coord:
    coord = coord.replace(old_sig, new_sig, 1)

# Permite ao timer de 10 s fazer apenas a verificação remota quando a fila local está limpa.
coord = coord.replace(
    '    if (deviceOnly) {\n      try {\n        final localPending = await DeviceSyncService.pendingChangesCount();\n        if (localPending == 0) return;',
    '    if (deviceOnly && !pullWhenClean) {\n      try {\n        final localPending = await DeviceSyncService.pendingChangesCount();\n        if (localPending == 0) return;',
    1,
)

# Timer automático: força a consulta remota sem depender do throttle de 60 s.
coord = coord.replace(
    '(_) => _trySync(deviceOnly: true),',
    '(_) => _trySync(deviceOnly: true, force: true, pullWhenClean: true),',
    1,
)

# Encaminha force ao serviço quando a assinatura acima foi adicionada.
if 'bool force = false,' in coord and 'DeviceSyncService.synchronize(force: force)' not in coord:
    coord = coord.replace(
        'result = await DeviceSyncService.synchronize();',
        'result = await DeviceSyncService.synchronize(force: force);',
        1,
    )

# ---------------------------------------------------------------------------
# Histórico permanente de DDS no PC + retirada da ficha.
# ---------------------------------------------------------------------------
listing = listing.replace(
    "return ('DDS', Icons.record_voice_over_outlined);",
    "return ('Histórico de DDS', Icons.record_voice_over_outlined);",
    1,
)

old_order = "      orderBy: 'COALESCE(due_date, date) ASC, date DESC',\n"
new_order = "      orderBy: type == 'DDS' ? 'date DESC' : 'COALESCE(due_date, date) ASC, date DESC',\n"
if new_order not in db and old_order in db:
    db = db.replace(old_order, new_order, 1)

listing = listing.replace(
    "child: Text('Gerando lista do DDS...'),",
    "child: Text('Preparando ficha do DDS...'),",
    1,
)
listing = listing.replace(
    "final filename = 'DDS_${safeTitle.isEmpty ? record.id : safeTitle}_${DateFormat('dd-MM-yyyy').format(record.date)}.pdf';",
    "final filename = 'FICHA_DDS_${safeTitle.isEmpty ? record.id : safeTitle}_${DateFormat('dd-MM-yyyy').format(record.date)}.pdf';",
    1,
)
listing = listing.replace(
    "title: Text('Gerar PDF / lista de presença'),",
    "title: Text('Retirar ficha do DDS'),",
    1,
)

card_marker = """                    Wrap(
                      spacing: 12,
                      runSpacing: 4,
                      children: [
                        _meta(Icons.calendar_today_outlined, DateFormat('dd/MM/yyyy').format(record.date)),
                        if (due != null)
                          _meta(Icons.event_outlined, '${_dueLabel(widget.type)} ${DateFormat('dd/MM/yyyy').format(due)}'),
                        if (record.priority.isNotEmpty)
                          _meta(Icons.flag_outlined, record.priority),
                      ],
                    ),
"""
card_new = card_marker + """                    if (record.type == 'DDS') ...[
                      const SizedBox(height: 10),
                      SizedBox(
                        width: double.infinity,
                        child: OutlinedButton.icon(
                          onPressed: () => _generateDdsPdf(record),
                          icon: const Icon(Icons.picture_as_pdf_outlined, size: 18),
                          label: const Text('Retirar ficha do DDS'),
                        ),
                      ),
                    ],
"""
if "label: const Text('Retirar ficha do DDS')" not in listing and card_marker in listing:
    listing = listing.replace(card_marker, card_new, 1)

state_marker = "  Map<String, String> sectorNames = {};\n"
state_extra = """
  int _ddsParticipantCount(SstRecord record) {
    final raw = record.payload['dds_participants'];
    final structured = raw is List ? raw.length : 0;
    if (structured > 0) return structured;
    final text = '${record.payload['participants'] ?? ''}'.trim();
    if (text.isEmpty) return 0;
    return text
        .split(RegExp(r'[\\r\\n]+'))
        .where((name) => name.trim().isNotEmpty)
        .length;
  }

  int get _ddsTotalParticipations => records
      .where((record) => record.type == 'DDS')
      .fold<int>(0, (total, record) => total + _ddsParticipantCount(record));

  Widget _ddsHistorySummary() {
    return Card(
      margin: const EdgeInsets.fromLTRB(12, 12, 12, 4),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            const Icon(Icons.history_rounded, color: AuditarBrand.greenDark),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Histórico permanente de DDS',
                    style: TextStyle(
                      color: AuditarBrand.navy,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '${records.length} DDS • $_ddsTotalParticipations participação(ões)',
                    style: const TextStyle(fontSize: 12, color: Colors.black54),
                  ),
                ],
              ),
            ),
            const Icon(Icons.cloud_done_outlined, color: AuditarBrand.greenDark),
          ],
        ),
      ),
    );
  }
"""
if 'Widget _ddsHistorySummary()' not in listing and state_marker in listing:
    listing = listing.replace(state_marker, state_marker + state_extra, 1)

old_list = """                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
                      itemCount: records.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 8),
                      itemBuilder: (_, index) => _card(records[index]),
                    ),
"""
new_list = """                  : ListView(
                      padding: const EdgeInsets.only(bottom: 90),
                      children: [
                        if (widget.type == 'DDS') _ddsHistorySummary(),
                        ...List.generate(records.length, (index) => Padding(
                              padding: EdgeInsets.fromLTRB(
                                12,
                                index == 0 && widget.type != 'DDS' ? 12 : 4,
                                12,
                                4,
                              ),
                              child: _card(records[index]),
                            )),
                      ],
                    ),
"""
if "if (widget.type == 'DDS') _ddsHistorySummary()" not in listing and old_list in listing:
    listing = listing.replace(old_list, new_list, 1)

hub = hub.replace(
    "_tool('DDS', 'DDS', 'Temas, participantes e histórico por empresa.', Icons.record_voice_over_outlined, AuditarBrand.greenDark),",
    "_tool('DDS', 'DDS', 'Histórico permanente por empresa, assinaturas e ficha em PDF.', Icons.record_voice_over_outlined, AuditarBrand.greenDark),",
    1,
)

# ---------------------------------------------------------------------------
# Fotos/assinaturas: retentativa própria sem bloquear dados estruturados.
# ---------------------------------------------------------------------------
post_pos = media.find('  static Future<Map<String, dynamic>> _post(')
if post_pos < 0:
    post_pos = media.find('  static Future<Map<String, Object?>> _post(')
if post_pos < 0:
    raise RuntimeError('Método _post da mídia não localizado')

retry_helper = r'''  static bool _isTransientMediaTransportError(Object error) {
    final text = error.toString().toLowerCase();
    return text.contains('socket') ||
        text.contains('clientexception') ||
        text.contains('timeout') ||
        text.contains('timed out') ||
        text.contains('failed host lookup') ||
        text.contains('script.google.com') ||
        text.contains('googleusercontent.com') ||
        text.contains('central online') ||
        text.contains('connection') ||
        text.contains('503') ||
        text.contains('502') ||
        text.contains('504') ||
        text.contains('429');
  }

  static String _safeFriendlyError(Object error) {
    if (_isTransientMediaTransportError(error)) {
      return 'Envio temporariamente pendente. O app tentará novamente automaticamente; fotos e assinaturas continuam salvas no computador.';
    }
    return _friendlyError(error);
  }

  static Future<Map<String, dynamic>> _postReliable(
    Map<String, Object?> payload,
  ) async {
    Object? lastError;
    for (var attempt = 0; attempt < 3; attempt++) {
      try {
        return await _post(payload);
      } catch (error) {
        lastError = error;
        if (!_isTransientMediaTransportError(error) || attempt == 2) rethrow;
        await Future<void>.delayed(
          Duration(milliseconds: attempt == 0 ? 350 : 900),
        );
      }
    }
    throw lastError ?? StateError('Falha temporária no envio da mídia.');
  }

'''
if '_postReliable(' not in media:
    media = media[:post_pos] + retry_helper + media[post_pos:]

media = media.replace('await _post(<String, Object?>{', 'await _postReliable(<String, Object?>{')
media = media.replace('lastError = _friendlyError(e);', 'lastError = _safeFriendlyError(e);')
old_catch = """      } catch (e) {
        lastError = _safeFriendlyError(e);
      }
"""
new_catch = """      } catch (e) {
        lastError = _safeFriendlyError(e);
        if (_isTransientMediaTransportError(e)) break;
      }
"""
media = media.replace(old_catch, new_catch)

# ---------------------------------------------------------------------------
# Gravação.
# ---------------------------------------------------------------------------
pubp.write_text(pub, encoding='utf-8', newline='\n')
syncp.write_text(sync, encoding='utf-8', newline='\n')
coordp.write_text(coord, encoding='utf-8', newline='\n')
listp.write_text(listing, encoding='utf-8', newline='\n')
hubp.write_text(hub, encoding='utf-8', newline='\n')
dbp.write_text(db, encoding='utf-8', newline='\n')
mediap.write_text(media, encoding='utf-8', newline='\n')

# Regressões mínimas da versão consolidada.
final_pub = pubp.read_text(encoding='utf-8')
final_sync = syncp.read_text(encoding='utf-8')
final_coord = coordp.read_text(encoding='utf-8')
final_list = listp.read_text(encoding='utf-8')
final_media = mediap.read_text(encoding='utf-8')
assert 'version: 3.30.1+188' in final_pub
assert "'limit': 500," in final_sync
assert 'Duration(seconds: 10)' in final_coord
assert 'Retirar ficha do DDS' in final_list
assert 'Histórico permanente de DDS' in final_list
assert 'FICHA_DDS_' in final_list
assert '_postReliable(' in final_media
assert 'continuam salvas no computador' in final_media
print('Windows v3.30.1: sync rápido + histórico DDS/ficha + mídia resiliente aplicados.')
