#!/usr/bin/env python3
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / 'app' / 'Auditar_SST_v1_5_dashboard'
path = APP / 'lib/screens/ai_report_chat_screen.dart'
text = path.read_text(encoding='utf-8')
old = """                    return const Align(\n                      alignment: Alignment.centerLeft,\n                      child: Padding("""
new = """                    return Align(\n                      alignment: Alignment.centerLeft,\n                      child: Padding("""
if old not in text:
    raise RuntimeError('Trecho do loading dinâmico não encontrado')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('v3.29.18: const inválido do loading da IA executiva corrigido.')
