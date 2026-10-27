#!/usr/bin/env python3
from pathlib import Path
import re
import sys

# Patch de acabamento visual v3.24.5 — Android e Windows.
root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')

def read(rel):
    return (root / rel).read_text(encoding='utf-8')

def write(rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')

def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'Marcador não encontrado: {label}')
    return text.replace(old, new, 1)

# Versão: v3.24.4 já ficou reservada ao hotfix SQLite do Windows.
pub = read('pubspec.yaml')
pub = re.sub(r'^version:\s*\d+\.\d+\.\d+\+\d+\s*$', 'version: 3.24.5+105', pub, flags=re.M)
write('pubspec.yaml', pub)

# HOME: acabamento visual + responsividade específica para Windows.
home = read('lib/screens/home_screen.dart')
if "import 'dart:io';" not in home:
    home = home.replace("import 'dart:async';\n", "import 'dart:async';\nimport 'dart:io';\n", 1)

home = home.replace('Auditar SST • versão 3.21.3', 'Auditar SST • versão 3.24.5')
home = home.replace('Auditar SST • versão 3.24.4', 'Auditar SST • versão 3.24.5')
home = home.replace('Auditar SST para Windows • versão 3.21.3', 'Auditar SST para Windows • versão 3.24.5')
home = home.replace('Auditar SST para Windows • versão 3.24.4', 'Auditar SST para Windows • versão 3.24.5')
home = home.replace("'Todos os módulos'", "'Demais módulos'")
home = home.replace("'As funções voltaram a ficar visíveis, sem menus escondidos'", "'Acesse os demais recursos do sistema'")
home = home.replace("'NAVEGAÇÃO COMPLETA'", "'NAVEGAÇÃO'")

marker = "  String loadError = '';\n"
helper = """  String loadError = '';\n\n  bool _useDesktopLayout(double width) {\n    // No Windows, uma janela média já deve aproveitar o menu lateral.\n    // No Android, preservamos o layout de campo até larguras maiores.\n    return Platform.isWindows ? width >= 760 : width >= 900;\n  }\n"""
if '_useDesktopLayout(double width)' not in home:
    home = replace_once(home, marker, helper, 'helper de responsividade')

old_build = """  @override\n  Widget build(BuildContext context) {\n    return Scaffold(\n"""
new_build = """  @override\n  Widget build(BuildContext context) {\n    final screenWidth = MediaQuery.sizeOf(context).width;\n    final desktopLayout = _useDesktopLayout(screenWidth);\n    return Scaffold(\n"""
home = replace_once(home, old_build, new_build, 'estado de responsividade da home')
home = home.replace('if (constraints.maxWidth >= 900) {', 'if (_useDesktopLayout(constraints.maxWidth)) {', 1)
home = home.replace(
    'bottomNavigationBar: MediaQuery.sizeOf(context).width < 900\n          ? NavigationBar(',
    'bottomNavigationBar: desktopLayout\n          ? null\n          : NavigationBar(',
    1,
)
# Fecha o novo ternário sem manter o ": null" da expressão antiga.
home = home.replace(
    """              ],\n            )\n          : null,\n""",
    """              ],\n            ),\n""",
    1,
)
home = home.replace('          width: 292,', "          width: MediaQuery.sizeOf(context).width < 1050 ? 238 : 276,", 1)
home = home.replace('              padding: const EdgeInsets.fromLTRB(24, 22, 24, 32),', '              padding: EdgeInsets.fromLTRB(\n                MediaQuery.sizeOf(context).width < 1050 ? 18 : 24,\n                20,\n                MediaQuery.sizeOf(context).width < 1050 ? 18 : 24,\n                32,\n              ),', 1)
home = home.replace("fontSize: 26,", "fontSize: 24,", 1)
home = home.replace("'Visão completa para organizar empresas, registros e resultados.'", "'Empresas, vistorias, pendências e resultados em um só lugar.'", 1)
home = home.replace("_moduleWrap(_modules.take(4).toList(), minWidth: 210, maxColumns: 4)", "_moduleWrap(_modules.take(4).toList(), minWidth: 190, maxColumns: 4)", 1)
home = home.replace("_moduleWrap(_modules.skip(4).toList(), minWidth: 230, maxColumns: 3)", "_moduleWrap(_modules.skip(4).toList(), minWidth: 205, maxColumns: 3)", 1)
write('lib/screens/home_screen.dart', home)

# CONFIGURAÇÕES: reduzir ruído no celular e deixar controles técnicos no PC.
settings = read('lib/screens/settings_screen.dart')
if "import 'dart:io';" not in settings:
    settings = settings.replace("import 'dart:async';\n", "import 'dart:async';\nimport 'dart:io';\n", 1)

sync_start = """          const SizedBox(height: 28),\n          Text(\n            'Sincronização celular e computador',\n"""
if "if (Platform.isWindows) ...[\n          const SizedBox(height: 28),\n          Text(\n            'Sincronização celular e computador'," not in settings:
    settings = replace_once(
        settings,
        sync_start,
        """          if (Platform.isWindows) ...[\n          const SizedBox(height: 28),\n          Text(\n            'Sincronização celular e computador',\n""",
        'início do bloco de sincronização Windows',
    )
    google_marker = """          const SizedBox(height: 28),\n          Text(\n            'Google Drive',\n"""
    settings = replace_once(
        settings,
        google_marker,
        """          ],\n          const SizedBox(height: 28),\n          Text(\n            'Google Drive',\n""",
        'fim do bloco de sincronização Windows',
    )

settings = settings.replace("'Serviços web gratuitos'", "'Conexões do sistema'")
settings = settings.replace(
    "'A mesma publicação do Google Apps Script atende o Painel Gerencial, a votação CIPA por QR Code e a conexão segura do Assistente IA.'",
    "'Configuração usada pelo Painel Gerencial, votação CIPA e recursos online do aplicativo.'",
)
settings = settings.replace(
    "'Configuração única usada para publicar os links individuais das empresas. Depois de configurada, cada empresa terá seu próprio endereço de consulta.'",
    "'A configuração já vem pronta nas versões distribuídas pela Auditar.'",
)
write('lib/screens/settings_screen.dart', settings)

# NOVA VISTORIA: no PC, evitar formulário esticado de ponta a ponta.
new_inspection = read('lib/screens/new_inspection_screen.dart')
old_body = """      body: ListView(\n        padding: const EdgeInsets.all(16),\n        children: [\n"""
new_body = """      body: Center(\n        child: ConstrainedBox(\n          constraints: const BoxConstraints(maxWidth: 820),\n          child: ListView(\n            padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),\n            children: [\n"""
if 'constraints: const BoxConstraints(maxWidth: 820)' not in new_inspection:
    new_inspection = replace_once(new_inspection, old_body, new_body, 'largura máxima da nova vistoria')
    old_end = """        ],\n      ),\n    );\n  }\n}\n\n"""
    new_end = """            ],\n          ),\n        ),\n      ),\n    );\n  }\n}\n\n"""
    if not new_inspection.endswith(old_end):
        raise RuntimeError('Fim da tela Nova vistoria não encontrado.')
    new_inspection = new_inspection[:-len(old_end)] + new_end
write('lib/screens/new_inspection_screen.dart', new_inspection)

note = root / 'MUDANCAS_V3_24_5_ACABAMENTO_VISUAL.txt'
note.write_text(
    'Auditar SST v3.24.5 — acabamento visual\n\n'
    '- Mantém o hotfix SQLite v3.24.4 no Windows.\n'
    '- Corrige versão exibida no rodapé para 3.24.5.\n'
    '- Melhora a responsividade do Windows em janelas médias.\n'
    '- Menu lateral do PC mais compacto e conteúdo com melhor aproveitamento.\n'
    '- Textos da tela inicial revisados para uso profissional.\n'
    '- Configurações de sincronização ficam discretas e específicas do Windows.\n'
    '- Tela Nova vistoria ganha largura máxima no PC para facilitar leitura e preenchimento.\n'
    '- Nenhuma alteração de estrutura de dados, regras de checklist ou protocolo de sincronização.\n',
    encoding='utf-8',
)

print('v3.24.5: acabamento visual aplicado.')
