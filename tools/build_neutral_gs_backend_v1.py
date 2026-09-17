#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import re
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit('uso: build_neutral_gs_backend_v1.py <app_root> <output_dir>')

root = Path(sys.argv[1]).resolve()
source = root / 'painel_web_google_apps_script'
out = Path(sys.argv[2]).resolve()

if not source.exists():
    raise SystemExit(f'Backend Apps Script não encontrado: {source}')

if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True, exist_ok=True)

# A Central neutra de Vistoria/SST não carrega o módulo de Gestão EPI.
skip = {'EpiSync.gs', 'PATCH_EPI_SYNC_DOPOST.txt'}

for src in source.iterdir():
    if not src.is_file() or src.name in skip:
        continue
    shutil.copy2(src, out / src.name)

text_ext = {'.gs', '.html', '.txt', '.json'}
for path in out.iterdir():
    if path.suffix.lower() not in text_ext:
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')

    # Propriedades e funções de instalação totalmente independentes.
    text = text.replace('AUDITAR_DEVICE_SYNC_VERSION', 'SST_GESTAO_DEVICE_SYNC_VERSION')
    text = text.replace('AUDITAR_SPREADSHEET_ID', 'SST_GESTAO_SPREADSHEET_ID')
    text = text.replace('AUDITAR_SYNC_KEY', 'SST_GESTAO_SYNC_KEY')
    text = text.replace('AUDITAR_AI_MODEL', 'SST_GESTAO_AI_MODEL')
    # Qualquer constante/cache técnico restante da base antiga também recebe
    # prefixo próprio da Central neutra (ex.: WEEKLY_* e AUTH_*).
    text = text.replace('AUDITAR_', 'SST_GESTAO_')
    text = text.replace('setupAuditar', 'setupSstGestao')

    # Identidade visível da Central independente.
    text = text.replace('AUDITAR SST', 'SST GESTÃO')
    text = text.replace('Auditar SST', 'SST Gestão')
    text = text.replace('Auditar Soluções', 'SST Gestão')
    text = text.replace('Auditar Solucoes', 'SST Gestão')
    text = text.replace('Auditar EPI', 'SST Gestão')
    # O restante costuma ser identificador técnico. Use nomes sem espaço para\n    # manter o JavaScript válido; textos visíveis mais comuns já foram tratados acima.\n    text = text.replace('Auditar', 'SstGestao')\n    text = text.replace('auditar', 'sst_gestao')

    path.write_text(text, encoding='utf-8', newline='\n')

code_path = out / 'Code.gs'
if not code_path.exists():
    raise SystemExit('Code.gs não foi gerado')
code = code_path.read_text(encoding='utf-8')

# Remove a rota EPI da Central SST neutra.
code = re.sub(
    r"\n\s*//[^\n]*EPI[^\n]*\n\s*if \(request\.action === 'epi_sync_merge'\) \{.*?\n\s*\}\n",
    '\n',
    code,
    flags=re.S | re.I,
)
code = re.sub(
    r"\n\s*if \(request\.action === 'epi_sync_merge'\) \{.*?\n\s*\}\n",
    '\n',
    code,
    flags=re.S,
)

# Identidade de armazenamento: Drive e planilha são da edição SST Gestão.
code = code.replace("const DRIVE_ROOT_FOLDER = 'SST Gestão';", "const DRIVE_ROOT_FOLDER = 'SST Gestão';")
code_path.write_text(code, encoding='utf-8', newline='\n')

readme = """SST GESTÃO - CENTRAL GOOGLE APPS SCRIPT INDEPENDENTE

OBJETIVO
Esta Central pertence somente ao SST Gestão neutro. Ela não usa a planilha,
a chave, as sessões, a pasta do Drive nem as propriedades da Central Auditar.

FUNÇÕES PRESERVADAS
- Login e primeiro acesso do administrador
- Usuários e permissões
- Sincronização Android <-> Windows
- Empresas, setores, trabalhadores, vistorias, NCs e planos de ação
- Google Drive e envio de relatórios
- Painel gerencial
- CIPA
- Notificações e relatórios mensais
- Assistente IA / Gemini
- Auditoria de usuários e sessões

ARQUIVOS
Use todos os arquivos .gs e .html deste pacote no MESMO projeto Apps Script.

ATIVAÇÃO
1. Crie uma PLANILHA GOOGLE NOVA, exclusiva para o SST Gestão.
2. Nessa planilha: Extensões > Apps Script.
3. Crie/cole os arquivos deste pacote no projeto.
4. Execute manualmente a função setupSstGestao().
5. Autorize as permissões solicitadas.
6. A função criará as abas necessárias, a pasta 'SST Gestão' no Drive e a
   propriedade SST_GESTAO_SYNC_KEY.
7. Em Configurações do projeto > Propriedades do script, confirme:
   SST_GESTAO_SPREADSHEET_ID
   SST_GESTAO_SYNC_KEY
8. Se for usar IA, execute configurarAssistenteIA('SUA_CHAVE_GEMINI', 'modelo').
9. Implantar > Nova implantação > Aplicativo da Web.
   Executar como: você.
   Acesso: qualquer pessoa que tenha o link (o app protege operações por chave
   e sessão; não compartilhe a SST_GESTAO_SYNC_KEY).
10. Copie a URL terminada em /exec.

CONFIGURAÇÃO DO APP NEUTRO
O build do SST Gestão deve receber:
- SST_APPS_SCRIPT_URL = URL /exec desta Central
- SST_SYNC_KEY = valor de SST_GESTAO_SYNC_KEY

NÃO use a URL nem a chave da Central original.
"""
(out / 'LEIA-ME-ATIVACAO.txt').write_text(readme, encoding='utf-8', newline='\n')

# Passagem final defensiva: nenhum arquivo distribuído pode manter o prefixo,
# nome ou função de instalação da Central original.
for path in out.iterdir():
    if path.is_file() and path.suffix.lower() in text_ext:
        text = path.read_text(encoding='utf-8', errors='ignore')
        text = text.replace('AUDITAR_', 'SST_GESTAO_')
        text = text.replace('setupAuditar', 'setupSstGestao')
        text = text.replace('Auditar', 'SstGestao')
        text = text.replace('auditar', 'sst_gestao')
        path.write_text(text, encoding='utf-8', newline='\n')

# Validações: backend independente e sem vestígio de marca/armazenamento antigo.
all_text = '\n'.join(
    p.read_text(encoding='utf-8', errors='ignore')
    for p in out.iterdir()
    if p.is_file() and p.suffix.lower() in text_ext
)
required = [
    'SST_GESTAO_SPREADSHEET_ID',
    'SST_GESTAO_SYNC_KEY',
    'SST_GESTAO_DEVICE_SYNC_VERSION',
    'setupSstGestao',
    'SST Gestão',
]
for token in required:
    if token not in all_text:
        raise SystemExit(f'Backend neutro incompleto: ausente {token}')

for forbidden in [
    'AUDITAR_',
    'AUDITAR_SPREADSHEET_ID',
    'AUDITAR_SYNC_KEY',
    'AUDITAR_DEVICE_SYNC_VERSION',
    'setupAuditar',
    'Auditar SST',
    'AUDITAR SST',
    'Auditar Soluções',
    'Auditar',
    'auditar',
    'epi_sync_merge',
]:
    if forbidden.lower() in all_text.lower():
        raise SystemExit(f'Backend neutro contém referência proibida: {forbidden}')

if (out / 'EpiSync.gs').exists():
    raise SystemExit('EpiSync.gs não pode integrar a Central neutra de vistoria')

print('SST_GESTAO_GS_OK: Central independente gerada com funções SST preservadas e armazenamento separado.')

# Build da Central SST Gestão independente.
