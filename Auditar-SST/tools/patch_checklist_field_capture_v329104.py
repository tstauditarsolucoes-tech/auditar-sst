#!/usr/bin/env python3
"""Local-first rapid photo+NC capture inside the current Checklist screen."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
src=root/'lib/screens/checklist_screen.dart'
policy=root/'lib/services/checklist_field_capture_policy.dart'
policy.write_text(Path('build_sources/v3.29.104-field-speed/checklist_field_capture_policy.dart').read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
s=src.read_text(encoding='utf-8')

def once(old,new,label):
    global s
    if s.count(old)!=1: raise RuntimeError(label+': '+str(s.count(old))+' matches')
    s=s.replace(old,new,1)

once("import '../services/ai_assistant_service.dart';",
     "import '../services/ai_assistant_service.dart';\nimport '../services/checklist_field_capture_policy.dart';",
     'policy import')
once("  String description;\n  String risk;",
     "  String description;\n  String aiTextOriginal;\n  String risk;",
     'extra original')
once("    this.description = '',\n    this.risk = '',",
     "    this.description = '',\n    this.aiTextOriginal = '',\n    this.risk = '',",
     'extra constructor')
once("        'description': description,\n        'risk': risk,",
     "        'description': description,\n        'aiTextOriginal': aiTextOriginal,\n        'risk': risk,",
     'extra toJson')
once("        description: '"+'$'+"{map['description'] ?? ''}',\n        risk:",
     "        description: '"+'$'+"{map['description'] ?? ''}',\n        aiTextOriginal: '"+'$'+"{map['aiTextOriginal'] ?? ''}',\n        risk:",
     'extra fromJson')
once("  Future<void> _saveDraft({bool showMessage = false}) async {",
     "  Future<void> _saveDraft({bool showMessage = false, Set<String>? onlyItems}) async {",
     'draft only item signature')
once("""    for (final item in widget.checklistItems) {
      final status = statuses[item.id] ?? '';
      final observation = observations[item.id]!.text.trim();""",
     """    for (final item in widget.checklistItems) {
      if (onlyItems != null && !onlyItems.contains(item.id)) continue;
      final status = statuses[item.id] ?? '';
      final observation = observations[item.id]!.text.trim();""",
     'draft item filter')

once("  final Set<String> rewritingTextItems = {};",
     """  final Set<String> rewritingTextItems = {};
  final TextEditingController _fastSearch = TextEditingController();
  final TextEditingController _fastDescription = TextEditingController();
  final List<String> _fastEvidence = <String>[];
  ChecklistItem? _fastSelected;
  String _fastPriority = 'Média';
  bool _fastOpen = false;
  bool _fastSaving = false;""", 'fast capture state')
once("""    _scrollController.dispose();
    super.dispose();""",
     """    _fastSearch.dispose();
    _fastDescription.dispose();
    _scrollController.dispose();
    super.dispose();""", 'fast dispose')

anchor="  Future<void> _takePhoto(String itemId) async {"
if s.count(anchor)!=1:raise RuntimeError('photo method anchor')
methods=r'''  Future<void> _fastPick(ImageSource source) async {
    if (_fastSaving || _fastEvidence.length >= 10) return;
    final image = await picker.pickImage(
      source: Platform.isWindows ? ImageSource.gallery : source,
      imageQuality: 75, maxWidth: 1800,
    );
    if (image == null) return;
    final stored = await StorageService.persistImage(
      image.path, folder: 'fotos_vistorias',
    );
    if (mounted) setState(() => _fastEvidence.add(stored));
  }

  Future<void> _fastImproveText(ChecklistItem item, String original,
      String? extraId) async {
    final reply = await AiAssistantService.improveInspectionText(
      companyName: widget.companyName,
      area: widget.inspection.area,
      observationKind: 'Não conforme',
      originalText: original,
    );
    if (!mounted) return;
    if (!reply.success) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(reply.message)));
      return;
    }
    final approved = await InspectionTextAiReview.show(
      context,
      original: original,
      suggested: (reply.result['description'] ?? '').toString(),
    );
    if (approved == null || !mounted) return;
    setState(() {
      if (extraId == null) {
        observations[item.id]!.text = approved;
        aiTextMeta[item.id] = <String,dynamic>{
          'source': 'TEXT_ONLY',
          'originalText': original,
          'revisedText': approved,
          'approvedAt': DateTime.now().toUtc().toIso8601String(),
        };
      } else {
        for (final extra in extraOccurrences[item.id] ?? <_ExtraNcOccurrence>[]) {
          if (extra.id == extraId) {
            extra.description = approved;
            extra.aiTextOriginal = original;
            break;
          }
        }
      }
    });
    await _saveDraft(onlyItems: {item.id});
  }

  Future<void> _saveFastCapture({required bool improveAfterSave}) async {
    if (_fastSaving || saving || loadingExisting) return;
    final item = _fastSelected;
    final original = _fastDescription.text.trim();
    if (item == null || original.isEmpty || _fastEvidence.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Selecione um item, descreva a NC e anexe uma foto.')));
      return;
    }
    final currentStatus = statuses[item.id];
    if (!ChecklistFieldCapturePolicy.canAddOccurrence(currentStatus)) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Item já respondido como $currentStatus; '
            'revise-o no checklist antes de registrar nova NC.')));
      return;
    }
    if (!ChecklistFieldCapturePolicy.acceptsEvidence(
        photos[item.id]?.length ?? 0, _fastEvidence.length)) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Limite de 10 fotos por item. '
            'Abra o item para revisar as fotos existentes.')));
      return;
    }
    setState(() => _fastSaving = true);
    String? extraId;
    try {
      // Wait for an earlier autosave; never treat an ignored save as success.
      while (draftSaving) {
        await Future<void>.delayed(const Duration(milliseconds: 60));
        if (!mounted) return;
      }
      draftSaveTimer?.cancel();
      final additional = ChecklistFieldCapturePolicy.isAdditionalOccurrence(
          statuses[item.id], observations[item.id]!.text);
      setState(() {
        statuses[item.id] = 'Não Conforme';
        photos[item.id]!.addAll(_fastEvidence);
        _markAiPhotoPending(item.id);
        if (additional) {
          extraId = const Uuid().v4();
          extraOccurrences[item.id]!.add(_ExtraNcOccurrence(
            id: extraId!, description: original, priority: _fastPriority));
        } else {
          observations[item.id]!.text = original;
          priorities[item.id] = _fastPriority;
        }
      });
      await _saveDraft(onlyItems: {item.id});
      if (!mounted) return;
      setState(() {
        _fastEvidence.clear();
        _fastDescription.clear();
      });
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('NC e foto salvas no aparelho. '
            'Registre a próxima ocorrência sem aguardar a IA.')));
      if (improveAfterSave) {
        unawaited(_fastImproveText(item, original, extraId));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Não foi possível confirmar o salvamento. '
              'O item continua no rascunho para nova tentativa.')));
      }
    } finally {
      if (mounted) setState(() => _fastSaving = false);
    }
  }

  Widget _fastCaptureCard() {
    final query = _fastSearch.text.trim().toLowerCase();
    final matches = widget.checklistItems.where((item) {
      final searchable = (item.text + ' ' + item.category + ' ' +
              item.reference).toLowerCase();
      return query.isEmpty || searchable.contains(query);
    }).take(7).toList();
    return Card(
      color: const Color(0xFFF2F8F4),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text('Captura rápida · foto + descrição manual',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
            const SizedBox(height: 5),
            const Text('Salve a NC primeiro. IA texto é opcional e '
                'não recebe a fotografia. Itens não vistoriados ficam sem resposta.'),
            const SizedBox(height: 10),
            TextField(
              controller: _fastSearch,
              onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(
                labelText: 'Pesquisar item do checklist',
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(),
              ),
            ),
            if (_fastSelected != null)
              ListTile(
                leading: const Icon(Icons.check_circle, color: Colors.green),
                title: Text(_fastSelected!.text,
                    maxLines: 2, overflow: TextOverflow.ellipsis),
                subtitle: const Text('Item selecionado'),
              ),
            SizedBox(
              height: matches.isEmpty ? 48 : 166,
              child: matches.isEmpty
                ? const Center(child: Text('Nenhum item encontrado.'))
                : ListView.builder(
                    itemCount: matches.length,
                    itemBuilder: (_, index) {
                      final item = matches[index];
                      final status = statuses[item.id];
                      final allowed =
                          ChecklistFieldCapturePolicy.canAddOccurrence(status);
                      return ListTile(
                        dense: true,
                        enabled: allowed && !_fastSaving,
                        title: Text(item.text, maxLines: 2,
                            overflow: TextOverflow.ellipsis),
                        subtitle: Text(status == 'Não Conforme'
                            ? 'Adicionar outra NC ao mesmo item'
                            : status == null ? item.category
                            : 'Já respondido: $status'),
                        trailing: _fastSelected?.id == item.id
                            ? const Icon(Icons.check) : null,
                        onTap: () => setState(() {
                          _fastSelected = item;
                          _fastPriority = item.priority;
                        }),
                      );
                    },
                  ),
            ),
            const SizedBox(height: 8),
            Wrap(spacing: 8, runSpacing: 6, children: [
              OutlinedButton.icon(
                onPressed: _fastSaving || _fastEvidence.length >= 10
                    ? null : () => _fastPick(ImageSource.camera),
                icon: const Icon(Icons.camera_alt_outlined),
                label: const Text('Tirar foto'),
              ),
              OutlinedButton.icon(
                onPressed: _fastSaving || _fastEvidence.length >= 10
                    ? null : () => _fastPick(ImageSource.gallery),
                icon: const Icon(Icons.photo_library_outlined),
                label: const Text('Galeria'),
              ),
              Chip(label: Text('Fotos: ' + _fastEvidence.length.toString())),
            ]),
            if (_fastEvidence.isNotEmpty)
              SizedBox(
                height: 88,
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  itemCount: _fastEvidence.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 7),
                  itemBuilder: (_, index) => Stack(children: [
                    Image.file(File(_fastEvidence[index]),
                        width: 86, height: 86, fit: BoxFit.cover),
                    Positioned(
                      right: 0, top: 0,
                      child: IconButton.filled(
                        visualDensity: VisualDensity.compact,
                        onPressed: _fastSaving ? null
                            : () => setState(
                                () => _fastEvidence.removeAt(index)),
                        icon: const Icon(Icons.close, size: 14),
                      ),
                    ),
                  ]),
                ),
              ),
            const SizedBox(height: 10),
            TextField(
              controller: _fastDescription,
              maxLines: 3,
              minLines: 2,
              decoration: const InputDecoration(
                labelText: 'O que você identificou?',
                hintText: 'Ex.: esteira sem proteção, equipamento em operação.',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _fastPriority,
              isExpanded: true,
              decoration: const InputDecoration(
                labelText: 'Prioridade informada pelo técnico',
                border: OutlineInputBorder(),
              ),
              items: const ['Baixa', 'Média', 'Alta', 'Crítica']
                  .map((value) => DropdownMenuItem(
                      value: value, child: Text(value)))
                  .toList(),
              onChanged: _fastSaving ? null : (value) {
                if (value != null) setState(() => _fastPriority = value);
              },
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: _fastSaving ? null
                  : () => _saveFastCapture(improveAfterSave: false),
              icon: _fastSaving
                  ? const SizedBox(width: 16, height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.save_outlined),
              label: Text(_fastSaving
                  ? 'Salvando no aparelho...' : 'Salvar e próxima ocorrência'),
            ),
            OutlinedButton.icon(
              onPressed: _fastSaving ? null
                  : () => _saveFastCapture(improveAfterSave: true),
              icon: const Icon(Icons.auto_awesome_outlined),
              label: const Text('Salvar e melhorar texto com IA'),
            ),
            const Text(
              'Para analisar a imagem, abra o item e escolha IA foto. '
              'O checklist completo continua exigindo as respostas antes de finalizar.',
              style: TextStyle(fontSize: 11, color: Colors.black54),
            ),
          ],
        ),
      ),
    );
  }

'''
s=s.replace(anchor,methods+anchor,1)

once("""          IconButton(
            tooltip: 'Salvar rascunho e sair',
            onPressed: saving || draftSaving ? null : _saveDraftAndExit,""",
     """          IconButton(
            tooltip: 'Captura rápida: foto e NC',
            onPressed: saving || draftSaving ? null
                : () => setState(() => _fastOpen = !_fastOpen),
            icon: const Icon(Icons.add_a_photo_outlined),
          ),
          IconButton(
            tooltip: 'Salvar rascunho e sair',
            onPressed: saving || draftSaving ? null : _saveDraftAndExit,""",
     'appbar entry')
once("""          Card(
            child: ListTile(
              leading: const Icon(Icons.cloud_done_outlined),
              title: const Text(
                'Rascunho automático ativo',""",
     """          Card(
            child: ListTile(
              leading: const Icon(Icons.add_a_photo_outlined),
              title: const Text('Captura rápida: foto + NC',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              subtitle: const Text(
                'Registre e salve somente as situações encontradas. '
                'A IA é opcional; nenhum item será marcado conforme automaticamente.',
              ),
              trailing: Icon(_fastOpen ? Icons.expand_less : Icons.expand_more),
              onTap: () => setState(() => _fastOpen = !_fastOpen),
            ),
          ),
          if (_fastOpen) _fastCaptureCard(),
          Card(
            child: ListTile(
              leading: const Icon(Icons.cloud_done_outlined),
              title: const Text(
                'Rascunho automático ativo',""",
     'list entry')

src.write_text(s,encoding='utf-8',newline='\n')
print('CHECKLIST_FIELD_CAPTURE_OK')
