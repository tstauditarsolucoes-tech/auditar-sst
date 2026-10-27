#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PATCHES = [
    'patch_management_snapshot.py',
    'prepare_sst_source.py',
    'patch_resume_vistoria.py',
    'patch_multiuser.py',
    'patch_checklist_v324.py',
    'patch_quality_v3241.py',
    'patch_auth_timeout_v3241.py',
    'patch_simple_login_v3242.py',
    'patch_sync_v3243.py',
    'patch_windows_db_v3244.py',
    'patch_visual_v3245.py',
    'patch_pgr_ai_v3250.py',
    'patch_worker_sector_import_v3251.py',
    'patch_checklist_ai_v3252.py',
    'patch_pgr_tools_v3260.py',
    'patch_hardening_v3270.py',
    'patch_report_v3280.py',
    'apply_v3290_final_overrides.py',
    'patch_signature_fullscreen_v3291.py',
]


def run(script: Path, app: Path) -> None:
    subprocess.run([sys.executable, str(script), str(app)], check=True)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    out_root = repo / 'app'
    app = out_root / 'Auditar_SST_v1_5_dashboard'
    base_zip = repo / 'Auditar_SST_v1.5_dashboard_completo.zip'
    overrides = repo / 'source_overrides' / 'Auditar_SST_v1_5_dashboard'

    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)

    with zipfile.ZipFile(base_zip) as zf:
        zf.extractall(out_root)
    if not app.exists():
        raise RuntimeError(f'pasta do app não encontrada após extração: {app}')

    shutil.copytree(overrides, app, dirs_exist_ok=True)

    for name in PATCHES:
        run(repo / 'tools' / name, app)

    print(f'Fonte v3.29.1 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
