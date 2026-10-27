#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
listp = root / 'lib/screens/sst_records_screen.dart'
hubp = root / 'lib/screens/routine_hub_screen.dart'
dbp = root / 'lib/database.dart'
mediap = root / 'lib/services/media_sync_service.dart'

pub = pubp.read_text(encoding='utf-8')
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

# Versão.
if 'version: 3.29.53+195' not in pub:
    pub = once(pub, 'version: 3.29.52+194', 'version: 3.29.53+195', 'versão 3.29.52')

# Histórico DDS: título explícito e mais recente primeiro.
listing = listing.replace(
    "return ('DDS', Icons.record_voice_over_outlined);",
    "return ('Histórico de DDS', Icons.record_voice_over_outlined);",
    1,
)

old_order = "      orderBy: 'COALESCE(due_date, date) ASC, date DESC',\n"
new_order = "      orderBy: type == 'DDS' ? 'date DESC' : 'COALESCE(due_date, date) ASC, date DESC',\n"
if new_order not in db:
    db = once(db, old_order, new_order, 'ordenação dos registros SST')

# A ficha do DDS fica diretamente acessível no histórico, sem depender do menu de três pontos.
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
if "label: const Text('Retirar ficha do DDS')" not in listing:
    listing = once(listing, card_marker, card_new, 'botão Retirar ficha')

# Resumo permanente do histórico: quantidade de DDS e participações registradas.
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
if 'Widget _ddsHistorySummary()' not in listing:
    listing = once(listing, state_marker, state_marker + state_extra, 'resumo histórico DDS')

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
if 'if (widget.type == \'DDS\') _ddsHistorySummary()' not in listing:
    listing = once(listing, old_list, new_list, 'lista com resumo DDS')

hub = hub.replace(
    "_tool('DDS', 'DDS', 'Temas, participantes e histórico por empresa.', Icons.record_voice_over_outlined, AuditarBrand.greenDark),",
    "_tool('DDS', 'DDS', 'Histórico permanente por empresa, assinaturas e ficha em PDF.', Icons.record_voice_over_outlined, AuditarBrand.greenDark),",
    1,
)

# Mídia: fotos/assinaturas recebem retentativa própria sem bloquear o sync estruturado.
# O AppsScriptHttp já possui redirect + IPv4/DNS; aqui adicionamos retentativa curta
# específica da mídia para oscilações de rede observadas no Android.
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
      return 'Envio temporariamente pendente. O app tentará novamente automaticamente; fotos e assinaturas continuam salvas no aparelho.';
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

# Quando a rede está indisponível, não tenta dezenas de arquivos seguidos.
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

pubp.write_text(pub, encoding='utf-8', newline='\n')
listp.write_text(listing, encoding='utf-8', newline='\n')
hubp.write_text(hub, encoding='utf-8', newline='\n')
dbp.write_text(db, encoding='utf-8', newline='\n')
mediap.write_text(media, encoding='utf-8', newline='\n')

# Regressões essenciais.
assert 'version: 3.29.53+195' in pubp.read_text(encoding='utf-8')
ll = listp.read_text(encoding='utf-8')
mm = mediap.read_text(encoding='utf-8')
dd = dbp.read_text(encoding='utf-8')
assert 'Histórico de DDS' in ll
assert "Retirar ficha do DDS" in ll
assert 'Histórico permanente de DDS' in ll
assert 'FICHA_DDS_' in ll
assert "type == 'DDS' ? 'date DESC'" in dd
assert '_postReliable(' in mm
assert 'O app tentará novamente automaticamente' in mm
assert 'await _postReliable(<String, Object?>{' in mm
print('v3.29.53 aplicada: histórico DDS + ficha PDF + retentativa resiliente de fotos/assinaturas.')
