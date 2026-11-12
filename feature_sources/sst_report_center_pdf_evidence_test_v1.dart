import 'dart:convert';
import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/sst_report_center_models.dart';
import 'package:auditar_sst/services/sst_report_center_pdf.dart';

SstFieldDraft draftWith({List<String> photos=const [],String signature=''}) =>
    SstFieldDraft(
      kind:SstFieldReportKind.nr12,companyId:'empresa-A',
      technician:'Técnico SST',date:'2026-11-11',location:'Produção',
      signaturePath:signature,
      answers:{
        'nr12-02':SstFieldAnswer(
          status:SstFieldStatus.nonConforming,
          observation:'Proteção da correia removida na transmissão.',
          recommendation:'Recompor proteção e verificar o acesso.',
          photoPaths:photos,
        ),
      });

Future<List<int>> pdf(SstFieldDraft draft)=>
  SstFieldReportPdfService.generate(
    companyName:'Empresa A',companyId:'empresa-A',draft:draft);

void main() {
  test('PDF sem foto ou assinatura selecionadas continua disponível',()async{
    final bytes=await pdf(draftWith());
    expect(bytes.length,greaterThan(1200));
    expect(String.fromCharCodes(bytes.take(4)),'%PDF');
  });

  test('arquivo de foto ausente impede PDF com evidência omitida',()async{
    final draft=draftWith(photos:[
      '/caminho_inexistente_auditar_evidencia_20261111.jpg']);
    await expectLater(pdf(draft),
      throwsA(isA<StateError>().having(
        (e)=>e.message,'mensagem',contains('foto selecionada'))));
  });

  test('assinatura selecionada e ausente não some do PDF sem aviso',()async{
    final draft=draftWith(
      signature:'/caminho_inexistente_auditar_assinatura_20261111.png');
    await expectLater(pdf(draft),
      throwsA(isA<StateError>().having(
        (e)=>e.message,'mensagem',contains('assinatura selecionada'))));
  });

  test('foto local válida permite gerar PDF offline',()async{
    final directory=await Directory.systemTemp.createTemp('auditar-pdf-foto');
    addTearDown(()=>directory.delete(recursive:true));
    final image=File(directory.path+'/foto.png');
    // PNG fictício 32 x 32 (>100 bytes) para o teste de renderização.
    await image.writeAsBytes(base64Decode(
      'iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAAV0lEQVR4nGP8'
      '//8/AwMDAwMD9/RoCONr5lIqijAx0BjQ3AJGrmlREBZ1QwYuMgyCaDQVEQKj'
      'qYggGE1FBMFoKiIIRlMRQTCaigiC0VREEIymIoJg6KciAOl1vAamClBHAAAAAElFTkSuQmCC'));
    final bytes=await pdf(draftWith(photos:[image.path]));
    expect(bytes.length,greaterThan(1200));
    expect(String.fromCharCodes(bytes.take(4)),'%PDF');
  });
}
