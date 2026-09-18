#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys

if len(sys.argv) < 3:
    raise SystemExit("uso: compact_gs_backend.py <source_dir> <output_dir>")

src = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()

if not src.exists():
    raise SystemExit(f"pasta ausente: {src}")

if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True, exist_ok=True)

gs_files = sorted(src.glob("*.gs"), key=lambda p: (p.name != "Code.gs", p.name.lower()))
if not gs_files:
    raise SystemExit("nenhum .gs encontrado")

parts = []
for p in gs_files:
    parts.append(f"\n// ===== {p.name} =====\n")
    parts.append(p.read_text(encoding="utf-8", errors="strict"))
    parts.append("\n")

(out / "Code.gs").write_text("".join(parts), encoding="utf-8", newline="\n")

for html in src.glob("*.html"):
    shutil.copy2(html, out / html.name)

manifest = """{
  "timeZone": "America/Fortaleza",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8"
}
"""
(out / "appsscript.json").write_text(manifest, encoding="utf-8", newline="\n")

instructions = """SST GESTÃO - CENTRAL GS v1.1.0 EPI - PACOTE COMPACTO

Arquivos para criar no Google Apps Script:
1. Code.gs
2. Index.html (se presente neste pacote)
3. Votacao.html (se presente neste pacote)

ATIVAÇÃO
1. Crie uma planilha Google nova e exclusiva para o SST Gestão.
2. Abra Extensões > Apps Script.
3. Substitua o conteúdo de Code.gs pelo Code.gs deste pacote.
4. Se existirem Index.html e Votacao.html neste pacote, crie arquivos HTML com
   exatamente esses nomes e cole o conteúdo correspondente.
5. Salve.
6. Execute setupSstGestao() uma vez e autorize as permissões.
7. Em Configurações do projeto > Propriedades do script, confira:
   SST_GESTAO_SPREADSHEET_ID
   SST_GESTAO_SYNC_KEY
8. Para IA/Gemini, configure GEMINI_API_KEY nas Propriedades do script.
9. Implantar > Nova implantação > Aplicativo da Web.
   Executar como: você.
   Quem pode acessar: qualquer pessoa.
10. Copie a URL terminada em /exec.

NÃO use URL nem chave da Central original.
"""
(out / "PASSO-A-PASSO.txt").write_text(instructions, encoding="utf-8", newline="\n")

print(f"GS_COMPACT_OK: {len(gs_files)} arquivos .gs reunidos em Code.gs")
