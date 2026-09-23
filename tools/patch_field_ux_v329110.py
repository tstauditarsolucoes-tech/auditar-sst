#!/usr/bin/env python3
"""Targeted field UX fixes: DDS selection/signing, audit timeout, logo recovery."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
def edit(rel,fn):
    p=root/rel; old=p.read_text(encoding='utf-8'); new=fn(old)
    p.write_text(new,encoding='utf-8',newline='\n')
def rep(s,a,b,label):
    n=s.count(a)
    if n!=1: raise RuntimeError(f'{label}: expected one match, got {n}')
    return s.replace(a,b,1)

def dds_picker(s):
    s=rep(s,"""          return AlertDialog(
            title: const Text('Participantes do DDS'),
            content: SizedBox(
              width: 620,
              height: 580,""","""          return AlertDialog(
            insetPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            title: const Text('Participantes do DDS'),
            contentPadding: const EdgeInsets.fromLTRB(14, 12, 14, 6),
            content: SizedBox(
              width: (MediaQuery.sizeOf(context).width - 70)
                  .clamp(240.0, 620.0).toDouble(),
              height: (MediaQuery.sizeOf(context).height * .56)
                  .clamp(240.0, 580.0).toDouble(),""",'dds dialog sizing')
    s=rep(s,"""                    autofocus: true,
                    onChanged: (value) =>
                        setDialogState(() => query = value),""","""                    autofocus: false,
                    onChanged: (value) =>
                        setDialogState(() => query = value),""",'keyboard does not crush picker')
    start=s.index("                  Row(\n                    children: [\n                      Expanded(\n                        child: Text(\n                          '$totalVisible participante(s) encontrado(s)',")
    end=s.index("                  SizedBox(\n                    width: double.infinity,\n                    child: FilledButton.tonalIcon(",start)
    old=s[start:end]
    new="""                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '$totalVisible participante(s) encontrado(s)',
                        style: const TextStyle(fontSize: 12, color: Colors.black54),
                      ),
                      Align(
                        alignment: Alignment.centerRight,
                        child: Wrap(
                          spacing: 4,
                          runSpacing: 0,
                          children: [
                            TextButton(
                              onPressed: () => setDialogState(() {
                                chosenWorkers.addAll(
                                  visibleWorkers.map((worker) => worker.id),
                                );
                                chosenPreAdmissions.addAll(
                                  visiblePreAdmissions.map((row) => row.id),
                                );
                              }),
                              child: const Text('Selecionar exibidos'),
                            ),
                            TextButton(
                              onPressed: () => setDialogState(() {
                                chosenWorkers.clear();
                                chosenPreAdmissions.clear();
                              }),
                              child: const Text('Limpar'),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
"""
    if 'chosenWorkers.addAll' not in old:raise RuntimeError('dds picker block changed')
    s=s[:start]+new+s[end:]
    s=rep(s,"builder: (_) => DdsSignatureCaptureScreen(initialName: initialName),",
          "builder: (_) => DdsSignatureCaptureScreen(initialName: initialName),",
          'preserve selected participant') if False else s
    return s
edit('lib/screens/sst_record_form_screen.dart',dds_picker)

def dds_signature(s):
    s=rep(s,"""          builder: (_) => _DdsFullSignatureCanvas(
            controller: signatureController,
          ),""","""          builder: (_) => _DdsFullSignatureCanvas(
            controller: signatureController,
            participantName: nameController.text.trim(),
          ),""",'fullscreen chosen name')
    s=rep(s,"""          TextField(
            controller: nameController,
            textCapitalization: TextCapitalization.words,
            decoration: const InputDecoration(
              labelText: 'Nome do participante *',
              prefixIcon: Icon(Icons.person_outline),
            ),
          ),""","""          if (widget.initialName.trim().isNotEmpty)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 15, vertical: 14),
              decoration: BoxDecoration(
                color: AuditarBrand.navySoft,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AuditarBrand.navy.withValues(alpha: .16)),
              ),
              child: Column(children: [
                const Text('ASSINANDO AGORA', style: TextStyle(
                  fontSize: 12, fontWeight: FontWeight.w900,
                  color: AuditarBrand.greenDark, letterSpacing: 1)),
                const SizedBox(height: 5),
                Text(widget.initialName.trim().toUpperCase(),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 20,
                    fontWeight: FontWeight.w900, color: AuditarBrand.navy)),
              ]),
            )
          else
            TextField(
              controller: nameController,
              textCapitalization: TextCapitalization.words,
              decoration: const InputDecoration(
                labelText: 'Nome do participante *',
                prefixIcon: Icon(Icons.person_outline),
              ),
            ),""",'DDS participant fixed header')
    s=rep(s,"""class _DdsFullSignatureCanvas extends StatelessWidget {
  final SignatureController controller;

  const _DdsFullSignatureCanvas({required this.controller});""","""class _DdsFullSignatureCanvas extends StatelessWidget {
  final SignatureController controller;
  final String participantName;

  const _DdsFullSignatureCanvas({
    required this.controller,
    required this.participantName,
  });""",'DDS full signature name')
    s=rep(s,"""        title: const Text('Assinar em tela cheia'),
        actions: [""","""        title: Text(
          participantName.isEmpty ? 'Assinar em tela cheia'
            : 'ASSINANDO AGORA: $participantName',
          maxLines: 1, overflow: TextOverflow.ellipsis,
        ),
        actions: [""",'DDS fullscreen title')
    s=rep(s,"""          onPressed: () => Navigator.pop(context),
          icon: const Icon(Icons.check),""","""          onPressed: () {
            if (controller.isEmpty) {
              ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Assine antes de concluir.')));
              return;
            }
            Navigator.pop(context);
          },
          icon: const Icon(Icons.check),""",'DDS empty signature guard')
    return s
edit('lib/screens/dds_signature_capture_screen.dart',dds_signature)

def audit_screen(s):
    s="import 'dart:async';\n\n"+s if "import 'dart:async';" not in s else s
    s=rep(s,"""final result = await AuditService.listCompany(widget.company.id);""",
      """final result = await AuditService.listCompany(widget.company.id)
          .timeout(const Duration(seconds: 18));""",'audit timeout')
    s=rep(s,"""        error = e.toString().replaceFirst('Bad state: ', '');""",
      """        error = e is TimeoutException
            ? 'A consulta demorou demais. Confira a internet e tente novamente.'
            : e.toString().replaceFirst('Bad state: ', '');""",'audit readable error')
    return s
edit('lib/screens/audit_trail_screen.dart',audit_screen)

def companies(s):
    s=rep(s,"  bool loading = true;\n","  bool loading = true;\n  bool recoveringLogos = false;\n",'logo state')
    anchor='  Future<void> _editCompany([Company? company]) async {'
    method="""  Future<void> _recoverCompanyLogos() async {
    if (recoveringLogos) return;
    setState(() => recoveringLogos = true);
    try {
      final recovered = await MediaSyncService.restoreCompanyLogos(
        companyIds: companies.map((company) => company.id),
      ).timeout(const Duration(seconds: 55));
      if (recovered > 0) await _load();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(
        recovered > 0
          ? '$recovered logo(s) recuperada(s) do backup.'
          : 'Nenhuma logo disponível no backup da Central. Os cadastros foram preservados.',
      )));
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:
        Text('Não foi possível consultar as logos agora. Tente novamente mais tarde.')));
    } finally {
      if (mounted) setState(() => recoveringLogos = false);
    }
  }

"""
    s=rep(s,anchor,method+anchor,'manual logo action')
    s=rep(s,"""        actions: [
          IconButton(
            tooltip: 'Nova empresa',""","""        actions: [
          IconButton(
            tooltip: 'Recuperar logos do backup',
            onPressed: recoveringLogos ? null : _recoverCompanyLogos,
            icon: const Icon(Icons.cloud_download_outlined),
          ),
          IconButton(
            tooltip: 'Nova empresa',""",'logo recovery entry')
    return s
edit('lib/screens/companies_screen.dart',companies)
print('DDS_PICKER_SIGNATURE_AUDIT_LOGO_UI_OK',platform)
