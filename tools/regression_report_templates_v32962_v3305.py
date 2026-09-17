#!/usr/bin/env python3
from __future__ import annotations

import re
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
    coord = (root / 'lib/services/sync_coordinator.dart').read_text(encoding='utf-8')
    dev = (root / 'lib/services/device_sync_service.dart').read_text(encoding='utf-8')
    http = (root / 'lib/services/apps_script_http.dart').read_text(encoding='utf-8')
    ai = (root / 'lib/services/ai_assistant_service.dart').read_text(encoding='utf-8')
    ronda = (root / 'lib/screens/express_round_screen.dart').read_text(encoding='utf-8')

    failures: list[str] = []
    checks = 0

    def check(name: str, ok: bool) -> None:
        nonlocal checks
        checks += 1
        require(name, ok, failures)

    check('versão', f'version: {expected_version}' in pubspec)
    check('seis modelos', all(token in report for token in (
        'padrao_auditar', 'executivo', 'fotografico', 'obra', 'tecnico_clean', 'nr12',
        'Padrão Auditar', 'Executivo', 'Fotográfico', 'Obra', 'Técnico Clean', 'NR-12',
    )))
    check('padrão do usuário', 'report_template_user_default' in report)
    check('padrão da empresa', 'report_template_company_' in report)
    check('seleção por inspeção', 'report_template_inspection_' in report)
    check('editor apenas Windows', 'Platform.isWindows' in report and 'Personalizar modelo' in report)
    check('editor visual', all(token in report for token in (
        'Cor principal', 'Cor de destaque', 'Cabeçalho', 'Rodapé',
    )))
    check('opções de composição', all(token in report for token in (
        'Capa', 'Fotos', 'Assinaturas', 'Logo Auditar', 'Logo da empresa',
    )))
    check('resolução automática no PDF', all(token in pdf for token in (
        'effectiveTemplateId', 'report_template_user_default', 'report_template_company_',
        'report_template_inspection_',
    )))
    check('Drive sem template continua resolvendo padrão', 'allowEmpty: true' in pdf)
    check('arquivo de relatório propaga template', 'templateId' in report_file)

    # Regressão funcional herdada da v3.29.61/v3.30.4.
    check('histórico de Rondas preservado', all(token in ronda for token in (
        '_showRoundsArchive', 'Histórico de Rondas Expressas', '_loadRoundById',
        'viewingHistoricalRound', '_historicalRoundBody', '_historicalBottomBar',
        'Voltar à ronda atual',
    )))
    check('revisão humana da IA preservada', all(token in ronda for token in (
        '_reviewDeferredAiSuggestion', 'A IA não altera o registro automaticamente',
        'Aprovar e salvar', 'Manter pendente', "..['aiReviewedByTechnician'] = true",
        "..['aiStatus'] = 'CONCLUIDA'",
    )))
    try:
        batch = ronda.split('Future<void> _analyzePendingRoundPhotos() async {', 1)[1].split(
            'Future<void> _showRoundHistory() async {', 1
        )[0]
        review_before_save = batch.index('_reviewDeferredAiSuggestion') < batch.index("..['aiAssisted'] = true")
    except (IndexError, ValueError):
        review_before_save = False
    check('IA só grava após revisão', review_before_save)
    check('foto IA otimizada preservada', all(token in ai for token in (
        "'mode': 'checklist_photo'", "'rondaDeferred': true",
        "final rondaDeferred = payload['rondaDeferred'] == true;",
        '_prepareRoundPhotoForAi', 'maxDimension = 720', 'quality: 55',
        'const Duration(seconds: 95)', 'const Duration(seconds: 55)',
    )))

    if platform == 'android':
        check('Android sync 2s/5s preservado', 'Duration(seconds: 2)' in coord and 'Duration(seconds: 5)' in coord)
        check('Android pull 500 preservado', dev.count("'limit': 500,") >= 2)
        check('Android HTTP longo controlado', 'androidDirect && !allowLongAndroidRequest' in http)
        check('Android sem sync gerencial na Ronda', 'await ManagementPanelService.syncCompany(widget.company)' not in ronda)
        check('Android IA longa explícita', bool(re.search(r'allowLongAndroidRequest\s*:\s*true', ai)))
    else:
        media = (root / 'lib/services/media_sync_service.dart').read_text(encoding='utf-8')
        companies = (root / 'lib/screens/companies_screen.dart').read_text(encoding='utf-8')
        dds = (root / 'lib/screens/sst_records_screen.dart').read_text(encoding='utf-8')
        check('Windows sync 10s preservado', 'Duration(seconds: 10)' in coord)
        check('Windows pull 500 preservado', 'final pullLimit = isWindows ? 500 : 100;' in dev)
        check('Windows pullWhenClean preservado', 'pullWhenClean: true' in coord and 'force: force' in coord)
        check('Windows sync gerencial preservado', 'ManagementPanelService.syncCompany(widget.company)' in ronda)
        check('Windows logos e DDS preservados', all((
            'restoreCompanyLogos' in media,
            "'action': 'media_lookup'" in media,
            'MediaSyncService.restoreCompanyLogos' in companies,
            'MediaSyncService.uploadCompanyLogoNow' in companies,
            "'companies': {'logo_path'}" in dev,
            'Retirar ficha do DDS' in dds,
        )))
        icon = root / 'windows/runner/resources/app_icon.ico'
        check('ícone Windows preservado', icon.exists() and icon.stat().st_size > 10000)

    passed = checks - len(failures)
    if failures:
        print(f'REGRESSION_REPORT_TEMPLATES_FAIL {passed}/{checks}: ' + ', '.join(failures))
        return 1
    print(f'REGRESSION_REPORT_TEMPLATES_OK {passed}/{checks} platform={platform}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
