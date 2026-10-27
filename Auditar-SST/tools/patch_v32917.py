#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP = REPO / 'app' / 'Auditar_SST_v1_5_dashboard'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def patch_company_detail() -> None:
    path = APP / 'lib/screens/company_detail_screen.dart'
    text = path.read_text(encoding='utf-8')
    old = """          _shortcut(\n            icon: Icons.report_problem_outlined,\n            title: 'Atos e condições inseguras',\n"""
    new = """          _shortcut(\n            icon: Icons.psychology_alt_outlined,\n            title: 'IA · O que merece sua atenção',\n            subtitle: 'Cruza vistorias, atos/condições, NCs, ações, incidentes, treinamentos e PGR',\n            onTap: () => _open(ManagementPanelScreen(company: widget.company)),\n          ),\n          const SizedBox(height: 10),\n          _shortcut(\n            icon: Icons.report_problem_outlined,\n            title: 'Atos e condições inseguras',\n"""
    text = replace_once(text, old, new, 'atalho IA da empresa')
    path.write_text(text, encoding='utf-8')


def patch_report_screen() -> None:
    path = APP / 'lib/screens/report_screen.dart'
    text = path.read_text(encoding='utf-8')
    text = replace_once(text, '  bool pdfBusy = false;\n', '  bool fullPdfBusy = false;\n  bool executivePdfBusy = false;\n', 'estados separados PDF')
    text = replace_once(
        text,
        """  Future<void> _sharePdf({required bool executive}) async {\n    if (pdfBusy) return;\n    setState(() => pdfBusy = true);\n\n    try {\n""",
        """  Future<void> _sharePdf({required bool executive}) async {\n    if (executive ? executivePdfBusy : fullPdfBusy) return;\n    setState(() {\n      if (executive) {\n        executivePdfBusy = true;\n      } else {\n        fullPdfBusy = true;\n      }\n    });\n\n    try {\n""",
        'entrada geração PDF',
    )
    text = replace_once(
        text,
        """      await Printing.sharePdf(\n        bytes: bytes,\n        filename: executive\n            ? 'Relatorio_Executivo_Auditar_SST.pdf'\n            : 'Relatorio_Completo_Auditar_SST.pdf',\n      );\n    } finally {\n      if (mounted) setState(() => pdfBusy = false);\n    }\n""",
        """      if (mounted) {\n        setState(() {\n          if (executive) {\n            executivePdfBusy = false;\n          } else {\n            fullPdfBusy = false;\n          }\n        });\n      }\n\n      await Printing.sharePdf(\n        bytes: bytes,\n        filename: executive\n            ? 'Relatorio_Executivo_Auditar_SST.pdf'\n            : 'Relatorio_Completo_Auditar_SST.pdf',\n      );\n    } finally {\n      if (mounted && (executive ? executivePdfBusy : fullPdfBusy)) {\n        setState(() {\n          if (executive) {\n            executivePdfBusy = false;\n          } else {\n            fullPdfBusy = false;\n          }\n        });\n      }\n    }\n""",
        'saída rápida Gerando',
    )
    text = replace_once(
        text,
        """      body: ListView(\n        padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),\n        children: [\n""",
        """      body: Center(\n        child: ConstrainedBox(\n          constraints: const BoxConstraints(maxWidth: 1200),\n          child: ListView(\n            padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),\n            children: [\n""",
        'largura PC',
    )
    old_options = """          _reportOption(\n            title: 'Relatório Completo',\n            subtitle: includeActionPlan\n                ? 'Capa, resumo, pendências, fotos, plano de ação, checklist completo, antes/depois, conclusão e assinaturas.'\n                : 'Capa, resumo, pendências, fotos, checklist completo, antes/depois, conclusão e assinaturas.',\n            icon: Icons.description_outlined,\n            recommended: true,\n            onShare: () => _sharePdf(executive: false),\n            onSave: () => _saveLocal(executive: false),\n          ),\n          const SizedBox(height: 10),\n          _reportOption(\n            title: 'Relatório Executivo',\n            subtitle: includeActionPlan\n                ? 'Versão gerencial com quantitativos, quadro de providências, fotos das pendências, responsáveis, prazos, resolvidos e conclusão.'\n                : 'Versão gerencial com quantitativos, quadro de providências, fotos das pendências e conclusão.',\n            icon: Icons.assessment_outlined,\n            onShare: () => _sharePdf(executive: true),\n            onSave: () => _saveLocal(executive: true),\n          ),\n"""
    new_options = """          ResponsiveWrap(\n            minItemWidth: 360,\n            maxColumns: 2,\n            children: [\n              _reportOption(\n                title: 'Relatório Completo',\n                subtitle: includeActionPlan\n                    ? 'Capa, resumo, pendências, fotos, plano de ação, checklist completo, antes/depois, conclusão e assinaturas.'\n                    : 'Capa, resumo, pendências, fotos, checklist completo, antes/depois, conclusão e assinaturas.',\n                icon: Icons.description_outlined,\n                recommended: true,\n                busy: fullPdfBusy,\n                onShare: () => _sharePdf(executive: false),\n                onSave: () => _saveLocal(executive: false),\n              ),\n              _reportOption(\n                title: 'Relatório Executivo',\n                subtitle: includeActionPlan\n                    ? 'Versão gerencial com quantitativos, quadro de providências, fotos das pendências, responsáveis, prazos, resolvidos e conclusão.'\n                    : 'Versão gerencial com quantitativos, quadro de providências, fotos das pendências e conclusão.',\n                icon: Icons.assessment_outlined,\n                busy: executivePdfBusy,\n                onShare: () => _sharePdf(executive: true),\n                onSave: () => _saveLocal(executive: true),\n              ),\n            ],\n          ),\n"""
    text = replace_once(text, old_options, new_options, 'cartões responsivos')
    text = replace_once(
        text,
        """          ),\n        ],\n      ),\n    );\n  }\n\n  Widget _heroCard""",
        """          ),\n            ],\n          ),\n        ),\n      ),\n    );\n  }\n\n  Widget _heroCard""",
        'fechamento layout PC',
    )
    text = replace_once(
        text,
        """    required VoidCallback onShare,\n    required VoidCallback onSave,\n    bool recommended = false,\n""",
        """    required VoidCallback onShare,\n    required VoidCallback onSave,\n    required bool busy,\n    bool recommended = false,\n""",
        'busy cartão',
    )
    text = replace_once(
        text,
        """                    onPressed: pdfBusy ? null : onShare,\n                    icon: const Icon(Icons.picture_as_pdf_outlined),\n                    label: Text(\n                      pdfBusy ? 'Gerando...' : 'Gerar / compartilhar',\n""",
        """                    onPressed: busy ? null : onShare,\n                    icon: const Icon(Icons.picture_as_pdf_outlined),\n                    label: Text(\n                      busy ? 'Gerando...' : 'Gerar / compartilhar',\n""",
        'busy independente',
    )
    path.write_text(text, encoding='utf-8')


def patch_device_sync() -> None:
    path = APP / 'lib/services/device_sync_service.dart'
    text = path.read_text(encoding='utf-8')
    old = """          if ((table == 'evidence_photos' || table == 'completion_photos') &&\n              !payload.containsKey('path')) {\n            payload['path'] = '';\n          }\n\n          final updated = await txn.update(\n            table,\n            payload,\n            where: 'id = ?',\n            whereArgs: [recordId],\n          );\n          if (updated == 0) {\n            await txn.insert(\n              table,\n              payload,\n              conflictAlgorithm: ConflictAlgorithm.replace,\n            );\n          }\n"""
    new = """          final updated = await txn.update(\n            table,\n            payload,\n            where: 'id = ?',\n            whereArgs: [recordId],\n          );\n          if (updated == 0) {\n            final insertPayload = Map<String, Object?>.from(payload);\n            if ((table == 'evidence_photos' || table == 'completion_photos') &&\n                !insertPayload.containsKey('path')) {\n              insertPayload['path'] = '';\n            }\n            await txn.insert(\n              table,\n              insertPayload,\n              conflictAlgorithm: ConflictAlgorithm.replace,\n            );\n          }\n"""
    text = replace_once(text, old, new, 'preservar caminhos locais')
    path.write_text(text, encoding='utf-8')


def patch_media_and_pdf() -> None:
    media_path = APP / 'lib/services/media_sync_service.dart'
    media = media_path.read_text(encoding='utf-8')
    media = replace_once(media, '  static Future<MediaSyncSummary> downloadMissing() async {\n', '  static Future<MediaSyncSummary> downloadMissing({int limit = 120}) async {\n', 'limite parametrizável mídia')
    media = replace_once(media, """      orderBy: 'updated_at DESC',\n      limit: 120,\n""", """      orderBy: \"CASE WHEN entity_type = 'company_logo' THEN 0 ELSE 1 END, updated_at DESC\",\n      limit: limit,\n""", 'prioridade logo na recuperação')
    media_path.write_text(media, encoding='utf-8')

    pdf_path = APP / 'lib/services/pdf_service.dart'
    pdf = pdf_path.read_text(encoding='utf-8')
    pdf = replace_once(pdf, '      await MediaSyncService.downloadMissing();\n', '      await MediaSyncService.downloadMissing(limit: 24)\n          .timeout(const Duration(seconds: 5));\n', 'timeout mídia relatório')
    pdf_path.write_text(pdf, encoding='utf-8')


def patch_version() -> None:
    pub = APP / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.29.16+159', 'version: 3.29.17+160', 'versão')
    pub.write_text(text, encoding='utf-8')
    home = APP / 'lib/screens/home_screen.dart'
    text = home.read_text(encoding='utf-8')
    text = text.replace('Auditar SST • versão 3.29.16', 'Auditar SST • versão 3.29.17')
    text = text.replace('Auditar SST para Windows • versão 3.29.16', 'Auditar SST para Windows • versão 3.29.17')
    home.write_text(text, encoding='utf-8')


def validate() -> None:
    checks = {
        'versão': 'version: 3.29.17+160' in (APP / 'pubspec.yaml').read_text(encoding='utf-8'),
        'IA atenção': 'IA · O que merece sua atenção' in (APP / 'lib/screens/company_detail_screen.dart').read_text(encoding='utf-8'),
        'PDF separado': all(x in (APP / 'lib/screens/report_screen.dart').read_text(encoding='utf-8') for x in ('fullPdfBusy', 'executivePdfBusy')),
        'fotos preservadas': 'insertPayload' in (APP / 'lib/services/device_sync_service.dart').read_text(encoding='utf-8'),
        'logo priorizada': 'company_logo' in (APP / 'lib/services/media_sync_service.dart').read_text(encoding='utf-8') and 'CASE WHEN entity_type' in (APP / 'lib/services/media_sync_service.dart').read_text(encoding='utf-8'),
        'PDF limitado': 'downloadMissing(limit: 24)' in (APP / 'lib/services/pdf_service.dart').read_text(encoding='utf-8'),
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações v3.29.17 falharam: ' + ', '.join(missing))


def main() -> int:
    patch_company_detail()
    patch_report_screen()
    patch_device_sync()
    patch_media_and_pdf()
    patch_version()
    validate()
    print('v3.29.17+160 aplicada sobre a base v3.29.16+159.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
