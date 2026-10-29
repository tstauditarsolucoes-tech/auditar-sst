#!/usr/bin/env python3
"""Auditar SST v3.29.148 / v3.30.67

Refinamento aditivo do histórico de treinamentos:
- busca por título, código, instrutor, local e participante;
- filtros Todos / Em andamento / Finalizados / Assinaturas pendentes;
- nenhuma tabela nova;
- não altera sync, banco, autenticação, mídia, Drive, IA ou Apps Script.
"""
from pathlib import Path
import hashlib
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: patch_training_history_filters_v329148_v33067.py "
        "<APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
if platform not in ("android", "windows"):
    raise SystemExit("plataforma invalida")


def read(rel):
    return (root / rel).read_text(encoding="utf-8")


def write(rel, value):
    (root / rel).write_text(value, encoding="utf-8", newline="\n")


def once(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)


protected = [
    "lib/database.dart",
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

rel = "lib/screens/training_records_screen.dart"
s = read(rel)

s = once(
    s,
    "  List<SstRecord> preAdmissions = <SstRecord>[];\n",
    """  List<SstRecord> preAdmissions = <SstRecord>[];
  String _historyQuery = '';
  String _historyFilter = 'Todos';

  static const List<String> _historyFilters = <String>[
    'Todos',
    'Em andamento',
    'Finalizados',
    'Assinaturas pendentes',
  ];
""",
    "campos filtro historico",
)

anchor = """  Future<void> _open(SstRecord record) async {
    final current = company;
    if (current == null) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder:
            (_) => TrainingRecordDetailScreen(
              company: current,
              recordId: record.id,
            ),
      ),
    );
    await _load();
  }

"""
helper = """  Future<void> _open(SstRecord record) async {
    final current = company;
    if (current == null) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder:
            (_) => TrainingRecordDetailScreen(
              company: current,
              recordId: record.id,
            ),
      ),
    );
    await _load();
  }

  List<SstRecord> get _visibleHistoryRecords {
    final query = _historyQuery.trim().toLowerCase();
    return records.where((record) {
      final participants = _mapList(record.payload['participants']);
      final finalized = record.status.toUpperCase() == 'FINALIZADO';
      final pendingSignatures = participants.any(
        (item) => '${item['status'] ?? 'PENDENTE'}'.toUpperCase() != 'ASSINADO',
      );

      if (_historyFilter == 'Em andamento' && finalized) return false;
      if (_historyFilter == 'Finalizados' && !finalized) return false;
      if (_historyFilter == 'Assinaturas pendentes' && !pendingSignatures) {
        return false;
      }
      if (query.isEmpty) return true;

      final participantNames = participants
          .map(
            (item) =>
                '${item['name'] ?? item['workerName'] ?? item['participantName'] ?? ''}',
          )
          .join(' ');
      final searchable = <String>[
        record.title,
        '${record.payload['code'] ?? ''}',
        '${record.payload['instructor'] ?? ''}',
        '${record.payload['instructorName'] ?? ''}',
        '${record.payload['location'] ?? record.payload['local'] ?? ''}',
        participantNames,
      ].join(' ').toLowerCase();
      return searchable.contains(query);
    }).toList(growable: false);
  }

"""
s = once(s, anchor, helper, "helper filtro historico")

s = once(
    s,
    """  Widget build(BuildContext context) {
    final current = company;
    return Scaffold(
""",
    """  Widget build(BuildContext context) {
    final current = company;
    final visibleRecords = _visibleHistoryRecords;
    return Scaffold(
""",
    "visible records build",
)

s = once(
    s,
    """            const SizedBox(height: 12),
            if (loading)
""",
    """            const SizedBox(height: 12),
            if (!loading && records.isNotEmpty) ...[
              TextField(
                onChanged: (value) => setState(() => _historyQuery = value),
                decoration: InputDecoration(
                  labelText: 'Pesquisar treinamento ou participante',
                  hintText: 'Nome, código, instrutor, local ou colaborador',
                  prefixIcon: const Icon(Icons.search_rounded),
                  suffixIcon: _historyQuery.trim().isEmpty
                      ? null
                      : IconButton(
                          tooltip: 'Limpar pesquisa',
                          onPressed: () => setState(() => _historyQuery = ''),
                          icon: const Icon(Icons.close_rounded),
                        ),
                ),
              ),
              const SizedBox(height: 9),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                child: Row(
                  children: _historyFilters
                      .map(
                        (value) => Padding(
                          padding: const EdgeInsets.only(right: 7),
                          child: ChoiceChip(
                            label: Text(value),
                            selected: _historyFilter == value,
                            onSelected: (_) =>
                                setState(() => _historyFilter = value),
                          ),
                        ),
                      )
                      .toList(growable: false),
                ),
              ),
              const SizedBox(height: 7),
              Text(
                '${visibleRecords.length} de ${records.length} treinamento(s) exibido(s)',
                style: const TextStyle(
                  fontSize: 11.5,
                  color: AuditarBrand.neutral,
                ),
              ),
              const SizedBox(height: 7),
            ],
            if (loading)
""",
    "controles pesquisa",
)

s = once(
    s,
    """              const SizedBox(height: 8),
              ...records.map((record) {
""",
    """              const SizedBox(height: 8),
              if (visibleRecords.isEmpty)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(18),
                    child: Text(
                      'Nenhum treinamento corresponde à pesquisa ou ao filtro selecionado.',
                    ),
                  ),
                ),
              ...visibleRecords.map((record) {
""",
    "lista filtrada",
)

write(rel, s)

central_rel = "lib/screens/field_intelligence_center_screen.dart"
central = read(central_rel)
central = once(
    central,
    "    final version = Platform.isWindows ? '3.30.66' : '3.29.147';",
    "    final version = Platform.isWindows ? '3.30.67' : '3.29.148';",
    "versao diagnostico",
)
write(central_rel, central)

pub_rel = "pubspec.yaml"
pub = read(pub_rel)
old_release, new_release = (
    ("3.29.147+289", "3.29.148+290")
    if platform == "android"
    else ("3.30.66+253", "3.30.67+254")
)
marker = "version: " + old_release
if pub.count(marker) != 1:
    raise RuntimeError("versao esperada ausente: " + old_release)
pub = pub.replace(marker, "version: " + new_release, 1)
write(pub_rel, pub)

changed = [
    name
    for name, digest in before.items()
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest
]
if changed:
    raise SystemExit("PROTECTED_CORE_MODIFIED: " + repr(changed))

screen = read(rel)
for marker in [
    "Pesquisar treinamento ou participante",
    "Assinaturas pendentes",
    "_visibleHistoryRecords",
    "visibleRecords.length",
]:
    if marker not in screen:
        raise RuntimeError("marcador ausente: " + marker)

print("TRAINING_HISTORY_FILTERS_OK", platform, new_release)
print("SYNC_DB_AUTH_MEDIA_AI_DRIVE_GS_BYTE_IDENTICAL_OK")
