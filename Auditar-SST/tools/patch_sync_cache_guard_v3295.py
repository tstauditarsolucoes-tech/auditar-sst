#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print('uso: patch_sync_cache_guard_v3295.py <raiz-do-app>', file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    service = root / 'lib/services/device_sync_service.dart'
    if not service.exists():
        raise RuntimeError(f'arquivo ausente: {service}')

    text = service.read_text(encoding='utf-8')
    marker = "SELECT 1 FROM sqlite_master"
    if marker in text:
        print('v3.29.5: proteção do cache de sincronização já aplicada')
        return 0

    old = """    if (_changeTrackingReady) return;
"""
    new = """    // O cache evita recriar triggers em toda sincronização, mas precisa ser
    // validado por conexão: testes, troca/recriação do banco e bancos distintos
    // no mesmo processo não compartilham necessariamente a tabela de controle.
    if (_changeTrackingReady) {
      final trackingTable = await db.rawQuery(
        \"SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = '$_changesTable' LIMIT 1\",
      );
      if (trackingTable.isNotEmpty) return;
      _changeTrackingReady = false;
    }
"""

    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f'marcador do cache de sincronização inesperado: encontrado {count} vez(es)'
        )
    text = text.replace(old, new, 1)
    service.write_text(text, encoding='utf-8')

    check = service.read_text(encoding='utf-8')
    if marker not in check or 'static bool _changeTrackingReady = false;' not in check:
        raise RuntimeError('validação da proteção do cache falhou')

    print('v3.29.5: cache de sincronização protegido para múltiplos bancos')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
