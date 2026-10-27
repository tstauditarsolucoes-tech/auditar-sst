#!/usr/bin/env python3
"""Add an opt-in PDF header/logo editor without touching sync, AI, GS or DB schema.

Existing built-in and custom templates keep their legacy rendering until a user
saves an advanced variation. Source model JSON keeps backward compatibility.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]); platform = sys.argv[2]
assert platform in ('windows', 'android')

def replace(path, old, new, label):
    p = root / path
    s = p.read_text(encoding='utf-8')
    count=s.count(old)
    if count != 1: raise RuntimeError(f'{label}: expected once, found {count}')
    p.write_text(s.replace(old, new, 1), encoding='utf-8', newline='\n')

model='lib/services/report_template_service.dart'
replace(model, "  final bool isBuiltIn;", """  // Opt-in editor fields; absent in previous JSON versions.
  final bool advancedHeader;
  final bool showHeader;
  final String headerSubtitle;
  final String headerAlignment;
  final String leftLogoSource;
  final String rightLogoSource;
  final String leftLogoBase64;
  final String rightLogoBase64;
  final int logoSize;
  final bool isBuiltIn;""", 'model fields')
replace(model, "    this.isBuiltIn = false,", """    this.advancedHeader = false,
    this.showHeader = true,
    this.headerSubtitle = '',
    this.headerAlignment = 'centro',
    this.leftLogoSource = 'auditar',
    this.rightLogoSource = 'cliente',
    this.leftLogoBase64 = '',
    this.rightLogoBase64 = '',
    this.logoSize = 54,
    this.isBuiltIn = false,""", 'constructor')
replace(model, "    if (id == 'auditar_performance_grid' || headerStyle == 'performance') {", """    if (advancedHeader) {
      return title.isEmpty ? 'RELATÓRIO DE VISTORIA' : title;
    }
    if (id == 'auditar_performance_grid' || headerStyle == 'performance') {""", 'public title')
replace(model, "    bool? isBuiltIn,", """    bool? advancedHeader,
    bool? showHeader,
    String? headerSubtitle,
    String? headerAlignment,
    String? leftLogoSource,
    String? rightLogoSource,
    String? leftLogoBase64,
    String? rightLogoBase64,
    int? logoSize,
    bool? isBuiltIn,""", 'copy args')
replace(model, "      isBuiltIn: isBuiltIn ?? this.isBuiltIn,", """      advancedHeader: advancedHeader ?? this.advancedHeader,
      showHeader: showHeader ?? this.showHeader,
      headerSubtitle: headerSubtitle ?? this.headerSubtitle,
      headerAlignment: headerAlignment ?? this.headerAlignment,
      leftLogoSource: leftLogoSource ?? this.leftLogoSource,
      rightLogoSource: rightLogoSource ?? this.rightLogoSource,
      leftLogoBase64: leftLogoBase64 ?? this.leftLogoBase64,
      rightLogoBase64: rightLogoBase64 ?? this.rightLogoBase64,
      logoSize: logoSize ?? this.logoSize,
      isBuiltIn: isBuiltIn ?? this.isBuiltIn,""", 'copy fields')
replace(model, "    'logoMode': logoMode,", """    'logoMode': logoMode,
    'advancedHeader': advancedHeader,
    'showHeader': showHeader,
    'headerSubtitle': headerSubtitle,
    'headerAlignment': headerAlignment,
    'leftLogoSource': leftLogoSource,
    'rightLogoSource': rightLogoSource,
    'leftLogoBase64': leftLogoBase64,
    'rightLogoBase64': rightLogoBase64,
    'logoSize': logoSize,""", 'json fields')
replace(model, "      showChecklistDetails: map['showChecklistDetails'] == true,\n      isBuiltIn: false,", """      showChecklistDetails: map['showChecklistDetails'] == true,
      advancedHeader: map['advancedHeader'] == true,
      showHeader: map['showHeader'] != false,
      headerSubtitle: '${map['headerSubtitle'] ?? ''}'.trim(),
      headerAlignment: '${map['headerAlignment'] ?? 'centro'}'.trim(),
      leftLogoSource: '${map['leftLogoSource'] ?? (map['logoMode'] == 'nenhuma' || map['logoMode'] == 'cliente' ? 'nenhuma' : 'auditar')}',
      rightLogoSource: '${map['rightLogoSource'] ?? (map['logoMode'] == 'nenhuma' || map['logoMode'] == 'auditar' ? 'nenhuma' : 'cliente')}',
      leftLogoBase64: '${map['leftLogoBase64'] ?? ''}',
      rightLogoBase64: '${map['rightLogoBase64'] ?? ''}',
      logoSize: (map['logoSize'] is num) ? (map['logoSize'] as num).round().clamp(30, 90).toInt() : 54,
      isBuiltIn: false,""", 'json load')

# Shared helper maps independent logo slots to image providers, used by all PDF renderers.
(root/'lib/services/report_header_pdf_service.dart').write_text(r'''import 'dart:convert';

import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import 'report_template_service.dart';

/// PDF-only presentation utility. Does not load/change any business data.
class ReportHeaderPdfService {
  static pw.ImageProvider? logo(
    String source,
    String custom,
    pw.ImageProvider? auditar,
    pw.ImageProvider? company,
  ) {
    if (source == 'auditar') return auditar;
    if (source == 'cliente') return company; // Never duplicate Auditar as a fallback.
    if (source != 'personalizada' || custom.length > 500000) return null;
    try {
      final bytes = base64Decode(custom);
      if (bytes.length > 350000 || bytes.length < 16) return null;
      return pw.MemoryImage(bytes);
    } catch (_) {
      return null;
    }
  }

  static pw.Widget _slot(pw.ImageProvider? image, double size) => pw.SizedBox(
    width: size,
    height: size,
    child: image == null ? pw.SizedBox() : pw.Image(image, fit: pw.BoxFit.contain),
  );

  static pw.Widget logoRow({
    required ReportTemplateDefinition template,
    required pw.ImageProvider? auditar,
    required pw.ImageProvider? company,
  }) {
    if (!template.showHeader) return pw.SizedBox();
    final left=logo(template.leftLogoSource,template.leftLogoBase64,auditar,company);
    final right=logo(template.rightLogoSource,template.rightLogoBase64,auditar,company);
    return pw.Row(children:[
      _slot(left,template.logoSize.toDouble()),
      pw.Spacer(),
      _slot(right,template.logoSize.toDouble()),
    ]);
  }

  static pw.Widget header({
    required ReportTemplateDefinition template,
    required pw.ImageProvider? auditar,
    required pw.ImageProvider? companyLogo,
    required String company,
    String details = '',
  }) {
    if (!template.showHeader) return pw.SizedBox();
    final left=logo(template.leftLogoSource,template.leftLogoBase64,auditar,companyLogo);
    final right=logo(template.rightLogoSource,template.rightLogoBase64,auditar,companyLogo);
    final size=template.logoSize.toDouble();
    PdfColor primary;
    try { primary=PdfColor.fromHex(template.primaryColor); }
    catch (_) { primary=const PdfColor(0.08,0.22,0.42); }
    final align=template.headerAlignment == 'esquerda'
        ? pw.TextAlign.left : template.headerAlignment == 'direita'
            ? pw.TextAlign.right : pw.TextAlign.center;
    return pw.Container(
      margin:const pw.EdgeInsets.only(bottom:9),
      padding:const pw.EdgeInsets.only(bottom:7),
      decoration:pw.BoxDecoration(border:pw.Border(bottom:pw.BorderSide(color:primary,width:.8))),
      child:pw.Row(crossAxisAlignment:pw.CrossAxisAlignment.center,children:[
        _slot(left,size),pw.SizedBox(width:8),
        pw.Expanded(child:pw.Column(crossAxisAlignment:pw.CrossAxisAlignment.stretch,children:[
          pw.Text(template.publicTitle,textAlign:align,style:pw.TextStyle(
            color:primary,fontWeight:pw.FontWeight.bold,fontSize:11)),
          if (template.headerSubtitle.trim().isNotEmpty)
            pw.Text(template.headerSubtitle.trim(),textAlign:align,
              style:const pw.TextStyle(fontSize:8.2)),
          if (company.trim().isNotEmpty)
            pw.Text(company.trim(),textAlign:align,
              style:pw.TextStyle(color:primary,fontWeight:pw.FontWeight.bold,fontSize:9)),
          if (details.trim().isNotEmpty)
            pw.Text(details.trim(),textAlign:align,
              style:const pw.TextStyle(fontSize:7.2,color:PdfColors.grey700)),
        ])),
        pw.SizedBox(width:8),_slot(right,size),
      ]),
    );
  }
}
''',encoding='utf-8',newline='\n')

editor='lib/screens/report_template_library_screen.dart'
replace(editor, "import 'dart:io';", "import 'dart:io';\nimport 'dart:convert';", 'editor import')
replace(editor, "  late final TextEditingController title;", """  late final TextEditingController title;
  late final TextEditingController subtitle;
  late bool showHeader;
  late String headerAlignment;
  late String leftLogoSource;
  late String rightLogoSource;
  late String leftLogoBase64;
  late String rightLogoBase64;
  late int logoSize;""", 'editor state')
replace(editor, "    title = TextEditingController(text: b.headerTitle);", """    title = TextEditingController(text: b.headerTitle);
    subtitle = TextEditingController(text: b.headerSubtitle);
    showHeader = b.showHeader;
    headerAlignment = b.headerAlignment;
    leftLogoSource = b.advancedHeader ? b.leftLogoSource :
        (b.logoMode == 'ambas' || b.logoMode == 'auditar' ? 'auditar' : 'nenhuma');
    rightLogoSource = b.advancedHeader ? b.rightLogoSource :
        (b.logoMode == 'ambas' || b.logoMode == 'cliente' ? 'cliente' : 'nenhuma');
    leftLogoBase64 = b.leftLogoBase64;
    rightLogoBase64 = b.rightLogoBase64;
    logoSize = b.logoSize;""", 'editor init')
replace(editor, "    title.dispose();", "    title.dispose();\n    subtitle.dispose();", 'editor dispose')
replace(editor, "        headerTitle:\n            title.text.trim().isEmpty\n                ? widget.base.headerTitle\n                : title.text.trim(),", """        headerTitle: title.text.trim().isEmpty
            ? 'RELATÓRIO DE VISTORIA' : title.text.trim(),
        advancedHeader: widget.fullEditor || widget.base.advancedHeader,
        showHeader: showHeader,
        headerSubtitle: subtitle.text.trim(),
        headerAlignment: headerAlignment,
        leftLogoSource: leftLogoSource,
        rightLogoSource: rightLogoSource,
        leftLogoBase64: leftLogoBase64,
        rightLogoBase64: rightLogoBase64,
        logoSize: logoSize,""", 'editor save')

picker=r'''  Future<void> _pickLogo(bool isLeft) async {
    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['png','jpg','jpeg'],
      withData: true,
    );
    if (picked == null || picked.files.isEmpty) return;
    final file = picked.files.single;
    Uint8List? bytes = file.bytes;
    if (bytes == null && file.path != null) {
      bytes = await File(file.path!).readAsBytes();
    }
    if (bytes == null || bytes.isEmpty || bytes.length > 280000) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Use PNG ou JPG de até 280 KB.')));
      return;
    }
    final png=bytes.length>8 && bytes[0]==137 && bytes[1]==80 && bytes[2]==78 && bytes[3]==71;
    final jpg=bytes.length>3 && bytes[0]==255 && bytes[1]==216 && bytes[2]==255;
    if (!png && !jpg) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('A imagem deve ser PNG ou JPG válido.')));
      return;
    }
    if (!mounted) return;
    setState(() {
      if (isLeft) {
        leftLogoBase64=base64Encode(bytes!);
        leftLogoSource='personalizada';
      } else {
        rightLogoBase64=base64Encode(bytes!);
        rightLogoSource='personalizada';
      }
    });
  }

  Widget _logoChoice(bool isLeft) {
    final choice=isLeft ? leftLogoSource : rightLogoSource;
    final custom=isLeft ? leftLogoBase64 : rightLogoBase64;
    return Column(crossAxisAlignment: CrossAxisAlignment.start,children:[
      DropdownButtonFormField<String>(
        value: const ['auditar','cliente','personalizada','nenhuma'].contains(choice)
            ? choice : 'nenhuma',
        decoration: InputDecoration(labelText:isLeft ? 'Logo esquerda' : 'Logo direita'),
        items: const [
          DropdownMenuItem(value:'auditar',child:Text('Logo Auditar / SST')),
          DropdownMenuItem(value:'cliente',child:Text('Logo da empresa (se cadastrada)')),
          DropdownMenuItem(value:'personalizada',child:Text('Imagem personalizada')),
          DropdownMenuItem(value:'nenhuma',child:Text('Sem logo')),
        ],
        onChanged:(value)=>setState(() {
          if (isLeft) leftLogoSource=value ?? 'nenhuma';
          else rightLogoSource=value ?? 'nenhuma';
        }),
      ),
      if (choice=='personalizada') ...[
        const SizedBox(height:5),
        OutlinedButton.icon(onPressed:()=>_pickLogo(isLeft),
          icon:const Icon(Icons.add_photo_alternate_outlined),
          label:Text(custom.isEmpty ? 'Adicionar PNG/JPG' : 'Trocar imagem')),
        if (custom.isEmpty) const Text('Selecione uma imagem para este lado.'),
      ],
    ]);
  }

  Widget _livePreview() {
    final color=int.tryParse(primary.text.trim().replaceFirst('#',''),radix:16);
    final chosenColor= color == null || primary.text.trim().replaceFirst('#','').length != 6
        ? const Color(0xFF0B2E4F) : Color(0xFF000000 | color);
    Widget logo(String source,String b64) {
      if (source=='nenhuma') return const SizedBox(width:64,height:64);
      if (source=='personalizada' && b64.isNotEmpty) {
        try { return SizedBox(width:64,height:64,child:Image.memory(
            base64Decode(b64),fit:BoxFit.contain)); }
        catch (_) {}
      }
      return SizedBox(width:64,height:64,child:Center(child:Text(
        source=='cliente' ? 'EMPRESA' : source=='auditar' ? 'AUDITAR' : 'LOGO',
        textAlign:TextAlign.center,style:const TextStyle(fontSize:9,fontWeight:FontWeight.bold))));
    }
    final alignment=headerAlignment=='esquerda'?TextAlign.left:
        headerAlignment=='direita'?TextAlign.right:TextAlign.center;
    return Card(elevation:0,color:Colors.white,
      shape:RoundedRectangleBorder(side:BorderSide(color:Colors.grey.shade300),
        borderRadius:BorderRadius.circular(10)),
      child:Padding(padding:const EdgeInsets.all(14),child:Column(
        crossAxisAlignment:CrossAxisAlignment.stretch,children:[
        const Text('Prévia esquemática do cabeçalho',
          style:TextStyle(fontWeight:FontWeight.w700)),
        const SizedBox(height:10),
        if (!showHeader) const Text('Cabeçalho oculto neste modelo.')
        else Row(children:[
          logo(leftLogoSource,leftLogoBase64),
          const SizedBox(width:8),
          Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
            Text(title.text.trim().isEmpty?'RELATÓRIO DE VISTORIA':title.text.trim(),
              textAlign:alignment,style:TextStyle(color:chosenColor,fontWeight:FontWeight.bold)),
            if (subtitle.text.trim().isNotEmpty)
              Text(subtitle.text.trim(),textAlign:alignment,
                style:const TextStyle(fontSize:11)),
            Text('NOME DA EMPRESA',textAlign:alignment,
              style:TextStyle(fontSize:11,fontWeight:FontWeight.w600,color:chosenColor)),
          ])),
          const SizedBox(width:8),logo(rightLogoSource,rightLogoBase64),
        ]),
        const Divider(height:20),
        const Text('Exemplo de conteúdo • NC • Evidências • Conclusão',
          style:TextStyle(fontSize:11,color:Colors.black54)),
      ])));
  }

'''
replace(editor,"  void _save() {\n    if (name.text.trim().isEmpty) return;",picker+"  void _save() {\n    if (name.text.trim().isEmpty) return;",'editor helpers')
# Enrich title field live change and insert Windows advanced block.
replace(editor,"""                  labelText: 'Título do cabeçalho',
                ),
              ),
              const SizedBox(height: 10),""", """                  labelText: 'Título do cabeçalho',
                ),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 10),
              if (full) ...[
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  value: showHeader,
                  title: const Text('Mostrar cabeçalho no relatório'),
                  onChanged: (value) => setState(() => showHeader=value),
                ),
                TextField(controller:subtitle,
                  decoration:const InputDecoration(labelText:'Subtítulo opcional'),
                  onChanged:(_)=>setState(() {})),
                const SizedBox(height:10),
                DropdownButtonFormField<String>(
                  value: headerAlignment,
                  decoration:const InputDecoration(labelText:'Alinhamento do cabeçalho'),
                  items: const [
                    DropdownMenuItem(value:'esquerda',child:Text('À esquerda')),
                    DropdownMenuItem(value:'centro',child:Text('Centralizado')),
                    DropdownMenuItem(value:'direita',child:Text('À direita')),
                  ],
                  onChanged:(value)=>setState(()=>headerAlignment=value??'centro'),
                ),
                const SizedBox(height:10),
                _logoChoice(true),
                const SizedBox(height:10),
                _logoChoice(false),
                const SizedBox(height:6),
                Text('Tamanho das logos: $logoSize pt'),
                Slider(value:logoSize.toDouble(),min:30,max:90,divisions:12,
                  onChanged:(v)=>setState(()=>logoSize=v.round())),
                const Text('A ausência de logo da empresa deixa o espaço vazio. '
                  'O app não repetirá outra imagem.',
                  style:TextStyle(fontSize:11,color:Colors.black54)),
                const SizedBox(height:12),
                _livePreview(),
                const SizedBox(height:10),
              ],""",'editor UI')
# Avoid DropdownButton assertion for built-ins with special headerStyle.
replace(editor,"""                    DropdownMenuItem(value: 'impacto', child: Text('Destaque')),
                  ],
                  onChanged:""", """                    DropdownMenuItem(value: 'impacto', child: Text('Destaque')),
                    DropdownMenuItem(value: 'performance', child: Text('Performance (foto + descrição)')),
                    DropdownMenuItem(value: 'institucional2', child: Text('Padrão Auditar 2')),
                  ],
                  onChanged:""",'editor special renderers')
replace(editor, "        width: full ? 620 : 430,", "        width: full ? 780 : 430,", 'editor width')
replace(editor, "widget.base.copyWith(\n        id: ReportTemplateService.newCustomId(),", "widget.base.copyWith(\n        id: widget.base.isBuiltIn ? ReportTemplateService.newCustomId() : widget.base.id,", 'edit saved custom without duplicated models')
replace(editor, "label: const Text('Salvar como novo modelo'),", "label: Text(widget.base.isBuiltIn ? 'Salvar como novo modelo' : 'Salvar alterações'),", 'save button label')
replace(editor, """                    hintText: '#0B2E4F',
                  ),
                )""", """                    hintText: '#0B2E4F',
                  ),
                  onChanged: (_) => setState(() {}),
                )""", 'live color preview')


# PDF integrations: no legacy renderer rewrite; each uses shared header only
# for saved advanced variations and removes duplicate logo fallback.
perf='lib/services/performance_report_pdf_service.dart'
replace(perf,"import 'report_logo_service.dart';", "import 'report_logo_service.dart';\nimport 'report_header_pdf_service.dart';",'performance import')
replace(perf,"      title: 'Relatório de vistoria',", "      title: template.publicTitle,", 'performance metadata')
replace(perf,"""    // The template name is an internal layout choice, not the client's document title.
    // Keep "Performance" in the report-model library, never print it on the PDF.
    const titleLine = 'RELATÓRIO DE VISTORIA';""", """    if (template.advancedHeader) {
      return ReportHeaderPdfService.header(
        template:template,auditar:sstLogo,companyLogo:companyLogo,
        company:company,details:'Vistoria realizada em $dateText | $location');
    }
    // Internal model name is never a document title.
    const titleLine = 'RELATÓRIO DE VISTORIA';""",'performance advanced header')
replace(perf,"(companyLogo ?? sstLogo) == null", "companyLogo == null",'performance null fallback')
replace(perf,"(companyLogo ?? sstLogo)!", "companyLogo!",'performance logo fallback')

styled='lib/services/styled_report_pdf_service.dart'
replace(styled,"import 'report_logo_service.dart';", "import 'report_logo_service.dart';\nimport 'report_header_pdf_service.dart';",'styled import')
replace(styled,"if (template.id == ReportTemplateService.standard2TemplateId) {", "if (template.id == ReportTemplateService.standard2TemplateId ||\n        template.headerStyle == 'institucional2') {",'keep standard2 renderer for customized variations')
replace(styled,"""        _dualLogos(auditarLogo, companyLogo, 58),""", """        template.advancedHeader
          ? ReportHeaderPdfService.logoRow(template:template,auditar:auditarLogo,company:companyLogo)
          : _dualLogos(auditarLogo, companyLogo, 58),""",'styled cover logos')
replace(styled,"""        header:
            (_) => _pageHeader(""", """        header:
            (_) => template.advancedHeader
                ? ReportHeaderPdfService.header(
                    template:template,auditar:auditarLogo,
                    companyLogo:companyLogo,company:company,
                    details:reportNumber)
                : _pageHeader(""",'styled advanced header')
replace(styled,"_logoBox(companyLogo ?? auditarLogo, compact ? 34 : 43)","_logoBox(companyLogo, compact ? 34 : 43)",'styled dup page')
replace(styled,"_logoBox(company ?? sst, size)","_logoBox(company, size)",'styled dup cover')

standard='lib/services/auditar_standard2_pdf_service.dart'
replace(standard,"import 'report_logo_service.dart';", "import 'report_logo_service.dart';\nimport 'report_header_pdf_service.dart';",'standard import')
replace(standard,"""    final widgets = <pw.Widget>[
      pw.Center(""", """    final widgets = <pw.Widget>[
      if (!template.advancedHeader) pw.Center(""",'standard title 1')
replace(standard,"""      pw.SizedBox(height: 3),
      pw.Center(""", """      if (!template.advancedHeader) pw.SizedBox(height: 3),
      pw.Center(""",'standard title 2')
replace(standard,"""      title: 'Padrão Auditar 2 - ' + company,""", """      title: template.publicTitle + ' - ' + company,""",'standard metadata')
replace(standard,"""        header: (_) => _header(logo, companyLogo, company),""", """        header: (_) => template.advancedHeader
          ? ReportHeaderPdfService.header(template:template,auditar:logo,
              companyLogo:companyLogo,company:company)
          : _header(logo, companyLogo, company),""",'standard advanced header')
replace(standard,"_logo(companyLogo ?? logo, 52)","_logo(companyLogo, 52)",'standard duplicate')

express='lib/services/express_round_pdf_service.dart'
replace(express,"import 'report_logo_service.dart';", "import 'report_logo_service.dart';\nimport 'report_header_pdf_service.dart';",'ronda import')
replace(express,"""                  pw.Row(
                    children: [
                      _pdfLogo(auditarLogo, 64, 64),
                      pw.Spacer(),
                      _pdfLogo(companyLogo ?? auditarLogo, 64, 64),
                    ],
                  ),""", """                  template?.advancedHeader == true
                    ? ReportHeaderPdfService.logoRow(template:template!,
                        auditar:auditarLogo,company:companyLogo)
                    : pw.Row(children: [
                        _pdfLogo(auditarLogo, 64, 64),pw.Spacer(),
                        _pdfLogo(companyLogo, 64, 64),
                      ]),""",'ronda cover logos')
replace(express,"""        header:
            (context) => _header(""", """        header:
            (context) => template?.advancedHeader == true
               ? ReportHeaderPdfService.header(template:template!,
                   auditar:auditarLogo,companyLogo:companyLogo,
                   company:company.name)
               : _header(""",'ronda advanced header')
replace(express,"_pdfLogo(companyLogo ?? auditarLogo, 47, 47)","_pdfLogo(companyLogo, 47, 47)",'ronda duplicate')

# Ship the additive pure-model test inside the assembled Flutter application.
from shutil import copyfile
model_test=Path(__file__).resolve().parent.parent/'build_sources/v3.29.115-report-editor/report_template_editor_model_test.dart'
assert model_test.exists(), 'report editor model test unavailable'
copyfile(model_test, root/'test/report_template_editor_model_test.dart')

# Version change last: existing regression markers test old version before this patch.
new_version='3.30.39+227' if platform=='windows' else '3.29.115+257'
pub=root/'pubspec.yaml'; value=pub.read_text(encoding='utf-8')
import re
value, count=re.subn(r'(?m)^version: 3\.(?:29|30)\.\d+\+\d+$',f'version: {new_version}',value)
assert count==1
pub.write_text(value,encoding='utf-8',newline='\n')
print('REPORT_EDITOR_ADVANCED_OK',platform,new_version)