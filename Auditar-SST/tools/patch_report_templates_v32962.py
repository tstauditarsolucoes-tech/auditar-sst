from pathlib import Path
import re
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')


def write(rel, content):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + '\n', encoding='utf-8')


def replace_once(path, old, new, label):
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'âncora ausente ({label}) em {path}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


write('lib/services/report_template_service.dart', r'''
import 'dart:convert';

import '../database.dart';

class ReportTemplateDefinition {
  final String id;
  final String name;
  final String description;
  final String primaryColor;
  final String secondaryColor;
  final String headerTitle;
  final String headerStyle;
  final String logoMode;
  final String footerText;
  final int photoColumns;
  final String signatureStyle;
  final bool showCover;
  final bool showSummary;
  final bool showChecklistDetails;
  final bool isBuiltIn;
  final bool useLegacyRenderer;

  const ReportTemplateDefinition({
    required this.id,
    required this.name,
    required this.description,
    required this.primaryColor,
    required this.secondaryColor,
    required this.headerTitle,
    required this.headerStyle,
    required this.logoMode,
    required this.footerText,
    required this.photoColumns,
    required this.signatureStyle,
    required this.showCover,
    required this.showSummary,
    required this.showChecklistDetails,
    this.isBuiltIn = false,
    this.useLegacyRenderer = false,
  });

  ReportTemplateDefinition copyWith({
    String? id,
    String? name,
    String? description,
    String? primaryColor,
    String? secondaryColor,
    String? headerTitle,
    String? headerStyle,
    String? logoMode,
    String? footerText,
    int? photoColumns,
    String? signatureStyle,
    bool? showCover,
    bool? showSummary,
    bool? showChecklistDetails,
    bool? isBuiltIn,
    bool? useLegacyRenderer,
  }) {
    return ReportTemplateDefinition(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      primaryColor: primaryColor ?? this.primaryColor,
      secondaryColor: secondaryColor ?? this.secondaryColor,
      headerTitle: headerTitle ?? this.headerTitle,
      headerStyle: headerStyle ?? this.headerStyle,
      logoMode: logoMode ?? this.logoMode,
      footerText: footerText ?? this.footerText,
      photoColumns: photoColumns ?? this.photoColumns,
      signatureStyle: signatureStyle ?? this.signatureStyle,
      showCover: showCover ?? this.showCover,
      showSummary: showSummary ?? this.showSummary,
      showChecklistDetails: showChecklistDetails ?? this.showChecklistDetails,
      isBuiltIn: isBuiltIn ?? this.isBuiltIn,
      useLegacyRenderer: useLegacyRenderer ?? this.useLegacyRenderer,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'description': description,
        'primaryColor': primaryColor,
        'secondaryColor': secondaryColor,
        'headerTitle': headerTitle,
        'headerStyle': headerStyle,
        'logoMode': logoMode,
        'footerText': footerText,
        'photoColumns': photoColumns,
        'signatureStyle': signatureStyle,
        'showCover': showCover,
        'showSummary': showSummary,
        'showChecklistDetails': showChecklistDetails,
      };

  factory ReportTemplateDefinition.fromJson(Map<String, dynamic> map) {
    return ReportTemplateDefinition(
      id: '${map['id'] ?? ''}'.trim(),
      name: '${map['name'] ?? 'Modelo personalizado'}'.trim(),
      description: '${map['description'] ?? ''}'.trim(),
      primaryColor: '${map['primaryColor'] ?? '#0B2E4F'}'.trim(),
      secondaryColor: '${map['secondaryColor'] ?? '#178A3D'}'.trim(),
      headerTitle: '${map['headerTitle'] ?? 'RELATÓRIO DE INSPEÇÃO SST'}'.trim(),
      headerStyle: '${map['headerStyle'] ?? 'classico'}'.trim(),
      logoMode: '${map['logoMode'] ?? 'ambas'}'.trim(),
      footerText: '${map['footerText'] ?? 'Auditar SST - Segurança do Trabalho'}'.trim(),
      photoColumns: (map['photoColumns'] is num)
          ? (map['photoColumns'] as num).round().clamp(1, 3)
          : 2,
      signatureStyle: '${map['signatureStyle'] ?? 'app'}'.trim(),
      showCover: map['showCover'] != false,
      showSummary: map['showSummary'] != false,
      showChecklistDetails: map['showChecklistDetails'] == true,
      isBuiltIn: false,
      useLegacyRenderer: false,
    );
  }
}

class ReportTemplateService {
  static const _customKey = 'report_templates_custom_v1';
  static const currentTemplateId = 'auditar_atual';

  static const ReportTemplateDefinition currentTemplate = ReportTemplateDefinition(
    id: currentTemplateId,
    name: 'Padrão Auditar atual',
    description: 'Modelo que já funciona hoje. Mantido intacto como padrão e fallback.',
    primaryColor: '#0B2E4F',
    secondaryColor: '#178A3D',
    headerTitle: 'RELATÓRIO DE INSPEÇÃO SST',
    headerStyle: 'classico',
    logoMode: 'ambas',
    footerText: 'Auditar SST - Segurança do Trabalho',
    photoColumns: 2,
    signatureStyle: 'app',
    showCover: true,
    showSummary: true,
    showChecklistDetails: true,
    isBuiltIn: true,
    useLegacyRenderer: true,
  );

  static const List<ReportTemplateDefinition> builtIns = [
    currentTemplate,
    ReportTemplateDefinition(
      id: 'auditar_executivo',
      name: 'Auditar Executivo',
      description: 'Curto, visual e direto para gestores, com resumo, prioridades e evidências.',
      primaryColor: '#0B2E4F',
      secondaryColor: '#178A3D',
      headerTitle: 'RELATÓRIO EXECUTIVO SST',
      headerStyle: 'classico',
      logoMode: 'ambas',
      footerText: 'Auditar SST • Segurança do Trabalho',
      photoColumns: 2,
      signatureStyle: 'app',
      showCover: true,
      showSummary: true,
      showChecklistDetails: false,
      isBuiltIn: true,
    ),
    ReportTemplateDefinition(
      id: 'auditar_fotografico',
      name: 'Auditar Fotográfico',
      description: 'Valoriza as evidências: foto, problema, risco, correção e prioridade.',
      primaryColor: '#157A46',
      secondaryColor: '#0B2E4F',
      headerTitle: 'RELATÓRIO FOTOGRÁFICO DE SST',
      headerStyle: 'impacto',
      logoMode: 'ambas',
      footerText: 'Auditar SST • Evidências de campo',
      photoColumns: 1,
      signatureStyle: 'app',
      showCover: true,
      showSummary: true,
      showChecklistDetails: false,
      isBuiltIn: true,
    ),
    ReportTemplateDefinition(
      id: 'auditar_obra',
      name: 'Auditar Obra',
      description: 'Leitura rápida para obras, com destaque visual para risco, prioridade e correção.',
      primaryColor: '#D97706',
      secondaryColor: '#7C2D12',
      headerTitle: 'RELATÓRIO DE VISTORIA DE OBRA',
      headerStyle: 'impacto',
      logoMode: 'ambas',
      footerText: 'Auditar SST • Vistoria de obra',
      photoColumns: 2,
      signatureStyle: 'app',
      showCover: true,
      showSummary: true,
      showChecklistDetails: false,
      isBuiltIn: true,
    ),
    ReportTemplateDefinition(
      id: 'auditar_tecnico_clean',
      name: 'Auditar Técnico Clean',
      description: 'Visual limpo e técnico, com mais espaço para texto, referência normativa e checklist.',
      primaryColor: '#1F2937',
      secondaryColor: '#6B7280',
      headerTitle: 'RELATÓRIO TÉCNICO DE SST',
      headerStyle: 'compacto',
      logoMode: 'ambas',
      footerText: 'Auditar SST • Relatório técnico',
      photoColumns: 2,
      signatureStyle: 'app',
      showCover: false,
      showSummary: true,
      showChecklistDetails: true,
      isBuiltIn: true,
    ),
    ReportTemplateDefinition(
      id: 'auditar_nr12',
      name: 'Auditar NR-12',
      description: 'Focado em máquinas e equipamentos, com leitura técnica e destaque para não conformidades.',
      primaryColor: '#B91C1C',
      secondaryColor: '#111827',
      headerTitle: 'RELATÓRIO DE INSPEÇÃO NR-12',
      headerStyle: 'impacto',
      logoMode: 'ambas',
      footerText: 'Auditar SST • Segurança em máquinas e equipamentos',
      photoColumns: 2,
      signatureStyle: 'app',
      showCover: true,
      showSummary: true,
      showChecklistDetails: true,
      isBuiltIn: true,
    ),
  ];

  static String _selectionKey(String companyId) => 'report_template_company_${companyId.trim()}';

  static Future<List<ReportTemplateDefinition>> getAllTemplates() async {
    final custom = await _loadCustom();
    return [...builtIns, ...custom];
  }

  static Future<List<ReportTemplateDefinition>> _loadCustom() async {
    final raw = await AppDatabase.instance.getSetting(_customKey, fallback: '[]');
    try {
      final decoded = jsonDecode(raw);
      if (decoded is! List) return const [];
      return decoded
          .whereType<Map>()
          .map((e) => ReportTemplateDefinition.fromJson(Map<String, dynamic>.from(e)))
          .where((e) => e.id.isNotEmpty)
          .toList();
    } catch (_) {
      return const [];
    }
  }

  static Future<void> saveCustom(ReportTemplateDefinition template) async {
    final list = await _loadCustom();
    final normalized = template.copyWith(isBuiltIn: false, useLegacyRenderer: false);
    final index = list.indexWhere((e) => e.id == normalized.id);
    if (index >= 0) {
      list[index] = normalized;
    } else {
      list.add(normalized);
    }
    await AppDatabase.instance.setSetting(
      _customKey,
      jsonEncode(list.map((e) => e.toJson()).toList()),
    );
  }

  static Future<void> deleteCustom(String templateId) async {
    final list = await _loadCustom();
    list.removeWhere((e) => e.id == templateId);
    await AppDatabase.instance.setSetting(
      _customKey,
      jsonEncode(list.map((e) => e.toJson()).toList()),
    );
  }

  static Future<void> selectForCompany(String companyId, String templateId) async {
    if (companyId.trim().isEmpty) return;
    await AppDatabase.instance.setSetting(_selectionKey(companyId), templateId);
  }

  static Future<ReportTemplateDefinition> selectedForCompany(String companyId) async {
    if (companyId.trim().isEmpty) return currentTemplate;
    final selected = await AppDatabase.instance.getSetting(
      _selectionKey(companyId),
      fallback: currentTemplateId,
    );
    final all = await getAllTemplates();
    return all.firstWhere(
      (e) => e.id == selected,
      orElse: () => currentTemplate,
    );
  }

  static Future<ReportTemplateDefinition> resolveForHeader(Map<String, Object?>? header) async {
    final companyId = '${header?['company_id'] ?? ''}'.trim();
    return selectedForCompany(companyId);
  }

  static String newCustomId() => 'custom_${DateTime.now().microsecondsSinceEpoch}';
}
''')

write('lib/services/styled_report_pdf_service.dart', r'''
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/services.dart' show rootBundle;
import 'package:intl/intl.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

import '../database.dart';
import '../models.dart';
import 'report_template_service.dart';

class StyledReportPdfService {
  static Future<Uint8List> generateInspectionPdf(
    String inspectionId, {
    required Map<String, Object?> header,
    required ReportTemplateDefinition template,
    bool executive = false,
    bool? includeActionPlan,
  }) async {
    final db = AppDatabase.instance;
    final answers = await db.getAnswers(inspectionId);
    final actions = await db.getActionsForInspection(inspectionId);
    final ncs = await db.getNonConformitiesForInspection(inspectionId);
    final includePlan = includeActionPlan ??
        ((header['include_action_plan'] is int)
            ? (header['include_action_plan'] as int) == 1
            : ('${header['include_action_plan'] ?? '1'}' != '0'));

    final primary = _color(template.primaryColor, const PdfColor(0.04, 0.18, 0.31));
    final secondary = _color(template.secondaryColor, const PdfColor(0.09, 0.54, 0.24));
    final doc = pw.Document();
    final auditarLogo = await _assetImage('assets/branding/auditar_icon.png');
    final companyLogo = await _fileImage('${header['company_logo_path'] ?? ''}');
    final techSignature = await _fileImage('${header['technician_signature_path'] ?? ''}');
    final responsibleSignature = await _fileImage('${header['responsible_signature_path'] ?? ''}');

    final ncByAnswer = <String, NonConformity>{for (final nc in ncs) nc.answerId: nc};
    final actionsByAnswer = <String, List<ActionPlan>>{};
    for (final action in actions) {
      actionsByAnswer.putIfAbsent(action.answerId, () => <ActionPlan>[]).add(action);
    }

    final issueAnswers = answers
        .where((e) => e.status == 'Não Conforme' || e.status == 'Parcial')
        .toList();
    final issueData = <_IssueData>[];
    for (final answer in issueAnswers) {
      final photos = await db.getPhotosForAnswer(answer.id);
      final images = <pw.MemoryImage>[];
      for (final photo in photos.take(template.photoColumns == 1 ? 4 : 6)) {
        final image = await _fileImage(photo.path);
        if (image != null) images.add(image);
      }
      issueData.add(_IssueData(
        answer: answer,
        nc: ncByAnswer[answer.id],
        actions: actionsByAnswer[answer.id] ?? const [],
        photos: images,
      ));
    }

    final company = '${header['company_name'] ?? '-'}'.trim();
    final sector = '${header['sector_name'] ?? header['area'] ?? '-'}'.trim();
    final worksite = '${header['worksite_name'] ?? ''}'.trim();
    final date = DateTime.tryParse('${header['date'] ?? ''}');
    final dateText = date == null ? '-' : DateFormat('dd/MM/yyyy').format(date);
    final reportNumber = '${header['report_number'] ?? ''}'.trim();
    final considered = answers.where((e) => e.status != 'Não se aplica').length;
    final conformes = answers.where((e) => e.status == 'Conforme').length;
    final parciais = answers.where((e) => e.status == 'Parcial').length;
    final naoConformes = answers.where((e) => e.status == 'Não Conforme').length;
    final conformity = considered == 0 ? 0 : (conformes / considered * 100).round();

    if (template.showCover) {
      doc.addPage(
        pw.Page(
          pageFormat: PdfPageFormat.a4,
          margin: const pw.EdgeInsets.all(36),
          build: (_) => _cover(
            template: template,
            primary: primary,
            secondary: secondary,
            auditarLogo: auditarLogo,
            companyLogo: companyLogo,
            company: company,
            sector: sector,
            worksite: worksite,
            dateText: dateText,
            reportNumber: reportNumber,
            executive: executive,
          ),
        ),
      );
    }

    final widgets = <pw.Widget>[];
    if (template.showSummary) {
      widgets.addAll([
        _sectionTitle('Resumo da vistoria', primary),
        pw.SizedBox(height: 8),
        _summaryGrid(
          conformity: conformity,
          conformes: conformes,
          parciais: parciais,
          naoConformes: naoConformes,
          primary: primary,
          secondary: secondary,
        ),
        pw.SizedBox(height: 16),
      ]);
    }

    widgets.add(_sectionTitle('Pontos de atenção', primary));
    widgets.add(pw.SizedBox(height: 8));
    if (issueData.isEmpty) {
      widgets.add(_notice('Nenhuma não conformidade ou situação parcial registrada nesta vistoria.', secondary));
    } else {
      for (var i = 0; i < issueData.length; i++) {
        widgets.add(_issueBlock(
          i + 1,
          issueData[i],
          template,
          primary,
          secondary,
          includePlan,
          executive,
        ));
        widgets.add(pw.SizedBox(height: 12));
      }
    }

    if (includePlan && actions.isNotEmpty) {
      widgets.add(pw.SizedBox(height: 4));
      widgets.add(_sectionTitle('Plano de ação', primary));
      widgets.add(pw.SizedBox(height: 8));
      for (final action in actions) {
        widgets.add(_actionBlock(action, primary));
        widgets.add(pw.SizedBox(height: 7));
      }
    }

    if (!executive && template.showChecklistDetails) {
      widgets.add(pw.SizedBox(height: 6));
      widgets.add(_sectionTitle('Checklist da vistoria', primary));
      widgets.add(pw.SizedBox(height: 8));
      for (final answer in answers) {
        widgets.add(_checklistLine(answer, primary));
      }
    }

    final customConclusion = '${header['conclusion'] ?? ''}'.trim();
    widgets.addAll([
      pw.SizedBox(height: 12),
      _sectionTitle('Conclusão', primary),
      pw.SizedBox(height: 7),
      pw.Text(
        customConclusion.isNotEmpty
            ? customConclusion
            : _automaticConclusion(naoConformes, parciais, conformity),
        style: const pw.TextStyle(fontSize: 10.5, lineSpacing: 2.2),
      ),
    ]);

    if (template.signatureStyle != 'ocultar') {
      widgets.addAll([
        pw.SizedBox(height: 24),
        _signatures(
          header: header,
          style: template.signatureStyle,
          techSignature: techSignature,
          responsibleSignature: responsibleSignature,
          primary: primary,
        ),
      ]);
    }

    doc.addPage(
      pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(34, 36, 34, 34),
        header: (_) => _pageHeader(
          template: template,
          primary: primary,
          auditarLogo: auditarLogo,
          companyLogo: companyLogo,
          company: company,
          reportNumber: reportNumber,
        ),
        footer: (context) => _footer(template, context, primary),
        build: (_) => widgets,
      ),
    );

    return doc.save();
  }

  static pw.Widget _cover({
    required ReportTemplateDefinition template,
    required PdfColor primary,
    required PdfColor secondary,
    required pw.MemoryImage? auditarLogo,
    required pw.MemoryImage? companyLogo,
    required String company,
    required String sector,
    required String worksite,
    required String dateText,
    required String reportNumber,
    required bool executive,
  }) {
    return pw.Column(
      crossAxisAlignment: pw.CrossAxisAlignment.stretch,
      children: [
        _logos(template.logoMode, auditarLogo, companyLogo, 58),
        pw.Spacer(),
        pw.Container(width: 68, height: 6, color: secondary),
        pw.SizedBox(height: 18),
        pw.Text(
          executive ? 'RELATÓRIO EXECUTIVO' : template.headerTitle,
          style: pw.TextStyle(fontSize: 25, fontWeight: pw.FontWeight.bold, color: primary),
        ),
        pw.SizedBox(height: 10),
        pw.Text(company, style: pw.TextStyle(fontSize: 18, fontWeight: pw.FontWeight.bold)),
        pw.SizedBox(height: 22),
        _coverLine('Setor / área', sector),
        if (worksite.isNotEmpty) _coverLine('Local / unidade', worksite),
        _coverLine('Data da vistoria', dateText),
        if (reportNumber.isNotEmpty) _coverLine('Relatório', reportNumber),
        pw.Spacer(),
        pw.Container(
          padding: const pw.EdgeInsets.all(14),
          decoration: pw.BoxDecoration(
            color: PdfColors.grey100,
            border: pw.Border(left: pw.BorderSide(color: primary, width: 4)),
          ),
          child: pw.Text(
            template.description,
            style: const pw.TextStyle(fontSize: 10, lineSpacing: 2),
          ),
        ),
      ],
    );
  }

  static pw.Widget _coverLine(String label, String value) => pw.Padding(
        padding: const pw.EdgeInsets.only(bottom: 7),
        child: pw.Row(children: [
          pw.SizedBox(width: 108, child: pw.Text(label, style: pw.TextStyle(fontSize: 9, fontWeight: pw.FontWeight.bold, color: PdfColors.grey700))),
          pw.Expanded(child: pw.Text(value.isEmpty ? '-' : value, style: const pw.TextStyle(fontSize: 10.5))),
        ]),
      );

  static pw.Widget _pageHeader({
    required ReportTemplateDefinition template,
    required PdfColor primary,
    required pw.MemoryImage? auditarLogo,
    required pw.MemoryImage? companyLogo,
    required String company,
    required String reportNumber,
  }) {
    final compact = template.headerStyle == 'compacto';
    return pw.Container(
      margin: const pw.EdgeInsets.only(bottom: 14),
      padding: pw.EdgeInsets.only(bottom: compact ? 6 : 9),
      decoration: pw.BoxDecoration(border: pw.Border(bottom: pw.BorderSide(color: primary, width: compact ? 1 : 2))),
      child: pw.Row(
        crossAxisAlignment: pw.CrossAxisAlignment.center,
        children: [
          pw.SizedBox(width: compact ? 74 : 90, child: _logos(template.logoMode, auditarLogo, companyLogo, compact ? 25 : 32)),
          pw.SizedBox(width: 10),
          pw.Expanded(
            child: pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text(template.headerTitle, style: pw.TextStyle(fontSize: compact ? 10 : 12, fontWeight: pw.FontWeight.bold, color: primary)),
                pw.SizedBox(height: 2),
                pw.Text(company, style: const pw.TextStyle(fontSize: 8.5)),
              ],
            ),
          ),
          if (reportNumber.isNotEmpty) pw.Text(reportNumber, style: pw.TextStyle(fontSize: 8, color: PdfColors.grey700)),
        ],
      ),
    );
  }

  static pw.Widget _logos(String mode, pw.MemoryImage? auditar, pw.MemoryImage? client, double height) {
    final items = <pw.Widget>[];
    if ((mode == 'auditar' || mode == 'ambas') && auditar != null) {
      items.add(pw.Image(auditar, height: height, fit: pw.BoxFit.contain));
    }
    if ((mode == 'cliente' || mode == 'ambas') && client != null) {
      if (items.isNotEmpty) items.add(pw.SizedBox(width: 12));
      items.add(pw.Image(client, height: height, fit: pw.BoxFit.contain));
    }
    if (items.isEmpty) return pw.SizedBox(height: height);
    return pw.Row(mainAxisSize: pw.MainAxisSize.min, children: items);
  }

  static pw.Widget _summaryGrid({
    required int conformity,
    required int conformes,
    required int parciais,
    required int naoConformes,
    required PdfColor primary,
    required PdfColor secondary,
  }) {
    return pw.Row(children: [
      _metric('$conformity%', 'Conformidade', primary),
      pw.SizedBox(width: 7),
      _metric('$naoConformes', 'Não conformes', PdfColors.red700),
      pw.SizedBox(width: 7),
      _metric('$parciais', 'Parciais', PdfColors.orange700),
      pw.SizedBox(width: 7),
      _metric('$conformes', 'Conformes', secondary),
    ]);
  }

  static pw.Widget _metric(String value, String label, PdfColor color) => pw.Expanded(
        child: pw.Container(
          padding: const pw.EdgeInsets.symmetric(vertical: 10, horizontal: 8),
          decoration: pw.BoxDecoration(color: PdfColors.grey100, border: pw.Border(top: pw.BorderSide(color: color, width: 3))),
          child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
            pw.Text(value, style: pw.TextStyle(fontSize: 17, fontWeight: pw.FontWeight.bold, color: color)),
            pw.Text(label, style: const pw.TextStyle(fontSize: 7.5)),
          ]),
        ),
      );

  static pw.Widget _sectionTitle(String text, PdfColor color) => pw.Text(
        text,
        style: pw.TextStyle(fontSize: 14, fontWeight: pw.FontWeight.bold, color: color),
      );

  static pw.Widget _issueBlock(
    int number,
    _IssueData data,
    ReportTemplateDefinition template,
    PdfColor primary,
    PdfColor secondary,
    bool includePlan,
    bool executive,
  ) {
    final a = data.answer;
    final action = data.actions.isEmpty ? null : data.actions.first;
    final priority = (action?.priority.trim().isNotEmpty == true)
        ? action!.priority.trim()
        : (data.nc?.classification.trim().isNotEmpty == true ? data.nc!.classification.trim() : 'Média');
    final problem = a.observation.trim().isNotEmpty ? a.observation.trim() : (data.nc?.description.trim() ?? 'Situação registrada em campo.');
    final risk = a.riskIdentified.trim().isNotEmpty ? a.riskIdentified.trim() : (data.nc?.riskIdentified.trim() ?? 'Avaliar risco associado à situação encontrada.');
    final recommendation = a.recommendation.trim().isNotEmpty ? a.recommendation.trim() : (data.nc?.recommendation.trim() ?? 'Providenciar adequação conforme avaliação técnica.');
    final reference = a.questionReference.trim();

    return pw.Container(
      padding: const pw.EdgeInsets.all(11),
      decoration: pw.BoxDecoration(border: pw.Border.all(color: PdfColors.grey300, width: .8)),
      child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
        pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.Container(
            width: 27,
            height: 27,
            alignment: pw.Alignment.center,
            decoration: pw.BoxDecoration(color: primary, shape: pw.BoxShape.circle),
            child: pw.Text('$number', style: pw.TextStyle(color: PdfColors.white, fontWeight: pw.FontWeight.bold, fontSize: 9)),
          ),
          pw.SizedBox(width: 8),
          pw.Expanded(child: pw.Text(a.questionText, style: pw.TextStyle(fontSize: 11, fontWeight: pw.FontWeight.bold, color: primary))),
          pw.SizedBox(width: 6),
          _priorityChip(priority),
        ]),
        pw.SizedBox(height: 9),
        _labelValue('Situação encontrada', problem),
        _labelValue('Risco', risk),
        _labelValue('Correção recomendada', recommendation),
        if (reference.isNotEmpty) _labelValue('Referência', reference),
        if (includePlan && action != null) ...[
          _labelValue('Ação definida', action.correctiveAction),
          _labelValue('Responsável', action.responsible.isEmpty ? '-' : action.responsible),
          _labelValue('Prazo', action.dueDate == null ? '-' : DateFormat('dd/MM/yyyy').format(action.dueDate!)),
        ],
        if (data.photos.isNotEmpty) ...[
          pw.SizedBox(height: 8),
          _photos(data.photos, template.photoColumns, primary),
        ],
      ]),
    );
  }

  static pw.Widget _photos(List<pw.MemoryImage> images, int columns, PdfColor primary) {
    final cols = columns.clamp(1, 3);
    final width = cols == 1 ? 490.0 : (cols == 2 ? 241.0 : 158.0);
    final height = cols == 1 ? 235.0 : (cols == 2 ? 150.0 : 105.0);
    return pw.Wrap(
      spacing: 7,
      runSpacing: 7,
      children: images.map((image) => pw.Container(
        width: width,
        height: height,
        decoration: pw.BoxDecoration(border: pw.Border.all(color: primary, width: .5)),
        child: pw.Image(image, fit: pw.BoxFit.cover),
      )).toList(),
    );
  }

  static pw.Widget _priorityChip(String value) {
    final normalized = value.toLowerCase();
    final color = normalized.contains('alta') || normalized.contains('grave') || normalized.contains('imedi')
        ? PdfColors.red700
        : normalized.contains('baixa')
            ? PdfColors.green700
            : PdfColors.orange700;
    return pw.Container(
      padding: const pw.EdgeInsets.symmetric(horizontal: 7, vertical: 4),
      decoration: pw.BoxDecoration(color: color),
      child: pw.Text(value.toUpperCase(), style: pw.TextStyle(color: PdfColors.white, fontSize: 6.5, fontWeight: pw.FontWeight.bold)),
    );
  }

  static pw.Widget _labelValue(String label, String value) => pw.Padding(
        padding: const pw.EdgeInsets.only(bottom: 5),
        child: pw.RichText(
          text: pw.TextSpan(children: [
            pw.TextSpan(text: '$label: ', style: pw.TextStyle(fontSize: 9, fontWeight: pw.FontWeight.bold)),
            pw.TextSpan(text: value.trim().isEmpty ? '-' : value.trim(), style: const pw.TextStyle(fontSize: 9)),
          ]),
        ),
      );

  static pw.Widget _actionBlock(ActionPlan action, PdfColor primary) => pw.Container(
        padding: const pw.EdgeInsets.all(9),
        decoration: const pw.BoxDecoration(color: PdfColors.grey100),
        child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.Text(action.nonConformity, style: pw.TextStyle(fontSize: 9.5, fontWeight: pw.FontWeight.bold, color: primary)),
          pw.SizedBox(height: 4),
          pw.Text(action.correctiveAction, style: const pw.TextStyle(fontSize: 9)),
          pw.SizedBox(height: 4),
          pw.Text('Responsável: ${action.responsible.isEmpty ? '-' : action.responsible}  •  Prioridade: ${action.priority}  •  Status: ${action.status}', style: pw.TextStyle(fontSize: 7.5, color: PdfColors.grey700)),
        ]),
      );

  static pw.Widget _checklistLine(InspectionAnswer answer, PdfColor primary) {
    final statusColor = answer.status == 'Conforme'
        ? PdfColors.green700
        : answer.status == 'Não Conforme'
            ? PdfColors.red700
            : answer.status == 'Parcial'
                ? PdfColors.orange700
                : PdfColors.grey600;
    return pw.Container(
      padding: const pw.EdgeInsets.symmetric(vertical: 5),
      decoration: const pw.BoxDecoration(border: pw.Border(bottom: pw.BorderSide(color: PdfColors.grey300, width: .5))),
      child: pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
        pw.Container(width: 64, child: pw.Text(answer.status, style: pw.TextStyle(fontSize: 7.5, fontWeight: pw.FontWeight.bold, color: statusColor))),
        pw.SizedBox(width: 7),
        pw.Expanded(child: pw.Text(answer.questionText, style: const pw.TextStyle(fontSize: 8.5))),
      ]),
    );
  }

  static pw.Widget _notice(String text, PdfColor accent) => pw.Container(
        padding: const pw.EdgeInsets.all(11),
        decoration: pw.BoxDecoration(color: PdfColors.grey100, border: pw.Border(left: pw.BorderSide(color: accent, width: 3))),
        child: pw.Text(text, style: const pw.TextStyle(fontSize: 9.5)),
      );

  static pw.Widget _signatures({
    required Map<String, Object?> header,
    required String style,
    required pw.MemoryImage? techSignature,
    required pw.MemoryImage? responsibleSignature,
    required PdfColor primary,
  }) {
    final tech = '${header['technician_name'] ?? ''}'.trim();
    final responsible = '${header['responsible_name'] ?? ''}'.trim();
    pw.Widget box(String name, String label, pw.MemoryImage? image) {
      return pw.Expanded(
        child: pw.Column(children: [
          pw.SizedBox(height: 48, child: style == 'app' && image != null ? pw.Image(image, fit: pw.BoxFit.contain) : null),
          pw.Container(height: .8, color: primary),
          pw.SizedBox(height: 4),
          pw.Text(name.isEmpty ? label : name, style: pw.TextStyle(fontSize: 8.5, fontWeight: pw.FontWeight.bold)),
          pw.Text(label, style: pw.TextStyle(fontSize: 7, color: PdfColors.grey700)),
        ]),
      );
    }
    return pw.Row(children: [
      box(tech, 'Responsável técnico', techSignature),
      pw.SizedBox(width: 26),
      box(responsible, 'Responsável da empresa', responsibleSignature),
    ]);
  }

  static pw.Widget _footer(ReportTemplateDefinition template, pw.Context context, PdfColor primary) => pw.Container(
        padding: const pw.EdgeInsets.only(top: 6),
        decoration: pw.BoxDecoration(border: pw.Border(top: pw.BorderSide(color: PdfColors.grey300, width: .5))),
        child: pw.Row(children: [
          pw.Expanded(child: pw.Text(template.footerText, style: pw.TextStyle(fontSize: 6.8, color: PdfColors.grey600))),
          pw.Text('${context.pageNumber}/${context.pagesCount}', style: pw.TextStyle(fontSize: 6.8, color: primary)),
        ]),
      );

  static String _automaticConclusion(int nc, int partial, int conformity) {
    if (nc == 0 && partial == 0) {
      return 'A vistoria não registrou não conformidades ou itens parciais. Manter os controles existentes e o acompanhamento preventivo.';
    }
    return 'A vistoria registrou $nc não conformidade(s) e $partial item(ns) parcial(is), com índice de conformidade de $conformity%. Recomenda-se priorizar as correções indicadas, registrar as evidências de conclusão e verificar a eficácia das medidas adotadas.';
  }

  static PdfColor _color(String hex, PdfColor fallback) {
    try {
      final clean = hex.replaceAll('#', '').trim();
      if (clean.length != 6) return fallback;
      final value = int.parse(clean, radix: 16);
      return PdfColor(
        ((value >> 16) & 0xFF) / 255,
        ((value >> 8) & 0xFF) / 255,
        (value & 0xFF) / 255,
      );
    } catch (_) {
      return fallback;
    }
  }

  static Future<pw.MemoryImage?> _assetImage(String asset) async {
    try {
      final data = await rootBundle.load(asset);
      return pw.MemoryImage(data.buffer.asUint8List());
    } catch (_) {
      return null;
    }
  }

  static Future<pw.MemoryImage?> _fileImage(String path) async {
    if (path.trim().isEmpty) return null;
    try {
      final file = File(path);
      if (!await file.exists()) return null;
      final bytes = await file.readAsBytes();
      if (bytes.isEmpty) return null;
      return pw.MemoryImage(bytes);
    } catch (_) {
      return null;
    }
  }
}

class _IssueData {
  final InspectionAnswer answer;
  final NonConformity? nc;
  final List<ActionPlan> actions;
  final List<pw.MemoryImage> photos;

  const _IssueData({
    required this.answer,
    required this.nc,
    required this.actions,
    required this.photos,
  });
}
''')

write('lib/screens/report_template_library_screen.dart', r'''
import 'dart:io';

import 'package:flutter/material.dart';

import '../brand.dart';
import '../services/report_template_service.dart';

class ReportTemplateLibraryScreen extends StatefulWidget {
  final String? companyId;

  const ReportTemplateLibraryScreen({super.key, this.companyId});

  @override
  State<ReportTemplateLibraryScreen> createState() => _ReportTemplateLibraryScreenState();
}

class _ReportTemplateLibraryScreenState extends State<ReportTemplateLibraryScreen> {
  bool loading = true;
  List<ReportTemplateDefinition> templates = const [];
  String selectedId = ReportTemplateService.currentTemplateId;

  bool get canSelect => (widget.companyId ?? '').trim().isNotEmpty;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final all = await ReportTemplateService.getAllTemplates();
    var selected = ReportTemplateService.currentTemplate;
    if (canSelect) {
      selected = await ReportTemplateService.selectedForCompany(widget.companyId!);
    }
    if (!mounted) return;
    setState(() {
      templates = all;
      selectedId = selected.id;
      loading = false;
    });
  }

  Future<void> _select(ReportTemplateDefinition template) async {
    if (!canSelect) return;
    await ReportTemplateService.selectForCompany(widget.companyId!, template.id);
    if (!mounted) return;
    setState(() => selectedId = template.id);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Modelo "${template.name}" selecionado para esta empresa.')),
    );
  }

  Future<void> _customize(ReportTemplateDefinition template) async {
    final result = await showDialog<ReportTemplateDefinition>(
      context: context,
      barrierDismissible: false,
      builder: (_) => _TemplateEditorDialog(base: template, fullEditor: Platform.isWindows),
    );
    if (result == null) return;
    await ReportTemplateService.saveCustom(result);
    if (canSelect) {
      await ReportTemplateService.selectForCompany(widget.companyId!, result.id);
    }
    await _load();
  }

  Future<void> _create() async {
    final base = ReportTemplateService.builtIns[1];
    await _customize(base.copyWith(name: 'Meu modelo de relatório'));
  }

  Future<void> _delete(ReportTemplateDefinition template) async {
    if (template.isBuiltIn) return;
    final yes = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Excluir modelo?'),
        content: Text('O modelo "${template.name}" será removido somente deste dispositivo.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Excluir')),
        ],
      ),
    );
    if (yes != true) return;
    await ReportTemplateService.deleteCustom(template.id);
    if (selectedId == template.id && canSelect) {
      await ReportTemplateService.selectForCompany(widget.companyId!, ReportTemplateService.currentTemplateId);
    }
    await _load();
  }

  void _preview(ReportTemplateDefinition template) {
    showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: Text(template.name),
        content: SizedBox(width: 520, child: _templatePreview(template, large: true)),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Fechar'))],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Modelos de relatório'),
        backgroundColor: AuditarBrand.navyDark,
        foregroundColor: Colors.white,
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _create,
        icon: const Icon(Icons.add),
        label: Text(Platform.isWindows ? 'Criar modelo' : 'Novo modelo'),
      ),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 90),
              children: [
                Card(
                  elevation: 0,
                  color: AuditarBrand.navySoft.withOpacity(.55),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Text(
                      Platform.isWindows
                          ? 'No computador você pode criar, personalizar e salvar novos modelos. O modelo atual continua intacto e sempre disponível.'
                          : 'No celular você pode escolher modelos e fazer ajustes básicos. O modelo atual continua intacto e sempre disponível.',
                      style: const TextStyle(height: 1.35),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                ...templates.map((template) => _templateCard(template)),
              ],
            ),
    );
  }

  Widget _templateCard(ReportTemplateDefinition template) {
    final selected = selectedId == template.id;
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      elevation: selected ? 2 : 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: selected ? AuditarBrand.green : Colors.grey.shade300, width: selected ? 1.5 : 1),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(width: 150, child: _templatePreview(template)),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        Expanded(child: Text(template.name, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800))),
                        if (selected) const Chip(label: Text('Selecionado')),
                      ]),
                      const SizedBox(height: 4),
                      Text(template.description, style: TextStyle(color: Colors.grey.shade700, height: 1.3)),
                      const SizedBox(height: 8),
                      Wrap(spacing: 7, runSpacing: 6, children: [
                        _smallChip(template.showCover ? 'Com capa' : 'Sem capa'),
                        _smallChip('${template.photoColumns} foto${template.photoColumns > 1 ? 's' : ''} por linha'),
                        _smallChip(_logoLabel(template.logoMode)),
                      ]),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                OutlinedButton.icon(onPressed: () => _preview(template), icon: const Icon(Icons.visibility_outlined), label: const Text('Pré-visualizar')),
                OutlinedButton.icon(onPressed: () => _customize(template), icon: const Icon(Icons.tune_rounded), label: Text(template.isBuiltIn ? 'Personalizar' : 'Salvar variação')),
                if (canSelect)
                  FilledButton.icon(
                    onPressed: selected ? null : () => _select(template),
                    icon: const Icon(Icons.check_circle_outline),
                    label: Text(selected ? 'Em uso' : 'Usar este modelo'),
                  ),
                if (!template.isBuiltIn)
                  IconButton(onPressed: () => _delete(template), tooltip: 'Excluir modelo', icon: const Icon(Icons.delete_outline)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _smallChip(String text) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(99)),
        child: Text(text, style: const TextStyle(fontSize: 11)),
      );

  String _logoLabel(String mode) {
    if (mode == 'auditar') return 'Logo Auditar';
    if (mode == 'cliente') return 'Logo cliente';
    if (mode == 'nenhuma') return 'Sem logo';
    return 'Duas logos';
  }

  Widget _templatePreview(ReportTemplateDefinition template, {bool large = false}) {
    final primary = _hexColor(template.primaryColor, AuditarBrand.navyDark);
    final secondary = _hexColor(template.secondaryColor, AuditarBrand.green);
    return AspectRatio(
      aspectRatio: .72,
      child: Container(
        padding: EdgeInsets.all(large ? 18 : 9),
        decoration: BoxDecoration(color: Colors.white, border: Border.all(color: Colors.grey.shade300), borderRadius: BorderRadius.circular(8)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              Container(width: large ? 42 : 22, height: large ? 22 : 12, decoration: BoxDecoration(color: primary, borderRadius: BorderRadius.circular(2))),
              const Spacer(),
              Container(width: large ? 34 : 18, height: large ? 22 : 12, decoration: BoxDecoration(color: secondary.withOpacity(.28), borderRadius: BorderRadius.circular(2))),
            ]),
            SizedBox(height: large ? 18 : 9),
            Container(width: double.infinity, height: large ? 7 : 4, color: primary),
            SizedBox(height: large ? 7 : 4),
            Container(width: large ? 180 : 92, height: large ? 7 : 4, color: Colors.grey.shade300),
            SizedBox(height: large ? 20 : 10),
            Row(children: List.generate(3, (index) => Expanded(child: Container(margin: const EdgeInsets.only(right: 3), height: large ? 38 : 20, color: index == 0 ? secondary.withOpacity(.18) : Colors.grey.shade100)))),
            SizedBox(height: large ? 14 : 7),
            Container(width: large ? 120 : 65, height: large ? 6 : 3, color: primary),
            SizedBox(height: large ? 8 : 4),
            Expanded(child: Container(width: double.infinity, color: Colors.grey.shade100)),
          ],
        ),
      ),
    );
  }

  Color _hexColor(String hex, Color fallback) {
    try {
      final clean = hex.replaceAll('#', '');
      return Color(int.parse('FF$clean', radix: 16));
    } catch (_) {
      return fallback;
    }
  }
}

class _TemplateEditorDialog extends StatefulWidget {
  final ReportTemplateDefinition base;
  final bool fullEditor;

  const _TemplateEditorDialog({required this.base, required this.fullEditor});

  @override
  State<_TemplateEditorDialog> createState() => _TemplateEditorDialogState();
}

class _TemplateEditorDialogState extends State<_TemplateEditorDialog> {
  late final TextEditingController name;
  late final TextEditingController title;
  late final TextEditingController footer;
  late final TextEditingController primary;
  late String logoMode;
  late String headerStyle;
  late String signatureStyle;
  late int photoColumns;
  late bool showCover;
  late bool showSummary;
  late bool showChecklistDetails;

  @override
  void initState() {
    super.initState();
    final b = widget.base;
    name = TextEditingController(text: b.isBuiltIn ? '${b.name} personalizado' : b.name);
    title = TextEditingController(text: b.headerTitle);
    footer = TextEditingController(text: b.footerText);
    primary = TextEditingController(text: b.primaryColor);
    logoMode = b.logoMode;
    headerStyle = b.headerStyle;
    signatureStyle = b.signatureStyle;
    photoColumns = b.photoColumns;
    showCover = b.showCover;
    showSummary = b.showSummary;
    showChecklistDetails = b.showChecklistDetails;
  }

  @override
  void dispose() {
    name.dispose();
    title.dispose();
    footer.dispose();
    primary.dispose();
    super.dispose();
  }

  void _save() {
    if (name.text.trim().isEmpty) return;
    Navigator.pop(
      context,
      widget.base.copyWith(
        id: ReportTemplateService.newCustomId(),
        name: name.text.trim(),
        description: 'Modelo personalizado pelo usuário.',
        primaryColor: primary.text.trim().isEmpty ? widget.base.primaryColor : primary.text.trim(),
        headerTitle: title.text.trim().isEmpty ? widget.base.headerTitle : title.text.trim(),
        footerText: footer.text.trim(),
        logoMode: logoMode,
        headerStyle: headerStyle,
        signatureStyle: signatureStyle,
        photoColumns: photoColumns,
        showCover: showCover,
        showSummary: showSummary,
        showChecklistDetails: showChecklistDetails,
        isBuiltIn: false,
        useLegacyRenderer: false,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final full = widget.fullEditor;
    return AlertDialog(
      title: Text(full ? 'Editor de modelo' : 'Ajustes do modelo'),
      content: SizedBox(
        width: full ? 620 : 430,
        child: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: name, decoration: const InputDecoration(labelText: 'Nome do modelo')),
              const SizedBox(height: 10),
              TextField(controller: title, decoration: const InputDecoration(labelText: 'Título do cabeçalho')),
              const SizedBox(height: 10),
              if (full)
                TextField(controller: primary, decoration: const InputDecoration(labelText: 'Cor principal', hintText: '#0B2E4F'))
              else
                DropdownButtonFormField<String>(
                  value: const ['#0B2E4F', '#157A46', '#D97706', '#1F2937', '#B91C1C'].contains(primary.text.toUpperCase()) ? primary.text.toUpperCase() : '#0B2E4F',
                  decoration: const InputDecoration(labelText: 'Cor principal'),
                  items: const [
                    DropdownMenuItem(value: '#0B2E4F', child: Text('Azul Auditar')),
                    DropdownMenuItem(value: '#157A46', child: Text('Verde')),
                    DropdownMenuItem(value: '#D97706', child: Text('Laranja obra')),
                    DropdownMenuItem(value: '#1F2937', child: Text('Cinza técnico')),
                    DropdownMenuItem(value: '#B91C1C', child: Text('Vermelho NR-12')),
                  ],
                  onChanged: (value) => primary.text = value ?? '#0B2E4F',
                ),
              const SizedBox(height: 10),
              DropdownButtonFormField<String>(
                value: logoMode,
                decoration: const InputDecoration(labelText: 'Logos no cabeçalho'),
                items: const [
                  DropdownMenuItem(value: 'ambas', child: Text('Auditar + cliente')),
                  DropdownMenuItem(value: 'auditar', child: Text('Somente Auditar')),
                  DropdownMenuItem(value: 'cliente', child: Text('Somente cliente')),
                  DropdownMenuItem(value: 'nenhuma', child: Text('Sem logos')),
                ],
                onChanged: (value) => setState(() => logoMode = value ?? 'ambas'),
              ),
              const SizedBox(height: 10),
              DropdownButtonFormField<int>(
                value: photoColumns,
                decoration: const InputDecoration(labelText: 'Fotos por linha'),
                items: const [
                  DropdownMenuItem(value: 1, child: Text('1 foto grande')),
                  DropdownMenuItem(value: 2, child: Text('2 fotos')),
                  DropdownMenuItem(value: 3, child: Text('3 fotos compactas')),
                ],
                onChanged: (value) => setState(() => photoColumns = value ?? 2),
              ),
              if (full) ...[
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: headerStyle,
                  decoration: const InputDecoration(labelText: 'Estilo do cabeçalho'),
                  items: const [
                    DropdownMenuItem(value: 'classico', child: Text('Clássico')),
                    DropdownMenuItem(value: 'compacto', child: Text('Compacto')),
                    DropdownMenuItem(value: 'impacto', child: Text('Destaque')),
                  ],
                  onChanged: (value) => setState(() => headerStyle = value ?? 'classico'),
                ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: signatureStyle,
                  decoration: const InputDecoration(labelText: 'Assinaturas'),
                  items: const [
                    DropdownMenuItem(value: 'app', child: Text('Usar assinaturas do app')),
                    DropdownMenuItem(value: 'linhas', child: Text('Linhas para assinatura')),
                    DropdownMenuItem(value: 'ocultar', child: Text('Ocultar assinaturas')),
                  ],
                  onChanged: (value) => setState(() => signatureStyle = value ?? 'app'),
                ),
                const SizedBox(height: 10),
                TextField(controller: footer, maxLines: 2, decoration: const InputDecoration(labelText: 'Rodapé')),
              ],
              SwitchListTile.adaptive(contentPadding: EdgeInsets.zero, value: showCover, title: const Text('Incluir capa'), onChanged: (value) => setState(() => showCover = value)),
              SwitchListTile.adaptive(contentPadding: EdgeInsets.zero, value: showSummary, title: const Text('Incluir resumo visual'), onChanged: (value) => setState(() => showSummary = value)),
              if (full)
                SwitchListTile.adaptive(contentPadding: EdgeInsets.zero, value: showChecklistDetails, title: const Text('Incluir checklist detalhado'), onChanged: (value) => setState(() => showChecklistDetails = value)),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
        FilledButton.icon(onPressed: _save, icon: const Icon(Icons.save_outlined), label: const Text('Salvar como novo modelo')),
      ],
    );
  }
}
''')

# report_screen.dart: apenas camada visual de seleção; não toca em sync/drive.
report_screen = root / 'lib/screens/report_screen.dart'
replace_once(
    report_screen,
    "import '../services/report_file_service.dart';\n",
    "import '../services/report_file_service.dart';\nimport '../services/report_template_service.dart';\n",
    'import report template service',
)
replace_once(
    report_screen,
    "import 'non_conformities_screen.dart';\n",
    "import 'non_conformities_screen.dart';\nimport 'report_template_library_screen.dart';\n",
    'import template screen',
)
replace_once(
    report_screen,
    "  String driveStatus = '';\n",
    "  String driveStatus = '';\n  String reportCompanyId = '';\n  ReportTemplateDefinition selectedReportTemplate = ReportTemplateService.currentTemplate;\n",
    'report template state',
)
replace_once(
    report_screen,
    "    final existing = await db.getDriveUploadForInspection(widget.inspectionId);\n\n    if (!mounted) return;\n",
    "    final existing = await db.getDriveUploadForInspection(widget.inspectionId);\n    final template = await ReportTemplateService.resolveForHeader(header);\n\n    if (!mounted) return;\n",
    'load selected template',
)
replace_once(
    report_screen,
    "      reportSignatureMode = signatureMode.isEmpty ? 'app' : signatureMode;\n\n      if (existing != null) {\n",
    "      reportSignatureMode = signatureMode.isEmpty ? 'app' : signatureMode;\n      reportCompanyId = '${header?['company_id'] ?? ''}'.trim();\n      selectedReportTemplate = template;\n\n      if (existing != null) {\n",
    'assign selected template',
)
method_anchor = "  Future<void> _sharePdf({required bool executive}) async {\n"
method_code = r'''  Future<void> _openReportTemplateLibrary() async {
    if (reportCompanyId.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Empresa da vistoria não identificada.')),
      );
      return;
    }
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ReportTemplateLibraryScreen(companyId: reportCompanyId),
      ),
    );
    final template = await ReportTemplateService.selectedForCompany(reportCompanyId);
    if (!mounted) return;
    setState(() => selectedReportTemplate = template);
  }

'''
replace_once(report_screen, method_anchor, method_code + method_anchor, 'open library method')
ui_anchor = "          const SizedBox(height: 18),\n          const Text(\n            'Escolha o formato',\n"
ui_code = r'''          const SizedBox(height: 18),
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: BorderSide(color: AuditarBrand.navyDark.withOpacity(.18)),
            ),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: AuditarBrand.navySoft,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.dashboard_customize_outlined, color: AuditarBrand.navyDark),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Modelo visual do relatório', style: TextStyle(fontWeight: FontWeight.w800, color: AuditarBrand.navyDark)),
                        const SizedBox(height: 3),
                        Text(selectedReportTemplate.name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700)),
                        Text(selectedReportTemplate.description, style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),
                  OutlinedButton.icon(
                    onPressed: _openReportTemplateLibrary,
                    icon: const Icon(Icons.swap_horiz_rounded),
                    label: const Text('Escolher'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 18),
          const Text(
            'Escolha o formato',
'''
replace_once(report_screen, ui_anchor, ui_code, 'report model card')

# settings: atalho da biblioteca. Nenhum serviço de sync é importado/modificado.
settings = root / 'lib/screens/settings_screen.dart'
replace_once(
    settings,
    "import 'login_screen.dart';\n",
    "import 'login_screen.dart';\nimport 'report_template_library_screen.dart';\n",
    'settings import library',
)
settings_anchor = "          const SizedBox(height: 16),\n          FilledButton.icon(\n            onPressed: _save,\n"
settings_code = r'''          const SizedBox(height: 14),
          OutlinedButton.icon(
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute(builder: (_) => const ReportTemplateLibraryScreen()),
            ),
            icon: const Icon(Icons.dashboard_customize_outlined),
            label: Text(
              Platform.isWindows
                  ? 'Biblioteca e editor de modelos de relatório'
                  : 'Modelos de relatório',
            ),
          ),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _save,
'''
replace_once(settings, settings_anchor, settings_code, 'settings library button')

# PdfService: fallback preserva integralmente o gerador atual.
pdf = root / 'lib/services/pdf_service.dart'
replace_once(
    pdf,
    'class PdfService {\n',
    "import 'report_template_service.dart';\nimport 'styled_report_pdf_service.dart';\n\nclass PdfService {\n",
    'pdf service imports',
)
pdf_anchor = "    final answers = await db.getAnswers(inspectionId);\n"
pdf_code = r'''    final reportTemplate = await ReportTemplateService.resolveForHeader(header);
    if (!reportTemplate.useLegacyRenderer) {
      return StyledReportPdfService.generateInspectionPdf(
        inspectionId,
        header: header,
        template: reportTemplate,
        executive: executive,
        includeActionPlan: includeActionPlan,
      );
    }

    final answers = await db.getAnswers(inspectionId);
'''
replace_once(pdf, pdf_anchor, pdf_code, 'pdf template routing')

# Versão isolada da biblioteca de relatórios.
pubspec = root / 'pubspec.yaml'
text = pubspec.read_text(encoding='utf-8')
text, count = re.subn(r'^version:\s*[^\n]+', 'version: 3.29.62+204', text, count=1, flags=re.M)
if count != 1:
    raise SystemExit('version não encontrada no pubspec')
pubspec.write_text(text, encoding='utf-8')

# Guardas: esta atualização não deve tocar no núcleo de sincronização.
for forbidden in [
    'lib/services/device_sync_service.dart',
    'lib/services/media_sync_service.dart',
    'lib/services/auth_service.dart',
    'lib/services/drive_service.dart',
    'lib/database.dart',
]:
    if not (root / forbidden).exists():
        raise SystemExit(f'arquivo essencial ausente: {forbidden}')

print('v3.29.62+204: biblioteca de modelos de relatório aplicada sem alterar sincronização, mídia, login, Drive ou banco.')
