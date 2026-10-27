#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')
pubp = root / 'pubspec.yaml'
aip = root / 'lib/services/ai_assistant_service.dart'
rondap = root / 'lib/screens/express_round_screen.dart'

pub = pubp.read_text(encoding='utf-8')
ai = aip.read_text(encoding='utf-8')
ronda = rondap.read_text(encoding='utf-8')


def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador ausente: {label}')
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, new_block: str, label: str) -> str:
    i = text.find(start)
    if i < 0:
        raise RuntimeError(f'Inicio ausente: {label}')
    j = text.find(end, i)
    if j < 0:
        raise RuntimeError(f'Fim ausente: {label}')
    return text[:i] + new_block.rstrip() + '\n\n' + text[j:]


pub = once(pub, 'version: 3.29.59+201', 'version: 3.29.60+202', 'versao v3.29.59')

# IA DE FOTO: usar diretamente a mesma rota comprovada do checklist e enviar
# uma copia compacta (o arquivo original da evidencia nunca e alterado).
new_photo_method = r'''  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({
    required Company company,
    required String observationKind,
    required String sectorName,
    required String location,
    required String photoPath,
    String technicianContext = '',
  }) async {
    if (photoPath.trim().isEmpty) {
      return const AiAssistantReply(
        success: false,
        message: 'Adicione uma foto antes de analisar.',
      );
    }

    try {
      final file = File(photoPath);
      if (!await file.exists()) {
        return const AiAssistantReply(
          success: false,
          message: 'A foto não está disponível neste aparelho. Aguarde a recuperação da mídia ou escolha a foto novamente.',
        );
      }

      // A evidência original permanece intacta. Para a IA enviamos somente uma
      // cópia compacta, reduzindo muito o tempo de upload no 4G/5G e no Apps Script.
      final bytes = _prepareRoundPhotoForAi(await file.readAsBytes());
      final image = 'data:image/jpeg;base64,${base64Encode(bytes)}';
      final area = [sectorName.trim(), location.trim()]
          .where((value) => value.isNotEmpty)
          .join(' • ');

      // Reaproveita exatamente a rota de imagem já usada pelo Checklist, que é
      // a rota de foto mais madura do Auditar. O contexto deixa claro se o
      // registro é conformidade ou não conformidade.
      final reply = await _send({
        'mode': 'checklist_photo',
        'companyName': company.name,
        'area': area.isEmpty ? 'Ronda Expressa' : area,
        'question': observationKind == 'Conformidade'
            ? 'Ronda Expressa: registrar uma conformidade ou boa prática observável na foto.'
            : 'Ronda Expressa: registrar uma não conformidade observável na foto.',
        'category': 'Ronda Expressa',
        'reference': '',
        'technicianContext': [
          technicianContext.trim(),
          if (observationKind == 'Conformidade')
            'Trate este registro como CONFORMIDADE/BOA PRÁTICA. Descreva somente aspectos positivos visíveis. Não invente risco ou irregularidade. A recomendação deve indicar como manter o padrão.'
          else
            'Trate este registro como NÃO CONFORMIDADE. Descreva somente o que for sustentado pela foto e pelo contexto do técnico. Sugira risco, recomendação e prioridade; referências normativas precisam ser conferidas pelo responsável técnico.',
        ].where((value) => value.isNotEmpty).join('\n'),
        'images': [image],
      });

      if (!reply.success) return reply;
      final normalized = Map<String, dynamic>.from(reply.result);
      normalized.putIfAbsent('title', () => '');
      normalized.putIfAbsent('possibleConsequence', () => '');
      normalized['aiImageBytes'] = bytes.length;
      return AiAssistantReply(
        success: true,
        message: 'Foto analisada. Revise a sugestão antes de usar no relatório.',
        result: normalized,
      );
    } catch (error) {
      return AiAssistantReply(
        success: false,
        message: 'Não foi possível preparar a foto para a IA: $error',
      );
    }
  }'''
ai = replace_between(
    ai,
    '  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({',
    '  static Future<AiAssistantReply> reviewExpressRound({',
    new_photo_method,
    'analyzeSafetyObservationPhoto',
)

compact_helper = r'''  static Uint8List _prepareRoundPhotoForAi(Uint8List originalBytes) {
    final decoded = img.decodeImage(originalBytes);
    if (decoded == null) {
      throw const FormatException('formato de imagem não reconhecido');
    }

    var prepared = img.bakeOrientation(decoded);
    const maxDimension = 720;
    if (prepared.width > maxDimension || prepared.height > maxDimension) {
      prepared = prepared.width >= prepared.height
          ? img.copyResize(prepared, width: maxDimension)
          : img.copyResize(prepared, height: maxDimension);
    }

    final sanitized = img.Image(
      width: prepared.width,
      height: prepared.height,
      numChannels: 3,
    );
    img.compositeImage(sanitized, prepared);

    var encoded = Uint8List.fromList(img.encodeJpg(sanitized, quality: 55));
    // Redes móveis e o Apps Script ficam muito mais estáveis com payload curto.
    // Se a imagem ainda for excepcionalmente grande, reduzimos só a cópia da IA.
    if (encoded.length > 650000) {
      final smaller = prepared.width >= prepared.height
          ? img.copyResize(sanitized, width: 600)
          : img.copyResize(sanitized, height: 600);
      encoded = Uint8List.fromList(img.encodeJpg(smaller, quality: 48));
    }
    return encoded;
  }

'''
ai = once(
    ai,
    '  static Uint8List _prepareImage(Uint8List originalBytes) {\n',
    compact_helper + '  static Uint8List _prepareImage(Uint8List originalBytes) {\n',
    'helper de foto compacta da Ronda',
)

# RONDA: IA deixa de ser parte do caminho de campo. O registro e salvo primeiro
# e pode ser enriquecido depois de tocar em Finalizar.
ronda = once(
    ronda,
    '  bool analyzingWithAi = false;\n  bool reviewingRoundWithAi = false;\n',
    '  bool analyzingWithAi = false;\n  bool analyzingRoundPhotos = false;\n  bool reviewingRoundWithAi = false;\n',
    'estado lote IA da ronda',
)

ronda = once(
    ronda,
    "          'aiAssisted': aiTitle.isNotEmpty || aiRecommendation.isNotEmpty,\n          'photoPath': photoPath,\n",
    "          'aiAssisted': aiTitle.isNotEmpty || aiRecommendation.isNotEmpty,\n          'aiStatus': photoPath.isEmpty\n              ? 'SEM_FOTO'\n              : (aiTitle.isNotEmpty || aiRecommendation.isNotEmpty)\n                  ? 'CONCLUIDA'\n                  : 'PENDENTE',\n          'aiLastError': '',\n          'aiAnalyzedAt': (aiTitle.isNotEmpty || aiRecommendation.isNotEmpty)\n              ? now.toIso8601String()\n              : '',\n          'photoPath': photoPath,\n",
    'status IA persistente no registro',
)

batch_methods = r'''  bool _recordIsConformity(SstRecord record) =>
      '${record.payload['observationKind'] ?? ''}' == 'Conformidade' ||
      '${record.payload['findingType'] ?? ''}' == 'CONFORMIDADE';

  bool _recordNeedsPhotoAi(SstRecord record) {
    final path = '${record.payload['photoPath'] ?? ''}'.trim();
    return path.isNotEmpty && record.payload['aiAssisted'] != true;
  }

  int get _pendingPhotoAiCount =>
      roundRecords.where(_recordNeedsPhotoAi).length;

  bool _isNetworkLikeAiFailure(String message) {
    final value = message.toLowerCase();
    return value.contains('temporariamente') ||
        value.contains('comunica') ||
        value.contains('conex') ||
        value.contains('internet') ||
        value.contains('demor') ||
        value.contains('timeout') ||
        value.contains('google');
  }

  String _recordTechnicianContext(SstRecord record) {
    final payload = record.payload;
    final categories = (payload['categories'] as List? ?? const [])
        .map((value) => '$value'.trim())
        .where((value) => value.isNotEmpty)
        .join(', ');
    return <String>[
      'Registro feito durante Ronda Expressa.',
      'Tipo: ${_recordIsConformity(record) ? 'Conformidade' : 'Não conformidade'}.',
      if (categories.isNotEmpty) 'Categorias: $categories.',
      if ('${payload['description'] ?? ''}'.trim().isNotEmpty)
        'Anotação do técnico: ${payload['description']}.',
      'A foto é evidência de campo. Não invente elemento que não esteja visível ou informado.',
    ].join('\n');
  }

  Future<void> _analyzePendingRoundPhotos() async {
    if (analyzingRoundPhotos) return;
    final pending = roundRecords.where(_recordNeedsPhotoAi).toList();
    if (pending.isEmpty) {
      _message('Não há fotos pendentes de análise nesta ronda.');
      return;
    }

    setState(() => analyzingRoundPhotos = true);
    if (mounted) {
      // ignore: discarded_futures
      showDialog<void>(
        context: context,
        barrierDismissible: false,
        builder: (_) => const AlertDialog(
          title: Row(
            children: [
              SizedBox(
                width: 22,
                height: 22,
                child: CircularProgressIndicator(strokeWidth: 2.4),
              ),
              SizedBox(width: 12),
              Expanded(child: Text('IA analisando a ronda')),
            ],
          ),
          content: Text(
            'As fotos já estão salvas. A IA está analisando um registro por vez; isso não altera nem atrasa a coleta de campo.',
          ),
        ),
      );
    }

    var completed = 0;
    var failed = 0;
    var stoppedByNetwork = false;
    try {
      for (final record in pending) {
        final original = Map<String, dynamic>.from(record.payload);
        final path = '${original['photoPath'] ?? ''}'.trim();
        if (path.isEmpty || !File(path).existsSync()) {
          failed += 1;
          continue;
        }

        final conformity = _recordIsConformity(record);
        final reply = await AiAssistantService.analyzeSafetyObservationPhoto(
          company: widget.company,
          observationKind: conformity ? 'Conformidade' : 'Condição insegura',
          sectorName: '${original['sectorName'] ?? ''}',
          location: '${original['location'] ?? ''}',
          photoPath: path,
          technicianContext: _recordTechnicianContext(record),
        );
        final now = DateTime.now();

        if (!reply.success) {
          failed += 1;
          final failedPayload = Map<String, dynamic>.from(original)
            ..['aiStatus'] = 'ERRO'
            ..['aiLastError'] = reply.message
            ..['updatedAt'] = now.toIso8601String();
          await AppDatabase.instance.upsertSstRecord(
            SstRecord(
              id: record.id,
              companyId: record.companyId,
              sectorId: record.sectorId,
              type: record.type,
              title: record.title,
              date: record.date,
              status: record.status,
              priority: record.priority,
              payload: failedPayload,
            ),
          );
          if (_isNetworkLikeAiFailure(reply.message)) {
            stoppedByNetwork = true;
            break;
          }
          continue;
        }

        final result = reply.result;
        String text(String key) => '${result[key] ?? ''}'.trim();
        List<String> list(String key) => (result[key] as List? ?? const [])
            .map((value) => '$value'.trim())
            .where((value) => value.isNotEmpty)
            .toList();
        final descriptionAi = text('description');
        final recommendation = <String>[
          text('recommendation'),
          text('correctiveAction'),
        ].where((value) => value.isNotEmpty).join('\n');
        final suggestedPriority = text('priority');
        final nextPriority = conformity
            ? 'Baixa'
            : const ['Baixa', 'Média', 'Alta', 'Crítica'].contains(suggestedPriority)
                ? suggestedPriority
                : record.priority;
        final nextPayload = Map<String, dynamic>.from(original)
          ..['description'] = descriptionAi.isNotEmpty
              ? descriptionAi
              : '${original['description'] ?? ''}'
          ..['risk'] = conformity ? '' : text('risk')
          ..['possibleConsequence'] = conformity
              ? ''
              : text('possibleConsequence')
          ..['recommendation'] = recommendation
          ..['immediateAction'] = conformity ? '' : text('immediateAction')
          ..['responsible'] = conformity ? '' : text('responsibleProfile')
          ..['likelyReferences'] = list('likelyReferences')
          ..['checksRequired'] = list('checksRequired')
          ..['aiConfidence'] = text('confidence')
          ..['aiAssisted'] = true
          ..['aiStatus'] = 'CONCLUIDA'
          ..['aiLastError'] = ''
          ..['aiAnalyzedAt'] = now.toIso8601String()
          ..['updatedAt'] = now.toIso8601String();

        await AppDatabase.instance.upsertSstRecord(
          SstRecord(
            id: record.id,
            companyId: record.companyId,
            sectorId: record.sectorId,
            type: record.type,
            title: record.title,
            date: record.date,
            status: record.status,
            priority: nextPriority,
            payload: nextPayload,
          ),
        );
        completed += 1;
      }
    } finally {
      await _reloadRoundRecords();
      if (mounted) {
        setState(() => analyzingRoundPhotos = false);
        Navigator.of(context, rootNavigator: true).pop();
      }
    }

    if (!mounted) return;
    if (stoppedByNetwork) {
      _message(
        'IA interrompida por instabilidade de rede/Google. $completed análise(s) ficaram salvas e o restante continua pendente para tentar depois.',
      );
    } else if (failed > 0) {
      _message(
        'IA concluiu $completed registro(s). $failed ficaram pendentes/indisponíveis e podem ser tentados novamente.',
      );
    } else {
      _message('IA concluiu a análise de $completed registro(s) da ronda.');
    }
  }

'''
ronda = once(
    ronda,
    '  Future<void> _showRoundHistory() async {\n',
    batch_methods + '  Future<void> _showRoundHistory() async {\n',
    'metodos de analise posterior da ronda',
)

ronda = once(
    ronda,
    "                    final path = '${record.payload['photoPath'] ?? ''}';\n                    return Card(\n",
    "                    final path = '${record.payload['photoPath'] ?? ''}';\n                    final aiStatus = '${record.payload['aiStatus'] ?? ''}';\n                    return Card(\n",
    'status IA no historico',
)
ronda = once(
    ronda,
    "                        subtitle: Text('$kind • ${record.priority}'),\n",
    "                        subtitle: Text(\n                          '$kind • ${record.priority}'\n                          '${path.isNotEmpty ? ' • IA: ${aiStatus.isEmpty ? 'Pendente' : aiStatus.toLowerCase()}' : ''}',\n                        ),\n",
    'legenda IA no historico',
)

ronda = once(
    ronda,
    "                  _summaryChip('Setores', _sectorCount, AuditarBrand.navy),\n",
    "                  _summaryChip('Setores', _sectorCount, AuditarBrand.navy),\n                  if (_pendingPhotoAiCount > 0)\n                    _summaryChip('IA pendente', _pendingPhotoAiCount, const Color(0xFF6A4BBC)),\n",
    'chip IA pendente',
)

post_round_ai = r'''              if (_pendingPhotoAiCount > 0) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFF4F0FF),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    'A ronda de campo está salva. Há $_pendingPhotoAiCount foto(s) aguardando IA. Você pode analisar agora, depois de finalizar a coleta, sem atrasar a caminhada.',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                ),
                const SizedBox(height: 8),
                FilledButton.icon(
                  onPressed: analyzingRoundPhotos
                      ? null
                      : () async {
                          Navigator.pop(sheetContext);
                          await _analyzePendingRoundPhotos();
                          if (mounted) await _finish();
                        },
                  icon: const Icon(Icons.auto_awesome_rounded),
                  label: Text(
                    'Analisar $_pendingPhotoAiCount registro(s) com IA',
                  ),
                ),
                const SizedBox(height: 8),
              ],
'''
ronda = once(
    ronda,
    "              const SizedBox(height: 4),\n              FilledButton.icon(\n                onPressed: reviewingRoundWithAi ? null : () async {\n",
    "              const SizedBox(height: 4),\n" + post_round_ai + "              FilledButton.icon(\n                onPressed: reviewingRoundWithAi ? null : () async {\n",
    'botao pos-ronda para IA de fotos',
)

ronda = once(
    ronda,
    "                    label: Text(analyzingWithAi ? 'Analisando...' : 'Analisar foto com IA'),\n",
    "                    label: Text(\n                      analyzingWithAi\n                          ? 'Analisando...'\n                          : 'Analisar agora com IA (opcional)',\n                    ),\n",
    'rotulo IA opcional',
)
ronda = once(
    ronda,
    "                TextButton.icon(\n                  onPressed: () => setState(() {\n",
    "                const Padding(\n                  padding: EdgeInsets.fromLTRB(4, 4, 4, 0),\n                  child: Text(\n                    'Você também pode salvar agora e analisar todas as fotos com IA somente ao finalizar a ronda.',\n                    textAlign: TextAlign.center,\n                    style: TextStyle(fontSize: 11.5, color: Colors.black54),\n                  ),\n                ),\n                TextButton.icon(\n                  onPressed: () => setState(() {\n",
    'aviso IA posterior',
)

for path, text in [(pubp, pub), (aip, ai), (rondap, ronda)]:
    path.write_text(text, encoding='utf-8', newline='\n')

assert 'version: 3.29.60+202' in pub
assert "'mode': 'checklist_photo'" in ai
assert '_prepareRoundPhotoForAi' in ai
assert 'const maxDimension = 720' in ai
assert 'quality: 55' in ai
assert 'analyzingRoundPhotos' in ronda
assert "'aiStatus': photoPath.isEmpty" in ronda
assert '_analyzePendingRoundPhotos' in ronda
assert '_pendingPhotoAiCount' in ronda
assert 'Analisar agora com IA (opcional)' in ronda
assert 'somente ao finalizar a ronda' in ronda
assert 'Analisar $_pendingPhotoAiCount registro(s) com IA' in ronda
print('Android v3.29.60+202: Ronda salva primeiro, IA pos-campo e foto compacta pela rota do checklist.')
