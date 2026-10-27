#!/usr/bin/env python3
from pathlib import Path
import runpy
import sys

if len(sys.argv) < 2:
    raise SystemExit('Uso: patch_windows_dds_mobile_module_v3301.py <app_dir>')

root = Path(sys.argv[1])
pubp = root / 'pubspec.yaml'
repo_tools = Path(__file__).resolve().parent


def run_patch(name: str) -> None:
    old = sys.argv[:]
    try:
        sys.argv = [str(repo_tools / name), str(root)]
        runpy.run_path(sys.argv[0], run_name='__main__')
    finally:
        sys.argv = old


# A base gerencial Windows já está em 3.30.0. Os patches DDS foram escritos
# numa linha Android 3.29.x, mas suas alterações são Flutter multiplataforma.
# Usamos apenas um shim temporário de versão para reaproveitar exatamente o
# módulo já testado no celular; ao final restauramos a linha Windows.
pub = pubp.read_text(encoding='utf-8')
if 'version: 3.30.0+187' not in pub:
    raise RuntimeError('Base Windows v3.30.0+187 não encontrada')
pubp.write_text(pub.replace('version: 3.30.0+187', 'version: 3.29.46+188', 1), encoding='utf-8', newline='\n')

run_patch('patch_dds_digital_signature_v32947.py')
run_patch('patch_dds_formal_pdf_v32948.py')
run_patch('patch_dds_formal_pdf_compile_fix_v32948.py')

# O ajuste de setor opcional veio depois de patches Android de transporte/sync,
# que não devem ser copiados para Windows. Avançamos apenas a etiqueta de versão
# para aplicar o ajuste funcional de DDS e PDF.
pub = pubp.read_text(encoding='utf-8')
if 'version: 3.29.48+190' not in pub:
    raise RuntimeError('Módulo formal DDS v3.29.48 não aplicado')
pubp.write_text(pub.replace('version: 3.29.48+190', 'version: 3.29.51+193', 1), encoding='utf-8', newline='\n')
run_patch('patch_dds_sector_optional_v32952.py')

# Retorna para a linha de versão do PC; o patch consolidado v3.30.1 fará o bump.
pub = pubp.read_text(encoding='utf-8')
if 'version: 3.29.52+194' not in pub:
    raise RuntimeError('Ajuste de setor opcional não aplicado')
pubp.write_text(pub.replace('version: 3.29.52+194', 'version: 3.30.0+187', 1), encoding='utf-8', newline='\n')

form = (root / 'lib/screens/sst_record_form_screen.dart').read_text(encoding='utf-8')
listing = (root / 'lib/screens/sst_records_screen.dart').read_text(encoding='utf-8')
media = (root / 'lib/services/media_sync_service.dart').read_text(encoding='utf-8')
pdf = (root / 'lib/services/dds_pdf_service.dart').read_text(encoding='utf-8')
capture = root / 'lib/screens/dds_signature_capture_screen.dart'

assert capture.exists()
assert 'registerDdsSignature({' in media
assert 'ddsSignatureLocalPath({' in media
assert 'Selecionar colaboradores' in form
assert 'Participantes adicionais (opcional)' in form
assert "widget.type == 'DDS' ? 'Setor (opcional)' : 'Setor'" in form
assert 'Future<void> _generateDdsPdf' in listing
assert 'Gerar PDF / lista de presença' in listing
assert 'REGISTRO DE DDS' in pdf
assert 'LISTA DE PRESENÇA E ASSINATURAS' in pdf
assert "selectedSector.isEmpty ? 'Não se aplica / sem setor' : selectedSector" in pdf
assert 'version: 3.30.0+187' in pubp.read_text(encoding='utf-8')
print('DDS mobile portado para Windows: assinatura, colaboradores, setor opcional e ficha PDF formal.')
