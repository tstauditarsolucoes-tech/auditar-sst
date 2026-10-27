#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
p = root / 'lib/services/dds_pdf_service.dart'
text = p.read_text(encoding='utf-8')

old = """    if (company == null) throw StateError('Empresa do DDS não encontrada.');

    final sectors = await AppDatabase.instance.getSectors(companyId, onlyActive: false);
"""
new = """    final resolvedCompany = company;
    if (resolvedCompany == null) {
      throw StateError('Empresa do DDS não encontrada.');
    }

    final sectors = await AppDatabase.instance.getSectors(companyId, onlyActive: false);
"""
if 'final resolvedCompany = company;' not in text:
    if old not in text:
        raise RuntimeError('Marcador de empresa não localizado')
    text = text.replace(old, new, 1)

text = text.replace('final companyLogo = await _loadFileImage(company.logoPath);',
                    'final companyLogo = await _loadFileImage(resolvedCompany.logoPath);')
text = text.replace("['Empresa', company.name, 'CNPJ', (company.cnpj ?? '').trim().isEmpty ? '-' : company.cnpj!.trim()],",
                    "['Empresa', resolvedCompany.name, 'CNPJ', (resolvedCompany.cnpj ?? '').trim().isEmpty ? '-' : resolvedCompany.cnpj!.trim()],")

p.write_text(text, encoding='utf-8', newline='\n')
final = p.read_text(encoding='utf-8')
assert 'final resolvedCompany = company;' in final
assert '_loadFileImage(resolvedCompany.logoPath)' in final
assert "['Empresa', resolvedCompany.name" in final
assert "['Empresa', company.name" not in final
print('Compile fix v3.29.48 aplicado: empresa promovida para valor não nulo no PDF DDS.')
