import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:signature/signature.dart';

import '../database.dart';
import '../services/auth_service.dart';
import '../services/sst_document_signature_models.dart';

/// Captura uma rubrica visual e a guarda localmente para CIÊNCIA da minuta.
/// NÃO substitui o processo de certificação requerido para PET digital.
class SstDocumentSignaturePanel extends StatefulWidget {
  const SstDocumentSignaturePanel({
    super.key,
    required this.companyId,
    required this.userId,
    required this.documentKind,
    required this.documentId,
    required this.snapshot,
    required this.roles,
    required this.enabled,
  });
  final String companyId, userId, documentKind, documentId, snapshot;
  final Map<String, String> roles;
  final bool enabled;

  @override
  State<SstDocumentSignaturePanel> createState() =>
      _SstDocumentSignaturePanelState();
}

class _SstDocumentSignaturePanelState
    extends State<SstDocumentSignaturePanel> {
  final store = SstHandwrittenSignatureStore(
    read: AppDatabase.instance.getSetting,
    write: AppDatabase.instance.setSetting,
  );
  List<SstHandwrittenMark> marks = const [];
  bool busy = false;
  String? error;
  int generation = 0;

  bool get allowed => widget.enabled &&
      AppDatabase.activeUserId.toString() == widget.userId &&
      AuthService.canAccessCompany(widget.companyId);
  bool get canManage => allowed && !busy;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant SstDocumentSignaturePanel oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.snapshot != widget.snapshot ||
        oldWidget.documentId != widget.documentId ||
        oldWidget.userId != widget.userId ||
        oldWidget.documentKind != widget.documentKind ||
        oldWidget.companyId != widget.companyId) {
      marks = const [];
      error = null;
      _load();
    }
  }

  Future<void> _load() async {
    final generationAtStart = ++generation;
    if (!allowed) return;
    try {
      final result = await store.load(
        user: widget.userId,
        company: widget.companyId,
        kind: widget.documentKind,
        id: widget.documentId,
      );
      if (mounted && allowed && generation == generationAtStart) {
        setState(() { marks = result; error = null; });
      }
    } catch (_) {
      if (mounted && generation == generationAtStart) {
        setState(() {
          error = 'Não foi possível ler as assinaturas locais. '
              'Nenhuma assinatura anterior foi substituída.';
        });
      }
    }
  }

  Future<void> _sign(String roleCode, String roleLabel) async {
    if (!canManage || !widget.roles.containsKey(roleCode)) return;
    final snapshot = widget.snapshot;
    final docId = widget.documentId;
    final userId = widget.userId;
    final companyId = widget.companyId;
    final kind = widget.documentKind;

    final controller = SignatureController(
      penStrokeWidth: 3,
      penColor: Colors.black,
      exportBackgroundColor: Colors.white,
    );
    final name = TextEditingController();
    final job = TextEditingController();
    bool accepted = false;

    try {
      final confirmed = await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (dialog) => StatefulBuilder(
          builder: (dialog, refresh) => AlertDialog(
            title: Text('Assinatura de ciência: ' + roleLabel),
            content: SizedBox(width: 500, child: SingleChildScrollView(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const Text('Assine na tela com o dedo ou mouse. Esta '
                  'rubrica representa SOMENTE ciência/revisão da minuta. '
                  'Não verifica identidade, não é assinatura certificada '
                  'e NÃO autoriza PT/PET nem entrada em espaço confinado.'),
                const SizedBox(height: 10),
                TextField(
                  controller: name,
                  maxLength: 160,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: 'Nome completo do signatário',
                  ),
                  onChanged: (_) => refresh(() {}),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: job,
                  maxLength: 160,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    labelText: 'Função declarada',
                  ),
                  onChanged: (_) => refresh(() {}),
                ),
                const SizedBox(height: 8),
                Container(
                  height: 180,
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey),
                  ),
                  child: Signature(
                    controller: controller,
                    backgroundColor: Colors.white,
                  ),
                ),
                const SizedBox(height: 6),
                TextButton.icon(
                  onPressed: () {
                    controller.clear();
                    refresh(() {});
                  },
                  icon: const Icon(Icons.refresh),
                  label: const Text('Limpar traço'),
                ),
                CheckboxListTile(
                  title: const Text('Li e concordo com o registro de ciência'),
                  subtitle: const Text('O traço será salvo localmente e '
                    'incluído no PDF apenas enquanto o documento não mudar.'),
                  value: accepted,
                  onChanged: (v) => refresh(() => accepted = v == true),
                  controlAffinity: ListTileControlAffinity.leading,
                ),
              ]),
            )),
            actions: [
              TextButton(onPressed: () => Navigator.pop(dialog, false),
                child: const Text('Cancelar')),
              FilledButton(
                onPressed: !accepted || name.text.trim().isEmpty ||
                    job.text.trim().isEmpty ? null :
                    () => Navigator.pop(dialog, true),
                child: const Text('Registrar ciência'),
              ),
            ],
          ),
        ),
      );
      if (confirmed != true || !mounted || !canManage ||
          snapshot != widget.snapshot ||
          docId != widget.documentId ||
          userId != widget.userId ||
          companyId != widget.companyId ||
          kind != widget.documentKind ||
          controller.isEmpty) return;

      final png = await controller.toPngBytes();
      if (png == null || png.length < 100 || png.length > 170000) {
        throw const FormatException('Traço inválido ou muito grande');
      }
      if (!mounted || !canManage || snapshot != widget.snapshot ||
          userId != widget.userId || docId != widget.documentId) return;
      setState(() => busy = true);
      final mark = SstHandwrittenMark(
        roleCode: roleCode,
        roleLabel: roleLabel,
        declaredName: name.text.trim(),
        declaredFunction: job.text.trim(),
        signedAt: DateTime.now().toUtc().toIso8601String(),
        documentSnapshot: snapshot,
        pngBase64: base64Encode(png),
      );
      await store.save(
        user: userId, company: companyId,
        kind: kind, id: docId,
        mark: mark, allowedRoles: widget.roles.keys.toSet(),
      );
      if (mounted && allowed && snapshot == widget.snapshot) {
        await _load();
      }
    } catch (_) {
      if (mounted) setState(() {
        error = 'Não foi possível registrar a rubrica. '
            'Confira os dados e tente novamente.';
      });
    } finally {
      controller.dispose();
      name.dispose();
      job.dispose();
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final current = marks.where((m) => m.isCurrent(widget.snapshot)).toList();
    final stale = marks.length - current.length;
    return Card(child: Padding(
      padding: const EdgeInsets.all(14),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Icon(Icons.draw_outlined),
          const SizedBox(width: 8),
          Expanded(child: Text('Assinaturas na tela (ciência / revisão)',
            style: Theme.of(context).textTheme.titleMedium)),
        ]),
        const SizedBox(height: 6),
        const Text('Assine no celular ou computador. O nome e a função '
          'são declarados pelo usuário, sem verificação automática. '
          'As rubricas NÃO representam aprovação formal de PT/PET.'),
        const SizedBox(height: 8),
        for (final entry in widget.roles.entries) ...[
          const Divider(height: 10),
          Text(entry.value, style: const TextStyle(
            fontWeight: FontWeight.bold)),
          if (current.any((m) => m.roleCode == entry.key)) ...[
            for (final mark in current)
              if (mark.roleCode == entry.key) ...[
                Text(mark.declaredName + ' — ' + mark.declaredFunction),
                Text('Registrado em UTC: ' + mark.signedAt,
                  style: const TextStyle(fontSize: 12)),
                Image.memory(base64Decode(mark.pngBase64),
                  width: 210, height: 70, fit: BoxFit.contain),
              ],
          ] else const Text('Ainda não assinou esta versão.'),
          OutlinedButton.icon(
            onPressed: canManage ? () => _sign(entry.key, entry.value) : null,
            icon: const Icon(Icons.draw_outlined),
            label: Text(current.any((m) => m.roleCode == entry.key)
                ? 'Substituir rubrica' : 'Assinar ciência'),
          ),
        ],
        if (stale > 0)
          const Padding(
            padding: EdgeInsets.only(top: 8),
            child: Text('O documento foi alterado após uma assinatura. '
              'Rubricas anteriores estão desatualizadas, não entram '
              'no PDF atual. É necessário assinar novamente.',
              style: TextStyle(color: Colors.deepOrange)),
          ),
        if (busy) const LinearProgressIndicator(),
        if (error != null) Text(error!, style: TextStyle(
          color: Theme.of(context).colorScheme.error)),
        const Text('A assinatura manual fica apenas neste dispositivo. '
          'Não há certificação ICP-Brasil, trilha de auditoria confiável '
          'ou sincronização neste protótipo.',
          style: TextStyle(fontSize: 12)),
      ]),
    ));
  }
}
