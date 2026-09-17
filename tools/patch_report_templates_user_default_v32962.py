#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')


def replace_once(path: Path, old: str, new: str, label: str):
    text = path.read_text(encoding='utf-8')
    if new in text:
        return
    if old not in text:
        raise SystemExit(f'âncora ausente ({label}) em {path}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8', newline='\n')


service = root / 'lib/services/report_template_service.dart'
replace_once(
    service,
    "import '../database.dart';\n",
    "import '../database.dart';\nimport 'auth_service.dart';\n",
    'import AuthService',
)

replace_once(
    service,
    "  static const _customKey = 'report_templates_custom_v1';\n  static const currentTemplateId = 'auditar_atual';\n",
    "  static const _customKey = 'report_templates_custom_v1';\n  static const _userDefaultPrefix = 'report_template_user_default_v1';\n  static const currentTemplateId = 'auditar_atual';\n",
    'prefixo padrão usuário',
)

replace_once(
    service,
    "  static String _selectionKey(String companyId) => 'report_template_company_${companyId.trim()}';\n\n",
    "  static String _selectionKey(String companyId) => 'report_template_company_${companyId.trim()}';\n\n"
    "  static String _userScope() {\n"
    "    final raw = (AuthService.currentUser?.id ?? 'local').trim();\n"
    "    final value = raw.isEmpty ? 'local' : raw;\n"
    "    return value.replaceAll(RegExp(r'[^a-zA-Z0-9._-]'), '_');\n"
    "  }\n\n"
    "  static String _userDefaultKey() => '${_userDefaultPrefix}_${_userScope()}';\n\n",
    'escopo usuário',
)

anchor = "  static Future<void> selectForCompany(String companyId, String templateId) async {\n"
insert = """  static Future<void> selectDefaultForCurrentUser(String templateId) async {
    await AppDatabase.instance.setSetting(_userDefaultKey(), templateId);
  }

  static Future<ReportTemplateDefinition> selectedDefaultForCurrentUser() async {
    final selected = await AppDatabase.instance.getSetting(
      _userDefaultKey(),
      fallback: currentTemplateId,
    );
    final all = await getAllTemplates();
    return all.firstWhere(
      (e) => e.id == selected,
      orElse: () => currentTemplate,
    );
  }

"""
replace_once(service, anchor, insert + anchor, 'métodos padrão usuário')

old_selected = """  static Future<ReportTemplateDefinition> selectedForCompany(String companyId) async {
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
"""
new_selected = """  static Future<ReportTemplateDefinition> selectedForCompany(String companyId) async {
    final userDefault = await selectedDefaultForCurrentUser();
    if (companyId.trim().isEmpty) return userDefault;
    final selected = await AppDatabase.instance.getSetting(
      _selectionKey(companyId),
      fallback: userDefault.id,
    );
    final all = await getAllTemplates();
    return all.firstWhere(
      (e) => e.id == selected,
      orElse: () => userDefault,
    );
  }
"""
replace_once(service, old_selected, new_selected, 'precedência empresa > usuário')

screen = root / 'lib/screens/report_template_library_screen.dart'
replace_once(
    screen,
    "  bool get canSelect => (widget.companyId ?? '').trim().isNotEmpty;\n",
    "  bool get isCompanyMode => (widget.companyId ?? '').trim().isNotEmpty;\n  bool get canSelect => true;\n",
    'modo usuário/empresa',
)

old_load = """    var selected = ReportTemplateService.currentTemplate;
    if (canSelect) {
      selected = await ReportTemplateService.selectedForCompany(widget.companyId!);
    }
"""
new_load = """    final selected = isCompanyMode
        ? await ReportTemplateService.selectedForCompany(widget.companyId!)
        : await ReportTemplateService.selectedDefaultForCurrentUser();
"""
replace_once(screen, old_load, new_load, 'carregar seleção por escopo')

old_select = """  Future<void> _select(ReportTemplateDefinition template) async {
    if (!canSelect) return;
    await ReportTemplateService.selectForCompany(widget.companyId!, template.id);
    if (!mounted) return;
    setState(() => selectedId = template.id);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Modelo \"${template.name}\" selecionado para esta empresa.')),
    );
  }
"""
new_select = """  Future<void> _select(ReportTemplateDefinition template) async {
    if (isCompanyMode) {
      await ReportTemplateService.selectForCompany(widget.companyId!, template.id);
    } else {
      await ReportTemplateService.selectDefaultForCurrentUser(template.id);
    }
    if (!mounted) return;
    setState(() => selectedId = template.id);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          isCompanyMode
              ? 'Modelo \"${template.name}\" selecionado para esta empresa.'
              : 'Modelo \"${template.name}\" definido como seu padrão.',
        ),
      ),
    );
  }
"""
replace_once(screen, old_select, new_select, 'selecionar usuário/empresa')

old_customize = """    await ReportTemplateService.saveCustom(result);
    if (canSelect) {
      await ReportTemplateService.selectForCompany(widget.companyId!, result.id);
    }
    await _load();
"""
new_customize = """    await ReportTemplateService.saveCustom(result);
    if (isCompanyMode) {
      await ReportTemplateService.selectForCompany(widget.companyId!, result.id);
    } else {
      await ReportTemplateService.selectDefaultForCurrentUser(result.id);
    }
    await _load();
"""
replace_once(screen, old_customize, new_customize, 'personalizar e selecionar')

old_delete = """    if (selectedId == template.id && canSelect) {
      await ReportTemplateService.selectForCompany(widget.companyId!, ReportTemplateService.currentTemplateId);
    }
"""
new_delete = """    if (selectedId == template.id) {
      if (isCompanyMode) {
        await ReportTemplateService.selectForCompany(
          widget.companyId!,
          ReportTemplateService.currentTemplateId,
        );
      } else {
        await ReportTemplateService.selectDefaultForCurrentUser(
          ReportTemplateService.currentTemplateId,
        );
      }
    }
"""
replace_once(screen, old_delete, new_delete, 'exclusão por escopo')

# Texto introdutório distingue biblioteca pessoal de escolha específica da empresa.
old_intro_windows = "'No computador você pode criar, personalizar e salvar novos modelos. O modelo atual continua intacto e sempre disponível.'"
new_intro_windows = "isCompanyMode\n                          ? 'Escolha o modelo desta empresa. Ele terá prioridade sobre o seu modelo padrão pessoal.'\n                          : 'Escolha seu modelo padrão pessoal. No computador você também pode criar, personalizar e salvar novos modelos. O modelo atual continua intacto e sempre disponível.'"
replace_once(screen, old_intro_windows, new_intro_windows, 'intro Windows por escopo')

old_intro_mobile = "'No celular você pode escolher modelos e fazer ajustes básicos. O modelo atual continua intacto e sempre disponível.'"
new_intro_mobile = "isCompanyMode\n                          ? 'Escolha o modelo desta empresa. Ele terá prioridade sobre o seu modelo padrão pessoal.'\n                          : 'Escolha seu modelo padrão pessoal. No celular você pode selecionar modelos e fazer ajustes básicos. O modelo atual continua intacto e sempre disponível.'"
replace_once(screen, old_intro_mobile, new_intro_mobile, 'intro Android por escopo')

# Chip e botão deixam claro se é padrão do usuário ou da empresa.
replace_once(
    screen,
    "if (selected) const Chip(label: Text('Selecionado')),",
    "if (selected)\n                          Chip(\n                            label: Text(\n                              isCompanyMode ? 'Padrão da empresa' : 'Meu padrão',\n                            ),\n                          ),",
    'chip de seleção',
)

replace_once(
    screen,
    "label: Text(selected ? 'Em uso' : 'Usar este modelo'),",
    "label: Text(\n                      selected\n                          ? 'Em uso'\n                          : (isCompanyMode\n                              ? 'Usar nesta empresa'\n                              : 'Definir como meu padrão'),\n                    ),",
    'botão de seleção',
)

print('Modelo padrão individual por usuário aplicado; empresa pode sobrescrever sem alterar o padrão pessoal.')
