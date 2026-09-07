#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3330.py')],
        cwd=repo,
        check=True,
    )

    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    pubspec_path = app / 'pubspec.yaml'
    pubspec = pubspec_path.read_text(encoding='utf-8')
    pubspec = replace_once(
        pubspec,
        'version: 3.33.0+149',
        'version: 3.33.1+150',
        'versão pubspec',
    )
    pubspec_path.write_text(pubspec, encoding='utf-8')

    checklist_path = app / 'lib' / 'screens' / 'checklist_screen.dart'
    checklist = checklist_path.read_text(encoding='utf-8')
    checklist = replace_once(
        checklist,
        '  bool draftSaving = false;\n  Timer? draftSaveTimer;',
        '  bool draftSaving = false;\n  bool suppressDraftAutosave = false;\n  Timer? draftSaveTimer;',
        'flag de bloqueio do autosave',
    )
    checklist = replace_once(
        checklist,
        '    if (!saving && !draftSaving && !loadingExisting) {\n      unawaited(_saveDraft());\n    }',
        '    if (!suppressDraftAutosave &&\n        !saving &&\n        !draftSaving &&\n        !loadingExisting) {\n      unawaited(_saveDraft());\n    }',
        'dispose do checklist',
    )
    checklist = replace_once(
        checklist,
        '  void didChangeAppLifecycleState(AppLifecycleState state) {\n    if (state == AppLifecycleState.inactive ||',
        '  void didChangeAppLifecycleState(AppLifecycleState state) {\n    if (suppressDraftAutosave) return;\n    if (state == AppLifecycleState.inactive ||',
        'autosave por ciclo de vida',
    )
    checklist = replace_once(
        checklist,
        '  void _scheduleDraftSave() {\n    if (saving || draftSaving || loadingExisting) return;',
        '  void _scheduleDraftSave() {\n    if (suppressDraftAutosave || saving || draftSaving || loadingExisting) {\n      return;\n    }',
        'agendamento de rascunho',
    )
    checklist = replace_once(
        checklist,
        '  Future<void> _saveDraft({bool showMessage = false}) async {\n    if (saving || draftSaving || loadingExisting) return;',
        '  Future<void> _saveDraft({bool showMessage = false}) async {\n    if (suppressDraftAutosave || saving || draftSaving || loadingExisting) {\n      return;\n    }',
        'gravação de rascunho',
    )

    old_finish = '''      await db.markInspectionInProgress(widget.inspection.id);\n\n      if (!mounted) return;\n\n      Navigator.of(context).push(\n        MaterialPageRoute(\n          builder:\n              (_) => SignatureScreen(\n                inspectionId: widget.inspection.id,\n                companyName: widget.companyName,\n                technicianName: widget.inspection.technicianName,\n                preserveExisting: widget.editExisting,\n              ),\n        ),\n      );\n'''
    new_finish = '''      await db.markInspectionInProgress(widget.inspection.id);\n\n      if (!mounted) return;\n\n      // O checklist já foi persistido. Enquanto assinatura/relatório estiverem\n      // abertos, o autosave não pode reabrir uma vistoria já finalizada.\n      suppressDraftAutosave = true;\n      await Navigator.of(context).push(\n        MaterialPageRoute(\n          builder:\n              (_) => SignatureScreen(\n                inspectionId: widget.inspection.id,\n                companyName: widget.companyName,\n                technicianName: widget.inspection.technicianName,\n                preserveExisting: widget.editExisting,\n              ),\n        ),\n      );\n\n      if (!mounted) return;\n      final header = await db.getInspectionHeader(widget.inspection.id);\n      final status = '${header?['status'] ?? ''}'.trim();\n      if (status != 'Finalizada') {\n        // Se o usuário desistiu da assinatura, o salvamento de rascunho volta.\n        suppressDraftAutosave = false;\n      }\n'''
    checklist = replace_once(
        checklist,
        old_finish,
        new_finish,
        'transição checklist -> assinatura',
    )
    checklist_path.write_text(checklist, encoding='utf-8')

    for name in ('home_screen.dart', 'history_screen.dart'):
        path = app / 'lib' / 'screens' / name
        text = path.read_text(encoding='utf-8')
        text = replace_once(
            text,
            "if ('${row['status'] ?? ''}' != 'Finalizada') {",
            "if ('${row['status'] ?? ''}'.trim() == 'Em andamento') {",
            f'filtro de vistoria em andamento em {name}',
        )
        path.write_text(text, encoding='utf-8')

    changes = app / 'MUDANCAS_V3_33_1_FINALIZACAO_VISTORIA.txt'
    changes.write_text(
        'Auditar SST v3.33.1+150\n\n'
        '- Corrige a vistoria finalizada que voltava a aparecer como em andamento.\n'
        '- Impede o autosave do checklist de reabrir a vistoria após a assinatura.\n'
        '- Se a assinatura for cancelada, o rascunho volta a salvar normalmente.\n'
        '- O atalho Continuar vistoria considera apenas status Em andamento.\n'
        '- Sincronização bidirecional v3.33.0 preservada.\n',
        encoding='utf-8',
    )

    if 'version: 3.33.1+150' not in pubspec_path.read_text(encoding='utf-8'):
        raise RuntimeError('Versão v3.33.1+150 não aplicada.')
    final_checklist = checklist_path.read_text(encoding='utf-8')
    for expected in (
        'bool suppressDraftAutosave = false;',
        'suppressDraftAutosave = true;',
        'if (suppressDraftAutosave) return;',
        "if (status != 'Finalizada')",
    ):
        if expected not in final_checklist:
            raise RuntimeError(f'Proteção de finalização ausente: {expected}')

    for name in ('home_screen.dart', 'history_screen.dart'):
        text = (app / 'lib' / 'screens' / name).read_text(encoding='utf-8')
        if "trim() == 'Em andamento'" not in text:
            raise RuntimeError(f'Filtro de rascunho ausente em {name}')

    print(f'Fonte v3.33.1 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
