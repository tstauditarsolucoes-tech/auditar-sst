#!/usr/bin/env python3
from pathlib import Path
import runpy

# Compatibilidade: o workflow original chama este nome. A implementação
# corrigida está no arquivo v32951b.
runpy.run_path(
    str(Path(__file__).with_name('patch_android_sync_latency_refresh_v32951b.py')),
    run_name='__main__',
)
