#!/usr/bin/env python3
"""Client-facing report titles for every built-in layout and Ronda Expressa.

The selected template's internal label is for the library only. Keep company
data, AI, structured sync, photos, database, and persisted template IDs intact.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
assert platform in ('android', 'windows')


def modify(path, old, new, label):
    p = root / path
    source = p.read_text(encoding='utf-8')
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f'{path} / {label}: expected one occurrence, got {count}')
    p.write_text(source.replace(old, new, 1), encoding='utf-8', newline='\n')

template_path = 'lib/services/report_template_service.dart'
modify(template_path,
       "      headerTitle: 'RELATÓRIO PERFORMANCE',",
       "      headerTitle: 'RELATÓRIO DE VISTORIA',",
       'performance template public title')
modify(template_path,
       '  ReportTemplateDefinition copyWith({',
       """  /// Public document title is distinct from the internal library name.
  /// Preserve explicit meaningful titles from custom models.
  String get publicTitle {
    final title = headerTitle.trim();
    final internal = name.trim().toLowerCase().replaceAll(RegExp(r'\s+'), ' ');
    final value = title.toLowerCase().replaceAll(RegExp(r'\s+'), ' ');
    if (id == 'auditar_performance_grid' || headerStyle == 'performance') {
      return 'RELATÓRIO DE VISTORIA';
    }
    if (title.isEmpty ||
        value == internal ||
        value == 'relatório $internal' ||
        value == 'relatorio $internal' ||
        value == 'modelo $internal' ||
        value == 'relatório performance' ||
        value == 'relatorio performance') {
      return 'RELATÓRIO DE VISTORIA';
    }
    return title;
  }

  ReportTemplateDefinition copyWith({""",
       'public title policy')
styled = 'lib/services/styled_report_pdf_service.dart'
modify(styled, '    final doc = pw.Document();',
       '    final doc = pw.Document(title: template.publicTitle);',
       'styled PDF metadata')
modify(styled, "executive ? 'RELATÓRIO EXECUTIVO' : template.headerTitle,",
       "executive ? 'RELATÓRIO EXECUTIVO' : template.publicTitle,",
       'styled cover title')
modify(styled, '                  template.headerTitle,',
       '                  template.publicTitle,',
       'styled page header title')

ronda = 'lib/services/express_round_pdf_service.dart'
modify(ronda, '    final doc = pw.Document();',
       "    final doc = pw.Document(title: 'Relatório de ronda expressa');",
       'ronda PDF metadata')
modify(ronda,
       """                    template!.headerTitle.trim().isEmpty
                        ? 'RELATÓRIO DE RONDA EXPRESSA'
                        : template.headerTitle.toUpperCase(),""",
       """                    'RELATÓRIO DE RONDA EXPRESSA',""",
       'ronda cover title')
modify(ronda,
       """                template != null && template.headerTitle.trim().isNotEmpty
                    ? '${template.headerTitle.toUpperCase()}  -  RONDA EXPRESSA'
                    : (style == ExpressRoundReportStyle.photographic
                        ? 'RELATÓRIO FOTOGRÁFICO DE RONDA DE SEGURANÇA'
                        : 'RELATÓRIO TÉCNICO DE RONDA DE SEGURANÇA'),""",
       """                style == ExpressRoundReportStyle.photographic
                    ? 'RELATÓRIO FOTOGRÁFICO DE RONDA DE SEGURANÇA'
                    : 'RELATÓRIO TÉCNICO DE RONDA DE SEGURANÇA',""",
       'ronda body title')
pubspec = root / 'pubspec.yaml'
old_version, new_version = {
    'android': ('3.29.113+255', '3.29.114+256'),
    'windows': ('3.30.37+224', '3.30.38+225'),
}[platform]
pub = pubspec.read_text(encoding='utf-8')
assert pub.count('version: ' + old_version) == 1, 'Unexpected base version: ' + old_version
pubspec.write_text(pub.replace('version: ' + old_version,
                               'version: ' + new_version, 1),
                   encoding='utf-8', newline='\n')
print('ALL_REPORT_PUBLIC_TITLES_WITHOUT_MODEL_NAMES_OK', platform, new_version)
