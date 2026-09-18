#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in {'android','windows'}:
    raise SystemExit('Uso: patch_internal_management_training_v32969_v3307.py <app> <android|windows>')

pubp = root/'pubspec.yaml'
screenp = root/'lib/screens/management_panel_screen.dart'

pub = pubp.read_text(encoding='utf-8')
screen = screenp.read_text(encoding='utf-8')

target = '3.29.69+211' if platform == 'android' else '3.30.7+194'
pub, n = re.subn(r'^version:\s*[^\n]+', 'version: '+target, pub, count=1, flags=re.M)
if n != 1:
    raise RuntimeError('Versão não localizada')

if "import 'training_records_screen.dart';" not in screen:
    marker = "import 'settings_screen.dart';\n"
    if marker not in screen:
        raise RuntimeError('Import settings não localizado')
    screen = screen.replace(marker, marker + "import 'training_records_screen.dart';\n", 1)

state_marker = "  int missingRequiredCount = 0;\n"
if "List<SstRecord> trainingRecords = [];" not in screen:
    if state_marker not in screen:
        raise RuntimeError('Estado do painel não localizado')
    screen = screen.replace(
        state_marker,
        state_marker + "  List<SstRecord> trainingRecords = [];\n",
        1,
    )

load_marker = """    final missingRequired =
        await db.getMissingRequiredTrainings(companyId: widget.company.id);
    final url =
"""
load_new = """    final missingRequired =
        await db.getMissingRequiredTrainings(companyId: widget.company.id);
    final loadedTrainingRecords = await db.getSstRecords(
      type: 'TREINAMENTO_SESSAO',
      companyId: widget.company.id,
    );
    final url =
"""
if "final loadedTrainingRecords = await db.getSstRecords(" not in screen:
    if load_marker not in screen:
        raise RuntimeError('Carga do painel não localizada')
    screen = screen.replace(load_marker, load_new, 1)

set_marker = """      missingRequiredCount = missingRequired.length;
      panelUrl = url;
"""
set_new = """      missingRequiredCount = missingRequired.length;
      trainingRecords = loadedTrainingRecords;
      panelUrl = url;
"""
if "trainingRecords = loadedTrainingRecords;" not in screen:
    if set_marker not in screen:
        raise RuntimeError('setState do painel não localizado')
    screen = screen.replace(set_marker, set_new, 1)

helpers_anchor = """  Future<void> _toggleAccess() async {
"""
helpers = r'''  List<Map<String, dynamic>> _trainingMapList(Object? raw) {
    if (raw is! List) return <Map<String, dynamic>>[];
    return raw
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  int _trainingSignedCount(SstRecord record) => _trainingMapList(
        record.payload['participants'],
      ).where((item) => '${item['status'] ?? ''}' == 'ASSINADO').length;

  int _trainingPhotoCount(SstRecord record) =>
      _trainingMapList(record.payload['photos']).length;

  int get _trainingTotalPhotos => trainingRecords.fold<int>(
        0,
        (total, record) => total + _trainingPhotoCount(record),
      );

  int get _trainingTotalSignatures => trainingRecords.fold<int>(
        0,
        (total, record) => total + _trainingSignedCount(record),
      );

  int get _trainingFinalizedCount => trainingRecords
      .where((record) => record.status.toUpperCase() == 'FINALIZADO')
      .length;

  Future<void> _openTrainingRecords() async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => TrainingRecordsScreen(
          companyId: widget.company.id,
        ),
      ),
    );
    await _load();
  }

  Future<void> _openTrainingRecord(SstRecord record) async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => TrainingRecordDetailScreen(
          company: widget.company,
          recordId: record.id,
        ),
      ),
    );
    await _load();
  }

  Widget _trainingRecordsCard() {
    final ordered = List<SstRecord>.from(trainingRecords)
      ..sort((a, b) => b.date.compareTo(a.date));
    final latest = ordered.take(4).toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                    color: AuditarBrand.green.withValues(alpha: .12),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.school_outlined,
                    color: AuditarBrand.greenDark,
                  ),
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Treinamentos realizados',
                        style: TextStyle(
                          color: AuditarBrand.navy,
                          fontSize: 16,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      SizedBox(height: 2),
                      Text(
                        'Fotos, participantes, assinaturas e ficha do treinamento.',
                        style: TextStyle(
                          fontSize: 12.2,
                          color: Colors.black54,
                        ),
                      ),
                    ],
                  ),
                ),
                TextButton(
                  onPressed: _openTrainingRecords,
                  child: const Text('Ver todos'),
                ),
              ],
            ),
            const SizedBox(height: 12),
            ResponsiveWrap(
              minItemWidth: 110,
              maxColumns: 4,
              children: [
                _trainingMetricMini(
                  'Realizados',
                  trainingRecords.length,
                  Icons.fact_check_outlined,
                ),
                _trainingMetricMini(
                  'Finalizados',
                  _trainingFinalizedCount,
                  Icons.verified_outlined,
                ),
                _trainingMetricMini(
                  'Fotos',
                  _trainingTotalPhotos,
                  Icons.photo_library_outlined,
                ),
                _trainingMetricMini(
                  'Assinaturas',
                  _trainingTotalSignatures,
                  Icons.draw_outlined,
                ),
              ],
            ),
            const SizedBox(height: 10),
            if (latest.isEmpty)
              InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: _openTrainingRecords,
                child: Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AuditarBrand.navy.withValues(alpha: .04),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: AuditarBrand.navy.withValues(alpha: .08),
                    ),
                  ),
                  child: const Row(
                    children: [
                      Icon(
                        Icons.add_photo_alternate_outlined,
                        color: AuditarBrand.navy,
                      ),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Nenhum treinamento realizado registrado ainda. Toque para cadastrar e guardar fotos e assinaturas.',
                          style: TextStyle(fontSize: 12.5),
                        ),
                      ),
                      Icon(Icons.chevron_right),
                    ],
                  ),
                ),
              )
            else
              ...latest.map((record) {
                final participants =
                    _trainingMapList(record.payload['participants']);
                final code = '${record.payload['code'] ?? ''}'.trim();
                final signed = _trainingSignedCount(record);
                final photoCount = _trainingPhotoCount(record);
                final finalized =
                    record.status.toUpperCase() == 'FINALIZADO';
                return Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(12),
                    onTap: () => _openTrainingRecord(record),
                    child: Container(
                      padding: const EdgeInsets.all(11),
                      decoration: BoxDecoration(
                        color: finalized
                            ? AuditarBrand.green.withValues(alpha: .06)
                            : AuditarBrand.navy.withValues(alpha: .035),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: finalized
                              ? AuditarBrand.green.withValues(alpha: .16)
                              : AuditarBrand.navy.withValues(alpha: .08),
                        ),
                      ),
                      child: Row(
                        children: [
                          CircleAvatar(
                            radius: 19,
                            backgroundColor: finalized
                                ? AuditarBrand.green.withValues(alpha: .13)
                                : const Color(0xFFFFF3D9),
                            child: Icon(
                              finalized
                                  ? Icons.verified_outlined
                                  : Icons.pending_actions_outlined,
                              color: finalized
                                  ? AuditarBrand.greenDark
                                  : const Color(0xFF9A6500),
                              size: 20,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  [
                                    if (code.isNotEmpty) code,
                                    record.title,
                                  ].join(' • '),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                                const SizedBox(height: 3),
                                Text(
                                  '${DateFormat('dd/MM/yyyy').format(record.date)}'
                                  ' • $signed/${participants.length} assinatura(s)'
                                  ' • $photoCount foto(s)',
                                  style: const TextStyle(
                                    fontSize: 11.8,
                                    color: Colors.black54,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const Icon(Icons.chevron_right),
                        ],
                      ),
                    ),
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _trainingMetricMini(
    String label,
    int value,
    IconData icon,
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
      decoration: BoxDecoration(
        color: AuditarBrand.navy.withValues(alpha: .035),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Icon(icon, size: 18, color: AuditarBrand.navy),
          const SizedBox(width: 7),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$value',
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w900,
                    color: AuditarBrand.navy,
                  ),
                ),
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 10.8,
                    color: Colors.black54,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

'''
if "Widget _trainingRecordsCard()" not in screen:
    if helpers_anchor not in screen:
        raise RuntimeError('Âncora dos helpers não localizada')
    screen = screen.replace(helpers_anchor, helpers + helpers_anchor, 1)

build_marker = """                  _managementAttentionCard(
                    openNcCount: openNcCount,
                    overdueActions: overdueActions,
                    expiredTrainings: expiredTrainings,
                    missingTrainings: missingRequiredCount,
                    criticalSectors: criticalSectorCount,
                  ),
                  const SizedBox(height: 12),
                  Card(
"""
build_new = """                  _managementAttentionCard(
                    openNcCount: openNcCount,
                    overdueActions: overdueActions,
                    expiredTrainings: expiredTrainings,
                    missingTrainings: missingRequiredCount,
                    criticalSectors: criticalSectorCount,
                  ),
                  const SizedBox(height: 12),
                  _trainingRecordsCard(),
                  const SizedBox(height: 12),
                  Card(
"""
if "_trainingRecordsCard()," not in screen:
    if build_marker not in screen:
        raise RuntimeError('Ponto de inserção do card não localizado')
    screen = screen.replace(build_marker, build_new, 1)

pubp.write_text(pub, encoding='utf-8', newline='\n')
screenp.write_text(screen, encoding='utf-8', newline='\n')

assert 'version: '+target in pubp.read_text(encoding='utf-8')
assert "type: 'TREINAMENTO_SESSAO'" in screen
assert 'Treinamentos realizados' in screen
assert 'Fotos, participantes, assinaturas e ficha do treinamento.' in screen
assert 'TrainingRecordDetailScreen(' in screen
assert 'TrainingRecordsScreen(' in screen
print('INTERNAL_MANAGEMENT_TRAINING_OK', target, platform)
