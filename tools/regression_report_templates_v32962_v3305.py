#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def require(name: str, ok: bool, failures: list[str]) -> None:
    if ok:
        print(f'OK   {name}')
    else:
        print(f'FAIL {name}')
        failures.append(name)


def main() -> int:
    if len(sys.argv) != 3:
        print('uso: regression_report_templates_v32962_v3305.py <raiz-do-app> <android|windows>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    platform = sys.argv[2].strip().lower()
    if platform not in {'android', 'windows'}:
        print('plataforma deve ser android ou windows', file=sys.stderr)
        return 2

    expected_version = '3.29.62+204' if platform == 'android' else '3.30.5+192'
    report = (root / 'lib/screens/report_screen.dart').read_text(encoding='utf-8')
    pdf = (root / 'lib/services/pdf_service.dart').read_text(encoding='utf-8')
    report_file = (root / 'lib/services/report_file_service.dart').read_text(encoding='utf-8')
    pubspec = (root / 'pubspec.yaml').read_text(encoding='utf-8')

    failures: list[str] = []
    require('versão', f'version: {expected_version}' in pubspec, failures)
    require('seis modelos', all(token in report for token in (
        'padrao_auditar', 'executivo', 'fotografico', 'obra', 'tecnico_clean', 'nr12',
        'Padrão Auditar', 'Executivo', 'Fotográfico', 'Obra', 'Técnico Clean', 'NR-12',
    )), failures)
    require('padrão do usuário', 'report_template_user_default' in report, failures)
    require('padrão da empresa', 'report_template_company_' in report, failures)
    require('seleção por inspeção', 'report_template_inspection_' in report, failures)
    require('editor apenas Windows', "Platform.isWindows" in report and 'Personalizar modelo' in report, failures)
    require('editor visual', all(token in report for token in (
        'Cor principal', 'Cor de destaque', 'Cabeçalho', 'Rodapé',
    )), failures)
    require('opções de composição', all(token in report for token in (
        'Capa', 'Fotos', 'Assinaturas', 'Logo Auditar', 'Logo da empresa',
    )), failures)
    require('resolução automática no PDF', all(token in pdf for token in (
        'effectiveTemplateId', 'report_template_user_default', 'report_template_company_',
        'report_template_inspection_',
    )), failures)
    require('Drive sem template continua resolvendo padrão', 'allowEmpty: true' in pdf, failures)
    require('arquivo de relatório propaga template', 'templateId' in report_file, failures)

    total = 11
    passed = total - len(failures)
    if failures:
        print(f'REGRESSION_REPORT_TEMPLATES_FAIL {passed}/{total}: ' + ', '.join(failures))
        return 1
    print(f'REGRESSION_REPORT_TEMPLATES_OK {passed}/{total} platform={platform}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
