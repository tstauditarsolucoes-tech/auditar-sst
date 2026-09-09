#!/usr/bin/env python3
from __future__ import annotations

import base64
import gzip
from pathlib import Path

payload = Path(__file__).resolve().parent / 'v3840' / 'assembler.b64'
code = gzip.decompress(base64.b64decode(payload.read_text(encoding='utf-8').strip())).decode('utf-8')
exec(compile(code, 'assemble_v3840_payload.py', 'exec'), {'__file__': __file__, '__name__': '__main__'})
