import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/sst_report_center_models.dart';

void main(){
  test('seis relatórios, 48 perguntas, sem duplicar IDs',(){
    final kinds=SstFieldReportKind.values;
    expect(kinds.length,6);
    expect(SstFieldTemplates.models.length,5);
    final counts=<String,int>{
      'nr12':10,'nr18':10,'nr10':10,'nr35':9,'incident':9
    };
    final ids=<String>{};
    for(final template in SstFieldTemplates.models){
      expect(template.questions.length,counts[template.kind.name]);
      for(final q in template.questions){
        expect(ids.add(q.id),isTrue,reason:q.id);
        expect(q.group.trim(),isNotEmpty);
        expect(q.title.trim(),isNotEmpty);
        expect(q.prompt.trim(),isNotEmpty);
      }
    }
    expect(ids.length,48);
  });

  test('rascunho começa não verificado e não emite PDF vazio',(){
    final draft=SstFieldDraft(
      kind:SstFieldReportKind.nr12,companyId:'empresa-A');
    expect(draft.reviewed,0);
    expect(draft.nonConformities,0);
    expect(draft.isPartial,isTrue);
    expect(draft.hasEnoughForPdf,isFalse);
    expect(draft.answer('nr12-02').status,SstFieldStatus.notChecked);
  });

  test('não conforme requer constatação para habilitar PDF',(){
    var draft=SstFieldDraft(
      kind:SstFieldReportKind.nr18,companyId:'empresa-A',
      technician:'Técnico',date:'2026-11-06');
    draft=draft.update('nr18-03',
      const SstFieldAnswer(status:SstFieldStatus.nonConforming));
    expect(draft.hasEnoughForPdf,isFalse);
    draft=draft.update('nr18-03',const SstFieldAnswer(
      status:SstFieldStatus.nonConforming,
      observation:'Guarda-corpo incompleto no trecho de circulação.',
      recommendation:'Recompor a proteção coletiva.'));
    expect(draft.hasEnoughForPdf,isTrue);
    expect(draft.isPartial,isTrue);
    expect(draft.nonConformities,1);
    expect(draft.answer('nr18-01').status,SstFieldStatus.notChecked);
  });

  test('investigação não inventa causas, depende de narrativa e data',(){
    var draft=SstFieldDraft(kind:SstFieldReportKind.incident,
      companyId:'empresa-A',technician:'Técnico',date:'2026-11-06',
      eventTime:'2026-11-05T10:30');
    draft=draft.update('incident-02',const SstFieldAnswer(
      status:SstFieldStatus.documented,
      observation:'Sequência de fatos informada, pendente confirmação.'));
    expect(draft.hasEnoughForPdf,isFalse);
    draft=draft.copyWith(eventNarrative:
      'Ocorrência comunicada na área industrial; cronologia a confirmar.');
    expect(draft.hasEnoughForPdf,isTrue);
    expect(draft.isPartial,isTrue);
    expect(draft.nonConformities,0);
  });

  test('não troca dados entre empresas e não aceita pergunta inexistente',(){
    var draft=SstFieldDraft(kind:SstFieldReportKind.nr35,
      companyId:'empresa-A',technician:'Técnico',date:'2026-11-06');
    draft=draft.update('nr35-03',const SstFieldAnswer(
      status:SstFieldStatus.conforming,
      observation:'Escada com apoio verificado.'));
    final map=draft.toJson();
    expect(()=>SstFieldDraft.fromJson(map,expectedKind:
      SstFieldReportKind.nr35,expectedCompanyId:'empresa-B'),
      throwsFormatException);
    expect(()=>SstFieldDraft.fromJson(map,expectedKind:
      SstFieldReportKind.nr18,expectedCompanyId:'empresa-A'),
      throwsFormatException);
    map['answers']={
      'nr35-03':const SstFieldAnswer(
        status:SstFieldStatus.conforming).toJson(),
      'nr12-02':const SstFieldAnswer(
        status:SstFieldStatus.nonConforming).toJson(),
    };
    final back=SstFieldDraft.fromJson(map,expectedKind:
      SstFieldReportKind.nr35,expectedCompanyId:'empresa-A');
    expect(back.answers.length,1);
    expect(back.answer('nr12-02').status,SstFieldStatus.notChecked);
  });

  test('mantém até duas fotos; nunca inventa foto, assinatura ou texto',(){
    final original=SstFieldAnswer.fromJson({
      'status':'nonConforming',
      'observation':'Falha observada.',
      'recommendation':'Verificar as proteções.',
      'photoPaths':['/a.jpg','/b.jpg','/c.jpg'],
    });
    expect(original.photoPaths,['/a.jpg','/b.jpg']);
    final from=SstFieldDraft.fromJson(
      SstFieldDraft(kind:SstFieldReportKind.nr10,
        companyId:'A').toJson(),
      expectedKind:SstFieldReportKind.nr10,expectedCompanyId:'A');
    expect(from.signaturePath,isEmpty);
    expect(from.reviewed,0);
  });

  test('mensal é redirecionado à gerência e não tem checklist fictício',(){
    expect(SstFieldReportKind.values.last,SstFieldReportKind.monthly);
    expect(SstFieldTemplates.models.any((m)=>
      m.kind==SstFieldReportKind.monthly),isFalse);
    final draft=SstFieldDraft(kind:SstFieldReportKind.monthly,
      companyId:'A',technician:'Técnico',date:'2026-11-06');
    expect(draft.hasEnoughForPdf,isFalse);
  });
}
