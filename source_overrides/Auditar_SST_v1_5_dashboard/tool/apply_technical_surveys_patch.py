from pathlib import Path

home = Path('lib/screens/home_screen.dart')
text = home.read_text(encoding='utf-8')

import_line = "import 'technical_surveys_screen.dart';\n"
if import_line not in text:
    anchor = "import 'settings_screen.dart';\n"
    if anchor not in text:
        raise SystemExit('Não foi possível localizar o bloco de imports da HomeScreen.')
    text = text.replace(anchor, anchor + import_line, 1)

if "title: 'Levantamentos técnicos'" not in text:
    anchor = "        _ModuleData(\n          title: 'Vistorias',"
    if anchor not in text:
        raise SystemExit('Não foi possível localizar o módulo Vistorias na HomeScreen.')
    block = """        _ModuleData(
          title: 'Levantamentos técnicos',
          subtitle: 'Coleta para ESO e laudo de acessibilidade com Assistente IA',
          icon: Icons.assignment_add,
          color: const Color(0xFF1E6F63),
          page: () => const TechnicalSurveysScreen(),
        ),
"""
    text = text.replace(anchor, block + anchor, 1)

home.write_text(text, encoding='utf-8')
print('Levantamentos técnicos conectados à HomeScreen.')
