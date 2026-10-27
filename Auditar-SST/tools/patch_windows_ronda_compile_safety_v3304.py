#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')
screenp = root / 'lib/screens/express_round_screen.dart'
pdfp = root / 'lib/services/express_round_pdf_service.dart'

screen = screenp.read_text(encoding='utf-8')
pdf = pdfp.read_text(encoding='utf-8')

# No diálogo imediato da IA existe um parâmetro String chamado `context` no
# método. Em Windows/Dart atual ele sombreia State.context. Usa explicitamente
# o BuildContext do State sem alterar a lógica do diálogo.
old = """    final apply = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
"""
new = """    final apply = await showDialog<bool>(
      context: this.context,
      builder: (dialogContext) => AlertDialog(
"""
if old in screen:
    screen = screen.replace(old, new, 1)
elif new not in screen:
    raise RuntimeError('Diálogo imediato da IA não encontrado para compile-safety')

# Company.cnpj é String? na base Windows atual. O PDF da Ronda vinha da base
# Android onde o acesso era tratado como não nulo. Normaliza somente esse campo.
pdf = pdf.replace("company.cnpj.trim()", "(company.cnpj ?? '').trim()")
pdf = pdf.replace("_tableRow('CNPJ', company.cnpj)", "_tableRow('CNPJ', company.cnpj ?? '')")

screenp.write_text(screen, encoding='utf-8', newline='\n')
pdfp.write_text(pdf, encoding='utf-8', newline='\n')

assert 'context: this.context,' in screen
assert "company.cnpj.trim()" not in pdf
assert "_tableRow('CNPJ', company.cnpj ?? '')" in pdf
print('Windows v3.30.4 compile-safety: BuildContext da IA e CNPJ nullable do PDF corrigidos.')
