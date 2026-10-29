import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/report_template_service.dart';
import 'package:auditar_sst/services/report_header_pdf_service.dart';

void main() {
  test('old custom template remains a legacy layout after JSON read', () {
    final original=ReportTemplateDefinition.fromJson({
      'id':'old','name':'Modelo antigo','headerTitle':'RELATÓRIO TÉCNICO',
      'logoMode':'cliente','showCover':false,
    });
    expect(original.advancedHeader,isFalse);
    expect(original.showHeader,isTrue);
    expect(original.leftLogoSource,'nenhuma');
    expect(original.rightLogoSource,'cliente');
    expect(original.publicTitle,'RELATÓRIO TÉCNICO');
  });

  test('advanced editor preserves independent logos and custom public title', () {
    final template=ReportTemplateService.builtIns.firstWhere(
      (t)=>t.id==ReportTemplateService.performanceTemplateId).copyWith(
      id:'new_custom_1',name:'Performance personalizado',
      advancedHeader:true,showHeader:true,
      headerTitle:'RELATÓRIO DE SEGURANÇA DA UNIDADE',
      headerSubtitle:'Inspeção de campo',
      headerAlignment:'esquerda',
      leftLogoSource:'nenhuma',rightLogoSource:'personalizada',
      rightLogoBase64:'ZHVtbXk=',logoSize:72,
    );
    final restored=ReportTemplateDefinition.fromJson(template.toJson());
    expect(restored.advancedHeader,isTrue);
    expect(restored.publicTitle,'RELATÓRIO DE SEGURANÇA DA UNIDADE');
    expect(restored.leftLogoSource,'nenhuma');
    expect(restored.rightLogoSource,'personalizada');
    expect(restored.rightLogoBase64,'ZHVtbXk=');
    expect(restored.logoSize,72);
    expect(restored.headerAlignment,'esquerda');
    expect(restored.headerSubtitle,'Inspeção de campo');
  });

  test('client logo missing never reuses Auditar logo', () {
    expect(ReportHeaderPdfService.logo('cliente','',null,null),isNull);
    expect(ReportHeaderPdfService.logo('nenhuma','',null,null),isNull);
  });
}