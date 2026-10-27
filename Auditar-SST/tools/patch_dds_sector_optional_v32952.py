#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
formp = root / 'lib/screens/sst_record_form_screen.dart'
pdfp = root / 'lib/services/dds_pdf_service.dart'

pub = pubp.read_text(encoding='utf-8')
form = formp.read_text(encoding='utf-8')
pdf = pdfp.read_text(encoding='utf-8')

if 'version: 3.29.52+194' not in pub:
    if 'version: 3.29.51+193' not in pub:
        raise RuntimeError('Base v3.29.51+193 não encontrada')
    pub = pub.replace('version: 3.29.51+193', 'version: 3.29.52+194', 1)

old_decoration = "                    decoration: const InputDecoration(labelText: 'Setor'),\n"
new_decoration = "                    decoration: InputDecoration(labelText: widget.type == 'DDS' ? 'Setor (opcional)' : 'Setor'),\n"
if new_decoration not in form:
    if old_decoration not in form:
        raise RuntimeError('Campo Setor não localizado')
    form = form.replace(old_decoration, new_decoration, 1)

old_empty = "                      const DropdownMenuItem<String>(value: '', child: Text('Sem setor específico')),\n"
new_empty = "                      DropdownMenuItem<String>(value: '', child: Text(widget.type == 'DDS' ? 'Sem setor / não se aplica' : 'Sem setor específico')),\n"
if new_empty not in form:
    if old_empty not in form:
        raise RuntimeError('Opção sem setor não localizada')
    form = form.replace(old_empty, new_empty, 1)

old_pdf = "['Duração', duration.isEmpty ? '-' : duration, 'Setor', selectedSector.isEmpty ? 'Geral / não informado' : selectedSector],"
new_pdf = "['Duração', duration.isEmpty ? '-' : duration, 'Setor', selectedSector.isEmpty ? 'Não se aplica / sem setor' : selectedSector],"
if new_pdf not in pdf:
    if old_pdf not in pdf:
        raise RuntimeError('Linha Setor do PDF DDS não localizada')
    pdf = pdf.replace(old_pdf, new_pdf, 1)

# O setor já é nullable no SstRecord. Garantimos que o DDS continue salvando
# selectedSectorId diretamente, sem validator e sem valor artificial obrigatório.
sector_block_start = form.find("DropdownButtonFormField<String>(\n                    isExpanded: true,\n                    value: selectedSectorId ?? '',")
if sector_block_start < 0:
    raise RuntimeError('Dropdown de setor não encontrado para validação')
sector_block_end = form.find('                  ),', sector_block_start)
if sector_block_end < 0:
    raise RuntimeError('Fim do dropdown de setor não encontrado')
sector_block = form[sector_block_start:sector_block_end]
if 'validator:' in sector_block:
    raise RuntimeError('Setor ainda possui validator obrigatório')
if 'sectorId: selectedSectorId,' not in form:
    raise RuntimeError('SstRecord não aceita selectedSectorId diretamente')

pubp.write_text(pub, encoding='utf-8', newline='\n')
formp.write_text(form, encoding='utf-8', newline='\n')
pdfp.write_text(pdf, encoding='utf-8', newline='\n')

assert 'version: 3.29.52+194' in pubp.read_text(encoding='utf-8')
assert "widget.type == 'DDS' ? 'Setor (opcional)' : 'Setor'" in formp.read_text(encoding='utf-8')
assert "widget.type == 'DDS' ? 'Sem setor / não se aplica' : 'Sem setor específico'" in formp.read_text(encoding='utf-8')
assert "selectedSector.isEmpty ? 'Não se aplica / sem setor' : selectedSector" in pdfp.read_text(encoding='utf-8')
print('v3.29.52 aplicada: Setor explicitamente opcional no DDS e PDF tolerante a ausência de setor.')
