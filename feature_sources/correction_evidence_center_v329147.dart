import 'dart:io';

import 'package:flutter/material.dart';

import '../brand.dart';
import '../database.dart';
import '../models.dart';
import '../services/correction_recurrence_detector.dart';
import 'action_plan_screen.dart';
import 'evidence_backup_screen.dart';
import 'non_conformities_screen.dart';

class CorrectionEvidenceCenterScreen extends StatefulWidget {
  final Company company;

  const CorrectionEvidenceCenterScreen({
    super.key,
    required this.company,
  });

  @override
  State<CorrectionEvidenceCenterScreen> createState() =>
      _CorrectionEvidenceCenterScreenState();
}

class _CorrectionEvidenceCenterScreenState
    extends State<CorrectionEvidenceCenterScreen> {
  bool loading = true;
  String error = '';
  String filter = 'Todos';
  List<_CorrectionItem> items = const [];
  List<CorrectionRecurrenceGroup> recurrenceGroups = const [];

  static const filters = <String>[
    'Todos',
    'Antes + depois',
    'Aguardando correção',
    'Sem foto inicial',
  ];

  String _value(Map<String, Object?>? row, String key) =>
      '${row?[key] ?? ''}'.trim();

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() {
        loading = true;
        error = '';
      });
    }
    try {
      final db = AppDatabase.instance;
      final ncs = await db.getNonConformityRows(
        companyId: widget.company.id,
        includeClosed: true,
      );
      final actions = await db.getPendingActions(
        companyId: widget.company.id,
        includeCompleted: true,
      );
      final loaded = <_CorrectionItem>[];

      for (final nc in ncs) {
        final ncId = _value(nc, 'id');
        final answerId = _value(nc, 'answer_id');
        final related = actions
            .where(
              (action) =>
                  _value(action, 'nc_id') == ncId ||
                  (answerId.isNotEmpty &&
                      _value(action, 'answer_id') == answerId),
            )
            .toList(growable: false);

        final before = <String>[];
        if (answerId.isNotEmpty) {
          try {
            final photos = await db.getPhotosForAnswer(answerId);
            before.addAll(
              photos
                  .map((photo) => photo.path.trim())
                  .where((path) => path.isNotEmpty),
            );
          } catch (_) {}
        }

        final after = <String>[];
        for (final action in related) {
          final actionId = _value(action, 'id');
          if (actionId.isEmpty) continue;
          try {
            final photos = await db.getCompletionPhotos(actionId);
            after.addAll(
              photos
                  .map((photo) => photo.path.trim())
                  .where((path) => path.isNotEmpty),
            );
          } catch (_) {}
        }

        loaded.add(
          _CorrectionItem(
            nc: nc,
            action: related.isEmpty ? null : related.first,
            beforePaths: before,
            afterPaths: after,
          ),
        );
      }

      if (!mounted) return;
      setState(() {
        items = loaded;
        recurrenceGroups = CorrectionRecurrenceDetector.detect(ncs);
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loading = false;
        error = '$e';
      });
    }
  }

  List<_CorrectionItem> get visibleItems {
    switch (filter) {
      case 'Antes + depois':
        return items.where((item) => item.hasBeforeAfter).toList();
      case 'Aguardando correção':
        return items
            .where(
              (item) =>
                  item.beforePaths.isNotEmpty && item.afterPaths.isEmpty,
            )
            .toList();
      case 'Sem foto inicial':
        return items.where((item) => item.beforePaths.isEmpty).toList();
      default:
        return items;
    }
  }

  Future<void> _open(Widget page) async {
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => page));
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    final complete = items.where((item) => item.hasBeforeAfter).length;
    final awaiting = items
        .where(
          (item) => item.beforePaths.isNotEmpty && item.afterPaths.isEmpty,
        )
        .length;
    final noBefore = items.where((item) => item.beforePaths.isEmpty).length;

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: AuditarBrand.background,
        appBar: AppBar(
          title: const Text('Evidências e recorrências'),
          actions: [
            IconButton(
              tooltip: 'Proteção e backup das fotos',
              onPressed: loading
                  ? null
                  : () => _open(
                        EvidenceBackupScreen(company: widget.company),
                      ),
              icon: const Icon(Icons.cloud_done_outlined),
            ),
            IconButton(
              tooltip: 'Atualizar',
              onPressed: loading ? null : _load,
              icon: const Icon(Icons.refresh_rounded),
            ),
          ],
          bottom: const TabBar(
            tabs: [
              Tab(icon: Icon(Icons.compare_outlined), text: 'Antes × Depois'),
              Tab(icon: Icon(Icons.repeat_rounded), text: 'Recorrências'),
            ],
          ),
        ),
        body: loading
            ? const Center(child: CircularProgressIndicator())
            : error.isNotEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(
                        'Não foi possível montar esta visão: $error',
                      ),
                    ),
                  )
                : TabBarView(
                    children: [
                      _correctionsTab(
                        complete: complete,
                        awaiting: awaiting,
                        noBefore: noBefore,
                      ),
                      _recurrencesTab(),
                    ],
                  ),
      ),
    );
  }

  Widget _correctionsTab({
    required int complete,
    required int awaiting,
    required int noBefore,
  }) {
    final rows = visibleItems;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(14, 14, 14, 30),
        children: [
          _header(
            'Evidência de correção',
            'O app reúne as fotos já vinculadas à constatação e à conclusão da ação. Nenhuma foto é duplicada.',
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _metric('NCs', items.length, Icons.warning_amber_rounded),
              _metric('Antes + depois', complete, Icons.compare_outlined),
              _metric(
                'Aguardando depois',
                awaiting,
                Icons.pending_actions_outlined,
              ),
              _metric('Sem foto inicial', noBefore, Icons.hide_image_outlined),
            ],
          ),
          const SizedBox(height: 12),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: filters
                  .map(
                    (value) => Padding(
                      padding: const EdgeInsets.only(right: 7),
                      child: ChoiceChip(
                        label: Text(value),
                        selected: filter == value,
                        onSelected: (_) => setState(() => filter = value),
                      ),
                    ),
                  )
                  .toList(),
            ),
          ),
          const SizedBox(height: 10),
          if (rows.isEmpty)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(18),
                child: Text('Nenhum registro encontrado neste filtro.'),
              ),
            )
          else
            ...rows.map(_correctionCard),
        ],
      ),
    );
  }

  Widget _correctionCard(_CorrectionItem item) {
    final description = _value(item.nc, 'description');
    final code = _value(item.nc, 'code');
    final sector = CorrectionRecurrenceDetector.sectorOf(item.nc);
    final ncStatus = _value(item.nc, 'status');
    final action = _value(item.action, 'corrective_action');
    final actionStatus = _value(item.action, 'status');
    final note = _value(item.action, 'completion_note');
    final beforePath =
        item.beforePaths.isEmpty ? '' : item.beforePaths.first;
    final afterPath = item.afterPaths.isEmpty ? '' : item.afterPaths.first;

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(
                  Icons.health_and_safety_outlined,
                  color: AuditarBrand.navy,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    code.isEmpty ? 'Não conformidade' : code,
                    style: const TextStyle(
                      fontWeight: FontWeight.w900,
                      fontSize: 15,
                    ),
                  ),
                ),
                _stageChip(item.evidenceStage),
              ],
            ),
            if (description.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                description,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
            ],
            if (sector.isNotEmpty || ncStatus.isNotEmpty) ...[
              const SizedBox(height: 5),
              Text(
                [
                  if (sector.isNotEmpty) sector,
                  if (ncStatus.isNotEmpty) ncStatus,
                ].join(' • '),
                style: const TextStyle(
                  fontSize: 12,
                  color: AuditarBrand.neutral,
                ),
              ),
            ],
            if (action.isNotEmpty) ...[
              const SizedBox(height: 9),
              Text('Ação: $action'),
              if (actionStatus.isNotEmpty)
                Text(
                  'Situação da ação: $actionStatus',
                  style: const TextStyle(fontSize: 12),
                ),
            ],
            const SizedBox(height: 10),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _photoBox(
                  label: 'ANTES',
                  path: beforePath,
                  count: item.beforePaths.length,
                  emptyText: 'Sem foto da constatação',
                ),
                const SizedBox(width: 8),
                _photoBox(
                  label: 'DEPOIS',
                  path: afterPath,
                  count: item.afterPaths.length,
                  emptyText: 'Aguardando foto da correção',
                ),
              ],
            ),
            if (note.isNotEmpty) ...[
              const SizedBox(height: 9),
              Text(
                'Registro da execução: $note',
                style: const TextStyle(fontSize: 12),
              ),
            ],
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () => _open(
                  ActionPlanScreen(companyId: widget.company.id),
                ),
                icon: const Icon(Icons.open_in_new_rounded, size: 18),
                label: const Text('Abrir plano de ação'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _recurrencesTab() => RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(14, 14, 14, 30),
          children: [
            _header(
              'Possíveis recorrências',
              'Leitura automática e conservadora: compara descrições semelhantes dentro do mesmo setor. Serve como alerta para revisão do TST, não como conclusão definitiva.',
            ),
            const SizedBox(height: 10),
            _metric(
              'Grupos encontrados',
              recurrenceGroups.length,
              Icons.repeat_rounded,
            ),
            const SizedBox(height: 12),
            if (recurrenceGroups.isEmpty)
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(18),
                  child: Text(
                    'Nenhuma possível recorrência foi identificada com os critérios atuais.',
                  ),
                ),
              )
            else
              ...recurrenceGroups.map(_recurrenceCard),
          ],
        ),
      );

  Widget _recurrenceCard(CorrectionRecurrenceGroup group) {
    final first = group.records.first;
    final example = _value(first, 'description');
    final codes = group.records
        .map((row) {
          final code = _value(row, 'code');
          return code.isEmpty ? _value(row, 'id') : code;
        })
        .where((value) => value.isNotEmpty)
        .take(6)
        .join(' • ');

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const CircleAvatar(
                  backgroundColor: AuditarBrand.greenSoft,
                  foregroundColor: AuditarBrand.greenDark,
                  child: Icon(Icons.repeat_rounded),
                ),
                const SizedBox(width: 9),
                Expanded(
                  child: Text(
                    group.sector.isEmpty
                        ? 'Setor não informado'
                        : group.sector,
                    style: const TextStyle(
                      fontWeight: FontWeight.w900,
                      fontSize: 15,
                    ),
                  ),
                ),
                Text(
                  '${group.count} registros',
                  style: const TextStyle(fontWeight: FontWeight.w800),
                ),
              ],
            ),
            const SizedBox(height: 9),
            if (example.isNotEmpty)
              Text(
                example,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            if (codes.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                codes,
                style: const TextStyle(
                  fontSize: 11.5,
                  color: AuditarBrand.neutral,
                ),
              ),
            ],
            const SizedBox(height: 5),
            const Text(
              'Revisar causa, medida corretiva e eficácia para verificar se o problema reapareceu.',
              style: TextStyle(fontSize: 12),
            ),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () => _open(
                  NonConformitiesScreen(companyId: widget.company.id),
                ),
                icon: const Icon(Icons.list_alt_rounded, size: 18),
                label: const Text('Revisar NCs'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _photoBox({
    required String label,
    required String path,
    required int count,
    required String emptyText,
  }) {
    final exists = path.isNotEmpty && File(path).existsSync();
    return Expanded(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            count > 1 ? '$label • $count fotos' : label,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 5),
          Container(
            height: 135,
            width: double.infinity,
            decoration: BoxDecoration(
              color: Colors.black.withValues(alpha: .04),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.black12),
            ),
            clipBehavior: Clip.antiAlias,
            child: exists
                ? Image.file(
                    File(path),
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => _photoPlaceholder(
                      'Foto vinculada, mas não disponível neste aparelho',
                    ),
                  )
                : _photoPlaceholder(
                    path.isEmpty
                        ? emptyText
                        : 'Foto vinculada, mas não disponível neste aparelho',
                  ),
          ),
        ],
      ),
    );
  }

  Widget _photoPlaceholder(String text) => Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.image_not_supported_outlined,
              color: Colors.black45,
            ),
            const SizedBox(height: 5),
            Text(
              text,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 10.5,
                color: Colors.black54,
              ),
            ),
          ],
        ),
      );

  Widget _header(String title, String subtitle) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            subtitle,
            style: const TextStyle(color: AuditarBrand.neutral),
          ),
        ],
      );

  Widget _metric(String label, int value, IconData icon) => SizedBox(
        width: MediaQuery.sizeOf(context).width < 600 ? 165 : 205,
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Icon(icon, color: AuditarBrand.navy),
                const SizedBox(width: 8),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '$value',
                        style: const TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      Text(
                        label,
                        style: const TextStyle(
                          fontSize: 10.5,
                          color: AuditarBrand.neutral,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      );

  Widget _stageChip(String label) {
    final color = switch (label) {
      'Antes + depois' => AuditarBrand.greenDark,
      'Aguardando correção' => const Color(0xFFAD6409),
      _ => Colors.blueGrey,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: color.withValues(alpha: .10),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 10.5,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}

class _CorrectionItem {
  final Map<String, Object?> nc;
  final Map<String, Object?>? action;
  final List<String> beforePaths;
  final List<String> afterPaths;

  const _CorrectionItem({
    required this.nc,
    required this.action,
    required this.beforePaths,
    required this.afterPaths,
  });

  bool get hasBeforeAfter =>
      beforePaths.isNotEmpty && afterPaths.isNotEmpty;

  String get evidenceStage {
    if (hasBeforeAfter) return 'Antes + depois';
    if (beforePaths.isNotEmpty) return 'Aguardando correção';
    return 'Sem foto inicial';
  }
}
