#!/usr/bin/env python3
from pathlib import Path
import re, shutil, sys

if len(sys.argv) < 2:
    raise SystemExit("uso: patch_report_template_ai_import_v32989_v33016.py <APP_DIR> [android|windows]")

root = Path(sys.argv[1])
platform = (sys.argv[2] if len(sys.argv) > 2 else "android").lower()
repo = Path.cwd()

def read(rel):
    return (root / rel).read_text(encoding="utf-8")

def write(rel, text):
    (root / rel).write_text(text, encoding="utf-8", newline="\n")

def insert_import(text, statement):
    if statement in text:
        return text
    imports = list(re.finditer(r"(?m)^import\s+[^;]+;\s*$", text))
    if not imports:
        raise RuntimeError("imports não localizados")
    pos = imports[-1].end()
    return text[:pos] + "\n" + statement + text[pos:]

src = repo / "build_sources/v3.29.89-report-template-ai/report_template_ai_import_service.dart"
dst = root / "lib/services/report_template_ai_import_service.dart"
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(src, dst)

rel = "lib/screens/report_template_library_screen.dart"
s = read(rel)
s = insert_import(s, "import 'dart:typed_data';")
s = insert_import(s, "import 'package:file_picker/file_picker.dart';")
s = insert_import(s, "import '../services/report_template_ai_import_service.dart';")

state_anchor = """  bool loading = true;
  List<ReportTemplateDefinition> templates = const [];
  String selectedId = ReportTemplateService.currentTemplateId;
"""
state_new = """  bool loading = true;
  bool importingAi = false;
  List<ReportTemplateDefinition> templates = const [];
  String selectedId = ReportTemplateService.currentTemplateId;
"""
if state_new not in s:
    if state_anchor not in s:
        raise RuntimeError("estado da biblioteca não localizado")
    s = s.replace(state_anchor, state_new, 1)

methods_anchor = """  Future<void> _create() async {
    final base = ReportTemplateService.builtIns[1];
    await _customize(base.copyWith(name: 'Meu modelo de relatório'));
  }

"""
ai_methods = r'''  Future<Uint8List?> _pickedBytes(PlatformFile file) async {
    if (file.bytes != null) return file.bytes!;
    final path = file.path;
    if (path == null || path.trim().isEmpty) return null;
    final source = File(path);
    if (!await source.exists()) return null;
    return source.readAsBytes();
  }

  Future<void> _importPdfWithAi() async {
    if (importingAi) return;

    final picked = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf'],
      allowMultiple: false,
      withData: true,
    );
    if (picked == null || picked.files.isEmpty) return;

    final file = picked.files.single;
    final bytes = await _pickedBytes(file);
    if (bytes == null || bytes.isEmpty) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Não foi possível abrir o PDF selecionado.'),
        ),
      );
      return;
    }

    setState(() => importingAi = true);
    ReportTemplateAiDraft? draft;
    Object? failure;
    try {
      draft = await ReportTemplateAiImportService.analyzePdf(
        pdfBytes: bytes,
        fileName: file.name,
      );
    } catch (error) {
      failure = error;
    } finally {
      if (mounted) setState(() => importingAi = false);
    }

    if (!mounted) return;
    if (draft == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            failure is ReportTemplateAiImportException
                ? failure.message
                : 'Não foi possível analisar o modelo: $failure',
          ),
          duration: const Duration(seconds: 7),
        ),
      );
      return;
    }

    final review = await showDialog<_AiTemplateReviewResult>(
      context: context,
      barrierDismissible: false,
      builder: (_) => _AiTemplateReviewDialog(
        draft: draft!,
        canUseForCompany: canSelect,
      ),
    );
    if (review == null) return;

    await ReportTemplateService.saveCustom(review.template);
    if (review.useForCompany && canSelect) {
      await ReportTemplateService.selectForCompany(
        widget.companyId!,
        review.template.id,
      );
    }
    await _load();
    if (!mounted) return;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          review.useForCompany && canSelect
              ? 'Modelo "${review.template.name}" salvo e definido para esta empresa.'
              : 'Modelo "${review.template.name}" salvo na biblioteca.',
        ),
      ),
    );
  }

  Widget _aiCreatorCard() {
    return Card(
      elevation: 0,
      color: const Color(0xFFF3F0FF),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFF7C3AED), width: 1),
      ),
      child: Padding(
        padding: const EdgeInsets.all(15),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.auto_awesome, color: Color(0xFF6D28D9)),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Criador de modelos com IA',
                    style: TextStyle(
                      fontSize: 17,
                      fontWeight: FontWeight.w900,
                      color: Color(0xFF31106E),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 7),
            const Text(
              'Envie um PDF de referência. A IA identifica estrutura, cores, capa, cabeçalho, fotos, resumo, conclusão e assinaturas e cria um rascunho compatível com o gerador do Auditar.',
              style: TextStyle(height: 1.35),
            ),
            const SizedBox(height: 7),
            Text(
              'Nada é cadastrado automaticamente: você revisa o resultado e confirma antes de salvar.',
              style: TextStyle(
                color: Colors.grey.shade700,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            FilledButton.icon(
              onPressed: importingAi ? null : _importPdfWithAi,
              icon: importingAi
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.picture_as_pdf_outlined),
              label: Text(
                importingAi
                    ? 'IA analisando o PDF...'
                    : 'Importar modelo em PDF com IA',
              ),
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFF6D28D9),
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }

'''
if "_importPdfWithAi()" not in s:
    if methods_anchor not in s:
        raise RuntimeError("âncora _create não localizada")
    s = s.replace(methods_anchor, methods_anchor + ai_methods, 1)

list_anchor = """                const SizedBox(height: 12),
                ...templates.map((template) => _templateCard(template)),
"""
list_new = """                const SizedBox(height: 12),
                _aiCreatorCard(),
                const SizedBox(height: 12),
                ...templates.map((template) => _templateCard(template)),
"""
if list_new not in s:
    if list_anchor not in s:
        raise RuntimeError("lista de modelos não localizada")
    s = s.replace(list_anchor, list_new, 1)

old_chips = """                        _smallChip(_logoLabel(template.logoMode)),
"""
new_chips = """                        _smallChip(_logoLabel(template.logoMode)),
                        if (template.description.contains('Importado com IA'))
                          _smallChip('Importado com IA'),
"""
if new_chips not in s:
    if old_chips not in s:
        raise RuntimeError("chips do modelo não localizados")
    s = s.replace(old_chips, new_chips, 1)

dialogs = r'''

class _AiTemplateReviewResult {
  final ReportTemplateDefinition template;
  final bool useForCompany;

  const _AiTemplateReviewResult({
    required this.template,
    required this.useForCompany,
  });
}

class _AiTemplateReviewDialog extends StatefulWidget {
  final ReportTemplateAiDraft draft;
  final bool canUseForCompany;

  const _AiTemplateReviewDialog({
    required this.draft,
    required this.canUseForCompany,
  });

  @override
  State<_AiTemplateReviewDialog> createState() =>
      _AiTemplateReviewDialogState();
}

class _AiTemplateReviewDialogState extends State<_AiTemplateReviewDialog> {
  late final TextEditingController name;
  late final TextEditingController headerTitle;
  late final TextEditingController footer;
  late final TextEditingController primary;
  late final TextEditingController secondary;
  late String headerStyle;
  late String logoMode;
  late String signatureStyle;
  late int photoColumns;
  late bool showCover;
  late bool showSummary;
  late bool showChecklistDetails;
  bool useForCompany = false;

  @override
  void initState() {
    super.initState();
    final t = widget.draft.template;
    name = TextEditingController(text: t.name);
    headerTitle = TextEditingController(text: t.headerTitle);
    footer = TextEditingController(text: t.footerText);
    primary = TextEditingController(text: t.primaryColor);
    secondary = TextEditingController(text: t.secondaryColor);
    headerStyle = t.headerStyle;
    logoMode = t.logoMode;
    signatureStyle = t.signatureStyle;
    photoColumns = t.photoColumns;
    showCover = t.showCover;
    showSummary = t.showSummary;
    showChecklistDetails = t.showChecklistDetails;
  }

  @override
  void dispose() {
    name.dispose();
    headerTitle.dispose();
    footer.dispose();
    primary.dispose();
    secondary.dispose();
    super.dispose();
  }

  Color _color(String value, Color fallback) {
    try {
      final clean = value.replaceAll('#', '').trim();
      if (clean.length != 6) return fallback;
      return Color(int.parse('FF$clean', radix: 16));
    } catch (_) {
      return fallback;
    }
  }

  ReportTemplateDefinition _currentTemplate() {
    final base = widget.draft.template;
    return base.copyWith(
      name: name.text.trim().isEmpty ? base.name : name.text.trim(),
      headerTitle: headerTitle.text.trim().isEmpty
          ? base.headerTitle
          : headerTitle.text.trim(),
      footerText: footer.text.trim(),
      primaryColor: RegExp(r'^#[0-9A-Fa-f]{6}$').hasMatch(primary.text.trim())
          ? primary.text.trim().toUpperCase()
          : base.primaryColor,
      secondaryColor:
          RegExp(r'^#[0-9A-Fa-f]{6}$').hasMatch(secondary.text.trim())
              ? secondary.text.trim().toUpperCase()
              : base.secondaryColor,
      headerStyle: headerStyle,
      logoMode: logoMode,
      signatureStyle: signatureStyle,
      photoColumns: photoColumns,
      showCover: showCover,
      showSummary: showSummary,
      showChecklistDetails: showChecklistDetails,
      isBuiltIn: false,
      useLegacyRenderer: false,
    );
  }

  Widget _preview() {
    final template = _currentTemplate();
    final p = _color(template.primaryColor, const Color(0xFF0B2E4F));
    final s = _color(template.secondaryColor, const Color(0xFF178A3D));

    return AspectRatio(
      aspectRatio: .72,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: Colors.grey.shade300),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(width: 34, height: 18, color: p),
                const Spacer(),
                Container(width: 28, height: 18, color: s.withOpacity(.25)),
              ],
            ),
            const SizedBox(height: 11),
            Container(width: double.infinity, height: 5, color: p),
            const SizedBox(height: 5),
            Container(width: 110, height: 5, color: Colors.grey.shade300),
            const SizedBox(height: 13),
            if (template.showSummary)
              Row(
                children: List.generate(
                  4,
                  (i) => Expanded(
                    child: Container(
                      margin: const EdgeInsets.only(right: 3),
                      height: 30,
                      color: i == 0
                          ? s.withOpacity(.18)
                          : Colors.grey.shade100,
                    ),
                  ),
                ),
              ),
            const SizedBox(height: 10),
            Container(width: 80, height: 4, color: p),
            const SizedBox(height: 5),
            Expanded(
              child: Row(
                children: [
                  Expanded(child: Container(color: Colors.grey.shade100)),
                  const SizedBox(width: 5),
                  Expanded(
                    child: Column(
                      children: [
                        Container(height: 7, color: p.withOpacity(.8)),
                        const SizedBox(height: 5),
                        Expanded(child: Container(color: Colors.grey.shade100)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _bullets(String title, List<String> values, {Color? color}) {
    if (values.isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: TextStyle(
              fontWeight: FontWeight.w800,
              color: color ?? Colors.black87,
            ),
          ),
          const SizedBox(height: 4),
          ...values.take(8).map(
                (value) => Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Text('• $value'),
                ),
              ),
        ],
      ),
    );
  }

  void _save() {
    Navigator.pop(
      context,
      _AiTemplateReviewResult(
        template: _currentTemplate(),
        useForCompany: useForCompany,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 900;
    final analysis = Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.draft.sourceFileName,
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 4),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            Chip(label: Text(widget.draft.templateClass)),
            Chip(label: Text('Confiança: ${widget.draft.confidence}')),
          ],
        ),
        const SizedBox(height: 6),
        Text(widget.draft.layoutSummary),
        _bullets('Seções identificadas', widget.draft.detectedSections),
        _bullets(
          'Adaptações necessárias',
          widget.draft.adaptations,
          color: Colors.deepOrange.shade800,
        ),
        _bullets(
          'Pontos para conferir',
          widget.draft.warnings,
          color: Colors.red.shade800,
        ),
      ],
    );

    final editor = Column(
      children: [
        TextField(
          controller: name,
          decoration: const InputDecoration(labelText: 'Nome do modelo'),
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: headerTitle,
          decoration: const InputDecoration(labelText: 'Título do cabeçalho'),
          onChanged: (_) => setState(() {}),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: primary,
                decoration: const InputDecoration(
                  labelText: 'Cor principal',
                  hintText: '#0B2E4F',
                ),
                onChanged: (_) => setState(() {}),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: secondary,
                decoration: const InputDecoration(
                  labelText: 'Cor secundária',
                  hintText: '#178A3D',
                ),
                onChanged: (_) => setState(() {}),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: headerStyle,
          decoration: const InputDecoration(labelText: 'Cabeçalho'),
          items: const [
            DropdownMenuItem(value: 'classico', child: Text('Clássico')),
            DropdownMenuItem(value: 'compacto', child: Text('Compacto')),
            DropdownMenuItem(value: 'impacto', child: Text('Destaque')),
          ],
          onChanged: (value) => setState(
            () => headerStyle = value ?? 'classico',
          ),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<int>(
          value: photoColumns,
          decoration: const InputDecoration(labelText: 'Fotos por linha'),
          items: const [
            DropdownMenuItem(value: 1, child: Text('1 foto grande')),
            DropdownMenuItem(value: 2, child: Text('2 fotos')),
            DropdownMenuItem(value: 3, child: Text('3 fotos')),
          ],
          onChanged: (value) => setState(() => photoColumns = value ?? 2),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: logoMode,
          decoration: const InputDecoration(labelText: 'Logos'),
          items: const [
            DropdownMenuItem(value: 'ambas', child: Text('Auditar + cliente')),
            DropdownMenuItem(value: 'auditar', child: Text('Somente Auditar')),
            DropdownMenuItem(value: 'cliente', child: Text('Somente cliente')),
            DropdownMenuItem(value: 'nenhuma', child: Text('Sem logos')),
          ],
          onChanged: (value) =>
              setState(() => logoMode = value ?? 'ambas'),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          value: signatureStyle,
          decoration: const InputDecoration(labelText: 'Assinaturas'),
          items: const [
            DropdownMenuItem(value: 'app', child: Text('Assinaturas do app')),
            DropdownMenuItem(value: 'linhas', child: Text('Linhas para assinatura')),
            DropdownMenuItem(value: 'ocultar', child: Text('Ocultar')),
          ],
          onChanged: (value) =>
              setState(() => signatureStyle = value ?? 'app'),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: footer,
          maxLines: 2,
          decoration: const InputDecoration(labelText: 'Rodapé'),
        ),
        SwitchListTile.adaptive(
          contentPadding: EdgeInsets.zero,
          value: showCover,
          title: const Text('Incluir capa'),
          onChanged: (value) => setState(() => showCover = value),
        ),
        SwitchListTile.adaptive(
          contentPadding: EdgeInsets.zero,
          value: showSummary,
          title: const Text('Incluir resumo gerencial'),
          onChanged: (value) => setState(() => showSummary = value),
        ),
        SwitchListTile.adaptive(
          contentPadding: EdgeInsets.zero,
          value: showChecklistDetails,
          title: const Text('Incluir checklist detalhado como anexo'),
          onChanged: (value) =>
              setState(() => showChecklistDetails = value),
        ),
        if (widget.canUseForCompany)
          SwitchListTile.adaptive(
            contentPadding: EdgeInsets.zero,
            value: useForCompany,
            title: const Text('Usar este modelo nesta empresa após salvar'),
            onChanged: (value) => setState(() => useForCompany = value),
          ),
      ],
    );

    return AlertDialog(
      title: const Text('Revisar modelo criado pela IA'),
      content: SizedBox(
        width: wide ? 980 : 560,
        height: MediaQuery.sizeOf(context).height * .72,
        child: SingleChildScrollView(
          child: wide
              ? Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'PDF original — leitura da IA',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 10),
                          analysis,
                        ],
                      ),
                    ),
                    const SizedBox(width: 18),
                    Expanded(
                      child: Column(
                        children: [
                          const Text(
                            'Modelo adaptado para o Auditar',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          const SizedBox(height: 10),
                          SizedBox(height: 310, child: _preview()),
                          const SizedBox(height: 12),
                          editor,
                        ],
                      ),
                    ),
                  ],
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Leitura do PDF',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 8),
                    analysis,
                    const Divider(height: 28),
                    const Text(
                      'Modelo criado para o Auditar',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 10),
                    SizedBox(height: 300, child: _preview()),
                    const SizedBox(height: 12),
                    editor,
                  ],
                ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancelar'),
        ),
        FilledButton.icon(
          onPressed: _save,
          icon: const Icon(Icons.save_outlined),
          label: const Text('Salvar modelo'),
        ),
      ],
    );
  }
}
'''

if "class _AiTemplateReviewDialog" not in s:
    s = s.rstrip() + dialogs + "\n"

write(rel, s)

rel = "painel_web_google_apps_script/Code.gs"
code = read(rel)

old_modes = "['checklist_photo', 'safety_observation_photo', 'report_conclusion', 'report_review_chat', 'company_priorities', 'training_management', 'cipa_minutes_import', 'training_record_import', 'employee_pdf_import', 'medical_pdf_import', 'pgr_extract', 'pgr_question', 'checklist_builder']"
new_modes = "['checklist_photo', 'safety_observation_photo', 'report_conclusion', 'report_review_chat', 'company_priorities', 'training_management', 'cipa_minutes_import', 'training_record_import', 'employee_pdf_import', 'medical_pdf_import', 'pgr_extract', 'pgr_question', 'report_template_import', 'checklist_builder']"
if new_modes not in code:
    if old_modes not in code:
        raise RuntimeError("whitelist de modos IA não localizada")
    code = code.replace(old_modes, new_modes, 1)

old_pdf_modes = "mode === 'training_record_import' || mode === 'employee_pdf_import' || mode === 'medical_pdf_import'"
new_pdf_modes = "mode === 'report_template_import' || mode === 'training_record_import' || mode === 'employee_pdf_import' || mode === 'medical_pdf_import'"
code = code.replace(old_pdf_modes, new_pdf_modes)

prompt = r'''if (mode === 'report_template_import') {
return [
'Analise este PDF como MODELO VISUAL de relatório de Segurança e Saúde no Trabalho.',
'O objetivo é adaptar o padrão visual e estrutural ao gerador de relatórios do Auditar, não copiar o conteúdo factual do relatório.',
'Identifique: presença de capa; estilo do cabeçalho; posição e quantidade aproximada de fotos; uso de resumo/indicadores; checklist detalhado; conclusão; assinaturas; rodapé; cores predominantes; hierarquia visual e tipo de relatório.',
'Classifique templateClass como Executivo, Fotográfico, Técnico, Obra, NR-12 ou Personalizado.',
'primaryColor e secondaryColor devem ser cores hexadecimais no formato #RRGGBB. Use aproximações seguras quando a cor exata não puder ser determinada.',
'headerStyle deve ser classico, compacto ou impacto. logoMode deve ser ambas, auditar, cliente ou nenhuma. signatureStyle deve ser app, linhas ou ocultar.',
'photoColumns deve ser 1, 2 ou 3 e representar a organização de evidências mais parecida com o PDF.',
'Em detectedSections liste as seções observadas no documento.',
'Em adaptations explique o que precisa ser adaptado porque o gerador do Auditar não reproduz livremente qualquer layout.',
'Em warnings informe elementos que precisam de conferência humana, como logos, fontes específicas, gráficos complexos ou elementos visuais que não possam ser inferidos com segurança.',
'Não invente logos, textos legais, registros profissionais, nomes de empresas, assinaturas ou conteúdo técnico do documento.',
'O modelo gerado deve ser apropriado para apresentação à gerência e preservar legibilidade em A4.'
].join('\n');
}
'''
u0 = code.find("function aiUserPrompt_(mode, payload)")
u1 = code.find("function aiOutputSchema_(mode)")
if u0 < 0 or u1 < 0:
    raise RuntimeError("funções de prompt/schema não localizadas")
if "if (mode === 'report_template_import')" not in code[u0:u1]:
    marker = "if (mode === 'report_review_chat') {"
    pos = code.find(marker, u0, u1)
    if pos < 0:
        raise RuntimeError("âncora report_review_chat não localizada")
    code = code[:pos] + prompt + code[pos:]

schema = r'''if (mode === 'report_template_import') {
return {
type: 'object',
properties: {
name: {type: 'string'},
description: {type: 'string'},
templateClass: {type: 'string', enum: ['Executivo', 'Fotográfico', 'Técnico', 'Obra', 'NR-12', 'Personalizado']},
primaryColor: {type: 'string'},
secondaryColor: {type: 'string'},
headerTitle: {type: 'string'},
headerStyle: {type: 'string', enum: ['classico', 'compacto', 'impacto']},
logoMode: {type: 'string', enum: ['ambas', 'auditar', 'cliente', 'nenhuma']},
footerText: {type: 'string'},
photoColumns: {type: 'integer', minimum: 1, maximum: 3},
signatureStyle: {type: 'string', enum: ['app', 'linhas', 'ocultar']},
showCover: {type: 'boolean'},
showSummary: {type: 'boolean'},
showChecklistDetails: {type: 'boolean'},
layoutSummary: {type: 'string'},
detectedSections: {type: 'array', items: {type: 'string'}},
adaptations: {type: 'array', items: {type: 'string'}},
warnings: {type: 'array', items: {type: 'string'}},
confidence: {type: 'string', enum: ['Baixa', 'Média', 'Alta']}
},
required: ['name', 'description', 'templateClass', 'primaryColor', 'secondaryColor', 'headerTitle', 'headerStyle', 'logoMode', 'footerText', 'photoColumns', 'signatureStyle', 'showCover', 'showSummary', 'showChecklistDetails', 'layoutSummary', 'detectedSections', 'adaptations', 'warnings', 'confidence']
};
}
'''
s0 = code.find("function aiOutputSchema_(mode)")
if s0 < 0:
    raise RuntimeError("aiOutputSchema_ não localizada")
if "if (mode === 'report_template_import')" not in code[s0:]:
    marker = "if (mode === 'report_review_chat') {"
    pos = code.find(marker, s0)
    if pos < 0:
        raise RuntimeError("âncora schema report_review_chat não localizada")
    code = code[:pos] + schema + code[pos:]

needle = """: mode === 'training_record_import'
          ? 'Selecione um PDF válido com o registro de treinamento.'
          : 'Selecione um PDF válido com a lista de funcionários.'"""
replacement = """: mode === 'report_template_import'
          ? 'Selecione um PDF válido com o modelo de relatório.'
          : mode === 'training_record_import'
            ? 'Selecione um PDF válido com o registro de treinamento.'
            : 'Selecione um PDF válido com a lista de funcionários.'"""
if needle in code:
    code = code.replace(needle, replacement, 1)

if "mode === 'report_template_import' ? 4800" not in code:
    if "maxOutputTokens:" not in code:
        raise RuntimeError("maxOutputTokens não localizado")
    code = code.replace(
        "maxOutputTokens:",
        "maxOutputTokens: mode === 'report_template_import' ? 4800\n:",
        1,
    )

# Garante validação e envio do PDF mesmo em bases Windows com cadeia antiga.
document_validation = r'''if (mode === 'report_template_import') {
if (!/^data:(application\/pdf);base64,/.test(document)) {
return {ok: false, message: 'Selecione um PDF válido com o modelo de relatório.'};
}
if (document.length > 18000000) {
return {ok: false, message: 'O PDF do modelo ultrapassou o limite da análise.'};
}
}

'''
validation_anchor = "if ((mode === 'pgr_extract' || mode === 'pgr_question')"
run_start = code.find("function runAiAssistant_(payload)")
if run_start < 0:
    raise RuntimeError("runAiAssistant_ não localizada")
anchor_pos = code.find(validation_anchor, run_start)
if anchor_pos < 0:
    raise RuntimeError("âncora de validação PGR não localizada")
segment_before = code[run_start:anchor_pos]
if "O PDF do modelo ultrapassou o limite da análise." not in segment_before:
    code = code[:anchor_pos] + document_validation + code[anchor_pos:]

inline_block = r'''if (mode === 'report_template_import') {
const match = document.match(/^data:(application\/pdf);base64,(.+)$/);
if (match) {
parts.push({inlineData: {mimeType: match[1], data: match[2]}});
}
}

'''
pgr_inline = "if (mode === 'pgr_extract' || mode === 'pgr_question') {"
parts_start = code.find("const parts = [{", run_start)
if parts_start < 0:
    raise RuntimeError("parts da IA não localizadas")
pgr_pos = code.find(pgr_inline, parts_start)
if pgr_pos < 0:
    raise RuntimeError("âncora inline PGR não localizada")
if "if (mode === 'report_template_import')" not in code[parts_start:pgr_pos]:
    code = code[:pgr_pos] + inline_block + code[pgr_pos:]

write(rel, code)

rel = "pubspec.yaml"
pub = read(rel)
version = "3.30.16+203" if platform == "windows" else "3.29.89+231"
pub, count = re.subn(
    r"(?m)^version:\s*[^\r\n]+",
    "version: " + version,
    pub,
    count=1,
)
if count != 1:
    raise RuntimeError("versão não localizada")
write(rel, pub)

screen = read("lib/screens/report_template_library_screen.dart")
service = read("lib/services/report_template_ai_import_service.dart")
backend = read("painel_web_google_apps_script/Code.gs")

for marker in [
    "Criador de modelos com IA",
    "Importar modelo em PDF com IA",
    "_AiTemplateReviewDialog",
    "Adaptações necessárias",
    "Salvar modelo",
]:
    assert marker in screen, "tela sem " + marker

for marker in [
    "report_template_import",
    "maxPdfBytes",
    "ReportTemplateAiDraft",
    "Central Online",
]:
    assert marker in service, "serviço sem " + marker

for marker in [
    "'report_template_import'",
    "Analise este PDF como MODELO VISUAL",
    "detectedSections",
    "adaptations",
    "templateClass",
]:
    assert marker in backend, "backend sem " + marker

assert f"version: {version}" in read("pubspec.yaml")
print("REPORT_TEMPLATE_AI_IMPORT_OK", platform, version)
