import 'dart:io';

import 'package:flutter/material.dart';

import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/ai_assistant_service.dart';

/// Campos normalizados da analise visual existente: sugestoes, nunca fatos.
class SstAccidentPhotoAiSuggestion {
  const SstAccidentPhotoAiSuggestion({
    required this.visual,
    required this.possibleRisk,
    required this.proposedAction,
  });

  final String visual;
  final String possibleRisk;
  final String proposedAction;

  static String _clean(Object? raw, {int max = 550}) {
    if (raw is! String) return '';
    final value = raw
        .replaceAll(RegExp(r'[\x00-\x08\x0B\x0C\x0E-\x1F]'), ' ')
        .trim();
    return value.length > max ? value.substring(0, max) : value;
  }

  factory SstAccidentPhotoAiSuggestion.fromResult(
      Map<String, dynamic> result) {
    final description = _clean(result['description']);
    final fallback = _clean(result['title']);
    return SstAccidentPhotoAiSuggestion(
      visual: description.isEmpty ? fallback : description,
      possibleRisk: _clean(result['possibleConsequence']),
      proposedAction: _clean(result['recommendation']),
    );
  }

  bool get hasVisual => visual.trim().isNotEmpty;

  String forEvidence(int photoCount) =>
      'Rascunho de leitura visual por IA - NAO CONFIRMADO. '
      'Quantidade de fotos analisadas: ' + photoCount.toString() +
      '. Descricao sugerida: ' + visual +
      '. Conferir no local e registrar a fonte antes de validar.';

  String forConditions() =>
      'Indicio visual a conferir, sem concluir causa do acidente: ' + visual +
      (possibleRisk.isEmpty ? '' :
        '. Possivel perigo/consequencia a avaliar: ' + possibleRisk) +
      '. A fotografia nao comprova o evento nem a causa.';

  String forActions() =>
      'Proposta da IA - NAO EXECUTADA e sujeita a revisao tecnica: ' +
      proposedAction +
      '. Definir responsavel, prazo e evidencia de eficacia.';
}

/// A IA so e chamada mediante uma acao de envio e confirmacao explicita.
/// As fotografias ja estao ligadas ao formulario, sem duplicar arquivos.
/// A sugestao nao e salva ate o tecnico revisar no editor do formulario.
class SstAccidentPhotoAiPanel extends StatefulWidget {
  const SstAccidentPhotoAiPanel({
    super.key,
    required this.company,
    required this.location,
    required this.activity,
    required this.photoPaths,
    required this.evidencePhotoCount,
    required this.enabled,
    required this.onAttachGallery,
    required this.onAttachCamera,
    required this.onReviewSuggestion,
  });

  final Company company;
  final String location;
  final String activity;
  final List<String> photoPaths;
  final int evidencePhotoCount;
  final bool enabled;
  final VoidCallback onAttachGallery;
  final VoidCallback onAttachCamera;
  final void Function(String questionId, String suggestion) onReviewSuggestion;

  @override
  State<SstAccidentPhotoAiPanel> createState() =>
      _SstAccidentPhotoAiPanelState();
}

class _SstAccidentPhotoAiPanelState extends State<SstAccidentPhotoAiPanel> {
  bool privacyAccepted = false;
  bool busy = false;
  String? error;
  SstAccidentPhotoAiSuggestion? suggestion;
  int photoCount = 0;
  int generation = 0;
  final Set<String> _selectedPaths = <String>{};

  /// Nenhuma foto é pré-selecionada para envio: escolha explícita do TST.
  List<String> get selectedPhotos =>
      widget.photoPaths.where((p) => p.trim().isNotEmpty &&
          _selectedPaths.contains(p)).toSet().take(2)
          .toList(growable: false);

  void _togglePhoto(String path, bool choose) {
    if (!authorized || busy) return;
    if (choose && !_selectedPaths.contains(path) &&
        _selectedPaths.length >= 2) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Selecione no máximo duas fotos por análise.'),
      ));
      return;
    }
    setState(() {
      if (choose) {
        _selectedPaths.add(path);
      } else {
        _selectedPaths.remove(path);
      }
      // Seleção nova sempre invalida consentimento e análise anteriores.
      generation++;
      privacyAccepted = false;
      suggestion = null;
      photoCount = 0;
      error = null;
    });
  }

  static String _identity(List<String> paths) => paths.join('|');

  @override
  void didUpdateWidget(covariant SstAccidentPhotoAiPanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (_identity(widget.photoPaths) != _identity(oldWidget.photoPaths) ||
        widget.company.id != oldWidget.company.id ||
        widget.evidencePhotoCount != oldWidget.evidencePhotoCount) {
      _selectedPaths.clear();
      generation++;
      privacyAccepted = false;
      suggestion = null;
      photoCount = 0;
      error = null;
      busy = false;
    }
  }

  bool get authorized =>
      widget.enabled && AuthService.canAccessCompany(widget.company.id);

  Future<void> _analyze() async {
    final photos = selectedPhotos;
    if (!authorized || busy || !privacyAccepted || photos.isEmpty) return;

    final account = AppDatabase.activeUserId.toString();
    final companyId = widget.company.id;
    final inputSignature = _identity(widget.photoPaths);
    final selectedSignature = _identity(photos);
    final accepted = await showDialog<bool>(
      context: context,
      builder: (dialog) => AlertDialog(
        title: const Text('Enviar fotos para análise com IA?'),
        content: const Text(
          'As fotos selecionadas e o nome da empresa serão enviados '
          'ao serviço de IA já utilizado pelo Auditar SST. '
          'Não envie rostos identificáveis, ferimentos, documentos, '
          'prontuários ou dados pessoais. Remova ou anonimize esses '
          'elementos antes de continuar. A análise exige internet e '
          'não comprova a causa do acidente.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialog, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialog, true),
            child: const Text('Confirmar envio'),
          ),
        ],
      ),
    );
    if (accepted != true || !mounted || !authorized ||
        _identity(widget.photoPaths) != inputSignature ||
        _identity(selectedPhotos) != selectedSignature ||
        account != AppDatabase.activeUserId.toString()) return;

    final currentGeneration = ++generation;
    setState(() {
      busy = true;
      error = null;
      suggestion = null;
      photoCount = 0;
    });

    try {
      for (final path in photos) {
        final file = File(path);
        if (!await file.exists() || await file.length() == 0) {
          throw StateError('Uma foto não está mais disponível.');
        }
      }
      if (!mounted || !authorized ||
          account != AppDatabase.activeUserId.toString() ||
          companyId != widget.company.id ||
          currentGeneration != generation) return;
      // Utiliza o serviço de análise fotográfica que ja existe no app.
      // O modo remoto atual é geral, não uma perícia de acidentes.
      final reply = await AiAssistantService.analyzeSafetyObservationPhoto(
        company: widget.company,
        observationKind: 'Acidente/incidente',
        sectorName: widget.location,
        location: widget.activity,
        photoPath: photos.first,
        secondPhotoPath: photos.length > 1 ? photos[1] : null,
        technicianContext:
            'APOIO A INVESTIGACAO DE ACIDENTE. Descreva somente as '
            'condicoes que realmente parecem visiveis nas fotos. '
            'Nao identifique pessoas nem infira lesao, culpa, nexo '
            'ou causa raiz. Indique apenas perigos aparentes e '
            'medidas a confirmar pelo TST. Se a imagem nao permitir '
            'uma observacao, nao invente.',
      );
      if (!mounted || !authorized ||
          account != AppDatabase.activeUserId.toString() ||
          companyId != widget.company.id ||
          currentGeneration != generation ||
          _identity(widget.photoPaths) != inputSignature ||
          _identity(selectedPhotos) != selectedSignature) return;

      if (!reply.success) {
        setState(() {
          error = reply.message.isEmpty
              ? 'A IA não conseguiu analisar as fotos. Nenhum dado foi alterado.'
              : reply.message;
        });
        return;
      }
      final parsed = SstAccidentPhotoAiSuggestion.fromResult(
        Map<String, dynamic>.from(reply.result),
      );
      if (!parsed.hasVisual) {
        setState(() {
          error = 'A resposta da IA não trouxe uma descrição visual '
              'verificável. Nenhuma sugestão foi aplicada.';
        });
        return;
      }
      setState(() {
        suggestion = parsed;
        photoCount = photos.length;
      });
    } catch (_) {
      if (mounted && currentGeneration == generation) {
        setState(() {
          error = 'Não foi possível analisar as fotos. Confira a conexão, '
              'as permissões e os arquivos. Nenhuma informação foi salva.';
        });
      }
    } finally {
      if (mounted && currentGeneration == generation) {
        setState(() => busy = false);
      }
    }
  }

  void _review(String questionId, String suggestionText) {
    if (!authorized || busy || suggestion == null) return;
    widget.onReviewSuggestion(questionId, suggestionText);
  }

  @override
  Widget build(BuildContext context) {
    final photos = selectedPhotos;
    final result = suggestion;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Icon(Icons.auto_awesome_outlined),
                const SizedBox(width: 8),
                Expanded(
                  child: Text('Analisar fotos do acidente com IA',
                      style: Theme.of(context).textTheme.titleMedium),
                ),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              'Anexe fotos do local aos campos de evidências ou condições. '
              'A IA descreve indícios visuais, mas você deve conferir tudo '
              'antes de usar no relatório.',
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                OutlinedButton.icon(
                  onPressed: authorized && !busy
                      ? widget.onAttachGallery : null,
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('Anexar fotos'),
                ),
                if (!Platform.isWindows)
                  OutlinedButton.icon(
                    onPressed: authorized && !busy
                        ? widget.onAttachCamera : null,
                    icon: const Icon(Icons.photo_camera_outlined),
                    label: const Text('Usar câmera'),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'Fotos úteis: 1) visão geral da área; 2) detalhe da '
              'proteção/equipamento; 3) acesso e entorno. Fotografe '
              'somente em condição segura, sem alterar a cena.',
              style: TextStyle(fontSize: 12),
            ),
            const SizedBox(height: 8),
            if (widget.photoPaths.isEmpty)
              const Text('Nenhuma foto anexada. Inclua ao menos uma.'),
            if (widget.photoPaths.isNotEmpty) ...[
              Text(
                'Escolha quais fotos enviar à IA: ' +
                    photos.length.toString() + ' de 2 selecionadas.',
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
              for (var index = 0; index < widget.photoPaths.length; index++)
                CheckboxListTile(
                  key: ValueKey('accident-photo-' + index.toString()),
                  contentPadding: EdgeInsets.zero,
                  controlAffinity: ListTileControlAffinity.leading,
                  title: Text(index < widget.evidencePhotoCount
                      ? 'Evidências - foto ' + (index + 1).toString()
                      : 'Condições - foto ' +
                          (index - widget.evidencePhotoCount + 1).toString()),
                  subtitle: const Text(
                    'Seleção individual para envio ao serviço de IA',
                  ),
                  secondary: Image.file(
                    File(widget.photoPaths[index]),
                    width: 72, height: 60, fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) =>
                        const Icon(Icons.broken_image_outlined),
                  ),
                  value: _selectedPaths.contains(widget.photoPaths[index]),
                  onChanged: authorized && !busy ? (value) =>
                      _togglePhoto(widget.photoPaths[index], value == true) : null,
                ),
            ],
            if (widget.photoPaths.isNotEmpty && photos.isEmpty)
              const Text('Selecione uma ou duas fotos para prosseguir.'),
            const SizedBox(height: 8),
            CheckboxListTile(
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              title: const Text('Conferi a privacidade das fotos'),
              subtitle: const Text(
                'Confirmo que não há pessoas identificáveis, ferimentos '
                'ou documentos pessoais nas imagens que serão enviadas.',
              ),
              value: privacyAccepted,
              onChanged: authorized && !busy && photos.isNotEmpty
                  ? (v) => setState(() => privacyAccepted = v == true)
                  : null,
            ),
            FilledButton.icon(
              onPressed: authorized && !busy && privacyAccepted &&
                      photos.isNotEmpty ? _analyze : null,
              icon: const Icon(Icons.auto_awesome),
              label: Text(busy ? 'Analisando...' : 'Analisar fotos com IA'),
            ),
            const SizedBox(height: 8),
            const Text(
              'A análise utiliza internet e o serviço de IA existente. '
              'O resultado fica apenas nesta tela até que você decida '
              'revisar uma sugestão. Nada é inserido automaticamente.',
              style: TextStyle(fontSize: 12),
            ),
            if (busy) const LinearProgressIndicator(),
            if (error != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(error!, style: TextStyle(
                    color: Theme.of(context).colorScheme.error)),
              ),
            if (result != null) ...[
              const Divider(),
              const Text('Leitura visual da IA — NÃO CONFIRMADA',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              const SizedBox(height: 5),
              Text(result.visual),
              if (result.possibleRisk.isNotEmpty) ...[
                const SizedBox(height: 8),
                const Text('Possível perigo ou consequência (hipótese):',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                Text(result.possibleRisk),
              ],
              if (result.proposedAction.isNotEmpty) ...[
                const SizedBox(height: 8),
                const Text('Medida sugerida, ainda não executada:',
                    style: TextStyle(fontWeight: FontWeight.bold)),
                Text(result.proposedAction),
              ],
              const SizedBox(height: 10),
              const Text(
                'O que confirmar? A proteção estava instalada? '
                'A situação era anterior ao evento? Quais documentos, '
                'depoimentos e registros sustentam a hipótese? '
                'Uma foto não comprova causa raiz.',
              ),
              const SizedBox(height: 10),
              OutlinedButton(
                onPressed: authorized && !busy ? () => _review(
                  'incident-03', result.forEvidence(photoCount)) : null,
                child: const Text('Revisar para o campo Evidências'),
              ),
              OutlinedButton(
                onPressed: authorized && !busy ? () => _review(
                  'incident-04', result.forConditions()) : null,
                child: const Text('Revisar para Condições do local'),
              ),
              if (result.proposedAction.isNotEmpty)
                OutlinedButton(
                  onPressed: authorized && !busy ? () => _review(
                    'incident-08', result.forActions()) : null,
                  child: const Text('Revisar para Plano de ação'),
                ),
              const Text(
                'As causas e os cinco porquês devem ser investigados '
                'manualmente com outras evidências.',
                style: TextStyle(fontSize: 12),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
