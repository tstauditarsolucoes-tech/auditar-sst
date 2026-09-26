#!/usr/bin/env python3
"""DDS/training opt-in batch signatures; screen-only; no sync schema GS changes."""
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1]);dds=root/'lib/screens/sst_record_form_screen.dart';train=root/'lib/screens/training_records_screen.dart'
protected=['lib/database.dart','lib/services/device_sync_service.dart','lib/services/sync_coordinator.dart','lib/services/media_sync_service.dart','lib/services/drive_service.dart','lib/services/apps_script_http.dart','lib/services/ai_assistant_service.dart','painel_web_google_apps_script/Code.gs','painel_web_google_apps_script/MultiUser.gs','painel_web_google_apps_script/ClientPortal.gs']
before={x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in protected}
def once(s,old,new,label):
 n=s.count(old)
 if n!=1:raise RuntimeError(label+' expected exactly once: '+str(n))
 return s.replace(old,new,1)
d=dds.read_text(encoding='utf-8')
d=once(d,'  bool restoringDdsSignatures = false;','  bool restoringDdsSignatures = false;\n  bool _ddsSignatureQueueRunning = false;','dds state')
dds_method=r'''  /// Operator opt-in. Cancel or failed registration stops before the next person.
  Future<void> _signDdsPendingInSequence() async {
    if (_ddsSignatureQueueRunning) return;
    if (selectedCompanyId == null || selectedCompanyId!.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Selecione a empresa antes de iniciar.')));
      return;
    }
    setState(() => _ddsSignatureQueueRunning = true);
    try {
      while (mounted) {
        final signed = ddsSignatures.map((item) =>
            (item['name'] ?? '').toString().trim().toLowerCase())
            .where((name) => name.isNotEmpty).toSet();
        final pending = _ddsParticipantNames().where(
            (name) => !signed.contains(name.toLowerCase())).toList();
        if (pending.isEmpty) break;
        final expected = pending.first.toLowerCase();
        await _collectDdsSignature();
        if (!mounted) return;
        final after = ddsSignatures.map((item) =>
            (item['name'] ?? '').toString().trim().toLowerCase()).toSet();
        if (!after.contains(expected)) break;
      }
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Coleta encerrada. Confira os participantes pendentes.')));
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Coleta interrompida: $error')));
    } finally {
      if (mounted) setState(() => _ddsSignatureQueueRunning = false);
    }
  }

'''
d=once(d,'  Future<void> _collectDdsFacial([Map<String, dynamic>? current]) async {',dds_method+'  Future<void> _collectDdsFacial([Map<String, dynamic>? current]) async {','dds method')
d=once(d,"                    onPressed: _collectDdsSignature,\n                    icon: const Icon(Icons.draw_outlined),\n                    label: const Text('Assinar na tela'),","                    onPressed: _ddsSignatureQueueRunning ? null : _collectDdsSignature,\n                    icon: const Icon(Icons.draw_outlined),\n                    label: const Text('Assinar na tela'),",'dds manual')
d=once(d,'            if (ddsSignatures.isEmpty) ...[',r'''            if (missing.isNotEmpty) ...[
              const SizedBox(height: 9),
              SizedBox(width: double.infinity, child: FilledButton.icon(
                onPressed: _ddsSignatureQueueRunning ? null : _signDdsPendingInSequence,
                icon: _ddsSignatureQueueRunning
                    ? const SizedBox(width: 16,height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.groups_2_outlined),
                label: Text(_ddsSignatureQueueRunning
                    ? 'Coleta em andamento...'
                    : 'Assinar pendentes em sequência (' + missing.length.toString() + ')'),
              )),
              const Text('Cada assinatura é registrada antes do próximo. '
                  'Voltar ou cancelar interrompe a sequência.',
                  style: TextStyle(fontSize: 11.5,color: Colors.black54)),
            ],
            if (ddsSignatures.isEmpty) ...[''','dds UI')
t=train.read_text(encoding='utf-8')
t=once(t,'  bool busy = false;\n  SstRecord? record;','  bool busy = false;\n  bool _trainingSignatureQueueRunning = false;\n  SstRecord? record;','train state')
train_method=r'''  /// Does not change confirmed/facial, paper-sheet or absent participants.
  Future<void> _signPendingTrainingInSequence() async {
    if (_trainingSignatureQueueRunning || busy || finalized) return;
    setState(() => _trainingSignatureQueueRunning = true);
    try {
      final queue = participants.where((person) =>
          (person['status'] ?? 'PENDENTE').toString() == 'PENDENTE')
          .map((person) => (person['id'] ?? '').toString())
          .where((id) => id.isNotEmpty).toList();
      for (final id in queue) {
        if (!mounted || finalized) return;
        Map<String, dynamic>? current;
        for (final person in participants) {
          if ((person['id'] ?? '').toString() == id) {current = person;break;}
        }
        if (current == null ||
            (current['status'] ?? '').toString() != 'PENDENTE') continue;
        await _sign(current);
        if (!mounted) return;
        Map<String, dynamic>? after;
        for (final person in participants) {
          if ((person['id'] ?? '').toString() == id) {after = person;break;}
        }
        if (after == null ||
            (after['status'] ?? '').toString() != 'ASSINADO') break;
      }
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Coleta encerrada. Confira os participantes pendentes.')));
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Coleta interrompida: $error')));
    } finally {
      if (mounted) setState(() => _trainingSignatureQueueRunning = false);
    }
  }

'''
t=once(t,'  Future<void> _face(Map<String, dynamic> participant) async {',train_method+'  Future<void> _face(Map<String, dynamic> participant) async {','train method')
t=once(t,'            ...participants.map((participant) {',r'''            if (!finalized && pending > 0) ...[
              SizedBox(width: double.infinity,child: FilledButton.icon(
                onPressed: busy || _trainingSignatureQueueRunning
                    ? null : _signPendingTrainingInSequence,
                icon: _trainingSignatureQueueRunning
                    ? const SizedBox(width: 16,height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.groups_2_outlined),
                label: Text(_trainingSignatureQueueRunning
                    ? 'Coleta em andamento...'
                    : 'Assinar pendentes em sequência ($pending)'),
              )),
              const SizedBox(height: 5),
              const Text('Após salvar a assinatura, o próximo participante '
                  'é apresentado. Cancelar encerra a sequência.',
                  style: TextStyle(fontSize: 11.5,color: Colors.black54)),
              const SizedBox(height: 8),
            ],
            ...participants.map((participant) {''','train UI')
t=once(t,'onTap: finalized ? null : () => _sign(participant),','onTap: finalized || _trainingSignatureQueueRunning ? null : () => _sign(participant),','train single tap')
dds.write_text(d,encoding='utf-8',newline='\n')
train.write_text(t,encoding='utf-8',newline='\n')
changed=[x for x,h in before.items() if hashlib.sha256((root/x).read_bytes()).hexdigest()!=h]
if changed:raise SystemExit('SYNC GS DB AI MODIFIED: '+repr(changed))
print('SIGNATURE_BATCH_UI_ISOLATED_OK')
print('SYNC_MEDIA_DATABASE_GS_BYTE_IDENTICAL_OK')
