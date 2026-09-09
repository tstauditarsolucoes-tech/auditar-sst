#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        fail(f'marcador não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_report_media_performance_v3295.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    pdf_service = root / 'lib/services/pdf_service.dart'
    pubspec = root / 'pubspec.yaml'
    home = root / 'lib/screens/home_screen.dart'
    signature = root / 'lib/screens/signature_screen.dart'
    report_screen = root / 'lib/screens/report_screen.dart'

    for path in (pdf_service, pubspec, home, signature, report_screen):
        if not path.exists():
            fail(f'arquivo ausente: {path}')

    text = pdf_service.read_text(encoding='utf-8')

    # Reutiliza o mecanismo de mídia já existente. Antes de montar um relatório
    # completo, tenta trazer do Drive as evidências que ainda não existem neste
    # dispositivo. Falhas de rede não impedem a geração offline do PDF.
    text = replace_once(
        text,
        "import '../models.dart';\n",
        "import '../models.dart';\nimport 'media_sync_service.dart';\n",
        'import do MediaSyncService',
    )

    old_header = """    if (header == null) {
      throw Exception('Vistoria não encontrada.');
    }

    final answers = await db.getAnswers(inspectionId);"""
    new_header = """    if (header == null) {
      throw Exception('Vistoria não encontrada.');
    }

    // v3.29.5: em outro dispositivo o caminho local antigo pode não existir.
    // A mídia estruturada já é sincronizada pelo app; aqui apenas garantimos,
    // sob demanda, que os bytes disponíveis no Drive sejam baixados antes de
    // renderizar o relatório completo. Em modo offline o relatório continua.
    if (!executive) {
      try {
        await MediaSyncService.downloadMissing();
      } catch (_) {
        // Mantém a geração offline e o comportamento anterior se não houver rede.
      }
    }

    final answers = await db.getAnswers(inspectionId);"""
    text = replace_once(text, old_header, new_header, 'recuperação de mídia antes do PDF')

    old_queries = """    final answers = await db.getAnswers(inspectionId);
    final actions = await db.getActionsForInspection(inspectionId);
    final ncs = await db.getNonConformitiesForInspection(inspectionId);

    final reportFooter = await db.getSetting("""
    new_queries = """    final answers = await db.getAnswers(inspectionId);
    final actions = await db.getActionsForInspection(inspectionId);
    final ncs = await db.getNonConformitiesForInspection(inspectionId);

    // Uma mesma resposta aparece nos pontos de atenção, checklist completo e
    // evidências de correção. O cache evita repetir a mesma consulta SQLite.
    final photoCache = <String, Future<List<EvidencePhoto>>>{};
    Future<List<EvidencePhoto>> photosForAnswer(String answerId) {
      return photoCache.putIfAbsent(
        answerId,
        () => db.getPhotosForAnswer(answerId),
      );
    }

    final reportFooter = await db.getSetting("""
    text = replace_once(text, old_queries, new_queries, 'cache de evidências do relatório')

    query_marker = 'final photos = await db.getPhotosForAnswer(answer.id);'
    query_count = text.count(query_marker)
    if query_count != 2:
        fail(f'quantidade inesperada de consultas repetidas de fotos: {query_count}')
    text = text.replace(
        query_marker,
        'final photos = await photosForAnswer(answer.id);',
    )

    text = replace_once(
        text,
        'final before = await db.getOriginalPhotosForAction(action.id);',
        'final before = await photosForAnswer(action.answerId);',
        'reuso de fotos ANTES no plano de ação',
    )

    # context.pageNumber/pagesCount já representam a posição/total do documento.
    # A capa é adicionada antes do MultiPage e já entra nessa contagem.
    text = replace_once(
        text,
        "'Página ${context.pageNumber + 1} de ${context.pagesCount + 1}',",
        "'Página ${context.pageNumber} de ${context.pagesCount}',",
        'paginação sem deslocamento artificial',
    )

    pdf_service.write_text(text, encoding='utf-8')

    pub = pubspec.read_text(encoding='utf-8')
    pub, count = re.subn(
        r'^version:\s*3\.29\.4\+146\s*$',
        'version: 3.29.5+147',
        pub,
        count=1,
        flags=re.M,
    )
    if count != 1 and 'version: 3.29.5+147' not in pub:
        fail('versão base 3.29.4+146 não encontrada')
    pubspec.write_text(pub, encoding='utf-8')

    home_text = home.read_text(encoding='utf-8')
    home_text = home_text.replace('versão 3.29.4', 'versão 3.29.5')
    home.write_text(home_text, encoding='utf-8')

    # Regressões que não podem entrar nesta versão.
    checks = {
        pdf_service: [
            "import 'media_sync_service.dart';",
            'await MediaSyncService.downloadMissing();',
            'final photoCache = <String, Future<List<EvidencePhoto>>>{};',
            'final photos = await photosForAnswer(answer.id);',
            'final before = await photosForAnswer(action.answerId);',
            "'Página ${context.pageNumber} de ${context.pagesCount}',",
            'Foto indisponível',
        ],
        pubspec: ['version: 3.29.5+147'],
        signature: [
            'Assinar em tela cheia',
            'Assinar externamente por Gov.br',
            'Emitir sem assinatura',
        ],
        report_screen: ['Incluir plano de ação no relatório'],
    }
    for path, markers in checks.items():
        src = path.read_text(encoding='utf-8')
        for marker in markers:
            if marker not in src:
                fail(f'validação v3.29.5 falhou em {path.name}: {marker}')

    src = pdf_service.read_text(encoding='utf-8')
    if 'context.pageNumber + 1' in src or 'context.pagesCount + 1' in src:
        fail('paginação antiga ainda presente')
    if 'await db.getPhotosForAnswer(answer.id)' in src:
        fail('consulta duplicada de fotos ainda presente no PDF')
    if 'await db.getOriginalPhotosForAction(action.id)' in src:
        fail('consulta redundante das fotos ANTES ainda presente no PDF')

    note = root / 'MUDANCAS_V3_29_5_RELATORIO_E_DESEMPENHO.md'
    note.write_text(
        '# Auditar SST v3.29.5 — relatório e desempenho\n\n'
        '- Corrige a numeração das páginas do relatório, contando a capa sem deslocamento.\n'
        '- Antes do relatório completo, tenta recuperar do Drive mídias ainda ausentes no dispositivo.\n'
        '- Se estiver offline, a geração do relatório continua normalmente.\n'
        '- Reaproveita consultas de evidências fotográficas dentro da mesma geração de PDF.\n'
        '- Mantém assinatura em tela cheia, Gov.br, emissão sem assinatura e plano de ação opcional.\n'
        '- Não altera esquema do banco, histórico, estrutura do Drive nem arquitetura offline-first.\n',
        encoding='utf-8',
    )

    print('v3.29.5: relatório, mídia sob demanda e cache de fotos aplicados com sucesso')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
