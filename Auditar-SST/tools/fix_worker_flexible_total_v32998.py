#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1])/'lib/services/worker_import_service.dart'
s=p.read_text(encoding='utf-8')
old=r"r'\btotal\s+(?:geral\s*)?:?\s*(\d+)\s*(?:empregados|funcionarios|funcionários|colaboradores|trabalhadores)?\b'"
new=r"r'\btotal(?:\s+geral)?\s*:?\s*(\d+)\b'"
if s.count(old)!=1: raise RuntimeError('total de importacao nao localizado')
p.write_text(s.replace(old,new,1),encoding='utf-8')
print('WORKER_FLEXIBLE_TOTAL_OK')
