#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
repo = Path(sys.argv[2] if len(sys.argv) > 2 else '.').resolve()


def read(rel):
    return (root / rel).read_text(encoding='utf-8')


def write(rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def rep(text, old, new, label, count=1):
    if old not in text:
        raise RuntimeError(f'marcador não encontrado: {label}')
    return text.replace(old, new, count)

source_dir = repo / 'build_sources' / 'v3.29.30-tutorial'
write('lib/services/tutorial_service.dart', (source_dir / 'tutorial_service.dart').read_text(encoding='utf-8'))
write('lib/widgets/tutorial_bubble.dart', (source_dir / 'tutorial_bubble.dart').read_text(encoding='utf-8'))

pub = read('pubspec.yaml')
pub = rep(pub, 'version: 3.29.28+171', 'version: 3.29.30+172', 'versão 3.29.28')
write('pubspec.yaml', pub)

home = read('lib/screens/home_screen.dart')
home = rep(home, "import '../widgets/responsive_wrap.dart';\n", "import '../widgets/responsive_wrap.dart';\nimport '../widgets/tutorial_bubble.dart';\n", 'import tutorial home')
module_tutorials = {
    "title: 'Empresas',": "title: 'Empresas',\n          tutorialId: 'companies',",
    "title: 'Vistoria rápida',": "title: 'Vistoria rápida',\n          tutorialId: 'field_quick',",
    "title: 'Vistorias',": "title: 'Vistorias',\n          tutorialId: 'history',",
    "title: 'Não conformidades',": "title: 'Não conformidades',\n          tutorialId: 'non_conformities',",
    "title: 'Planos de ação',": "title: 'Planos de ação',\n          tutorialId: 'action_plan',",
    "title: 'Trabalhadores',": "title: 'Trabalhadores',\n          tutorialId: 'workers',",
    "title: 'Treinamentos',": "title: 'Treinamentos',\n          tutorialId: 'trainings',",
    "title: 'Alertas e obrigações',": "title: 'Alertas e obrigações',\n          tutorialId: 'compliance_alerts',",
    "title: 'CIPA',": "title: 'CIPA',\n          tutorialId: 'cipa',",
    "title: 'Biblioteca de checklists',": "title: 'Biblioteca de checklists',\n          tutorialId: 'checklists',",
    "title: 'Rotina SST',": "title: 'Rotina SST',\n          tutorialId: 'routine',",
    "title: 'Melhorias',": "title: 'Melhorias',\n          tutorialId: 'improvements',",
    "title: 'Indicadores',": "title: 'Indicadores',\n          tutorialId: 'dashboard',",
}
for old, new in module_tutorials.items():
    home = rep(home, old, new, f'módulo {old}', count=1)
home = rep(home, """  Future<void> _open(Widget page) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => page),
    );
    await _refresh(showLoading: false);
  }
""", """  Future<void> _open(Widget page, {String? tutorialId}) async {
    final destination = tutorialId == null
        ? page
        : TutorialScreenShell(tutorialId: tutorialId, child: page);
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => destination),
    );
    await _refresh(showLoading: false);
  }
""", 'método _open tutorial')
home = rep(home, """          IconButton(
            tooltip: 'Configurações',
            onPressed: () => _open(const SettingsScreen()),
            icon: const Icon(Icons.settings_outlined),
          ),
""", """          IconButton(
            tooltip: 'Ajuda rápida',
            onPressed: () => TutorialCoach.show(context, 'home', force: true),
            icon: const Icon(Icons.help_outline_rounded),
          ),
          IconButton(
            tooltip: 'Configurações',
            onPressed: () => _open(
              const SettingsScreen(),
              tutorialId: 'settings',
            ),
            icon: const Icon(Icons.settings_outlined),
          ),
""", 'ajuda home')
home = home.replace("_open(const CompaniesScreen());", "_open(const CompaniesScreen(), tutorialId: 'companies');")
home = home.replace("_open(const HistoryScreen());", "_open(const HistoryScreen(), tutorialId: 'history');")
home = home.replace("_open(const NewInspectionScreen())", "_open(const NewInspectionScreen(), tutorialId: 'new_inspection')")
home = home.replace("_open(const SettingsScreen())", "_open(const SettingsScreen(), tutorialId: 'settings')")
home = home.replace("_open(const HistoryScreen(resumeLatestDraft: true))", "_open(const HistoryScreen(resumeLatestDraft: true), tutorialId: 'history')")
home = home.replace("_open(const FieldQuickScreen())", "_open(const FieldQuickScreen(), tutorialId: 'field_quick')")
home = home.replace("_open(const RoutineHubScreen())", "_open(const RoutineHubScreen(), tutorialId: 'routine')")
home = home.replace("onTap: () => _open(module.page()),", "onTap: () => _open(module.page(), tutorialId: module.tutorialId),")
home = home.replace("onTap: () => _open(const CompaniesScreen()),", "onTap: () => _open(const CompaniesScreen(), tutorialId: 'companies'),")
home = home.replace('versão 3.29.28', 'versão 3.29.30')
home = rep(home, """class _ModuleData {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;
  final Widget Function() page;

  const _ModuleData({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
    required this.page,
  });
}
""", """class _ModuleData {
  final String title;
  final String subtitle;
  final String tutorialId;
  final IconData icon;
  final Color color;
  final Widget Function() page;

  const _ModuleData({
    required this.title,
    required this.subtitle,
    required this.tutorialId,
    required this.icon,
    required this.color,
    required this.page,
  });
}
""", 'modelo _ModuleData')
write('lib/screens/home_screen.dart', home)

for rel in ['lib/screens/splash_screen.dart', 'lib/screens/login_screen.dart']:
    text = read(rel)
    text = rep(text, "import '../widgets/auditar_brand_logo.dart';\n", "import '../widgets/auditar_brand_logo.dart';\nimport '../widgets/tutorial_bubble.dart';\n", f'import tutorial {rel}')
    if rel.endswith('splash_screen.dart'):
        text = rep(text, '? const HomeScreen()', "? const TutorialScreenShell(\n                  tutorialId: 'home',\n                  child: HomeScreen(),\n                )", 'home splash')
    else:
        text = text.replace('MaterialPageRoute(builder: (_) => const HomeScreen())', "MaterialPageRoute(\n          builder: (_) => const TutorialScreenShell(\n            tutorialId: 'home',\n            child: HomeScreen(),\n          ),\n        )")
        if text.count("tutorialId: 'home'") < 2:
            raise RuntimeError('rotas de login para Home não foram atualizadas')
    write(rel, text)

companies = read('lib/screens/companies_screen.dart')
companies = rep(companies, "import '../models.dart';\n", "import '../models.dart';\nimport '../widgets/tutorial_bubble.dart';\n", 'import tutorial empresas')
companies = rep(companies, 'MaterialPageRoute(builder: (_) => CompanyDetailScreen(company: company))', "MaterialPageRoute(\n              builder: (_) => TutorialScreenShell(\n                tutorialId: 'company_detail',\n                child: CompanyDetailScreen(company: company),\n              ),\n            )", 'rota detalhe empresa')
write('lib/screens/companies_screen.dart', companies)

settings = read('lib/screens/settings_screen.dart')
settings = rep(settings, "import '../services/drive_service.dart';\n", "import '../services/drive_service.dart';\nimport '../services/tutorial_service.dart';\n", 'import tutorial settings')
settings = rep(settings, '  Future<void> _logout() async {\n', """  Future<void> _resetTutorial() async {
    await TutorialService.resetForCurrentAccount();
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text(
          'Mini tutorial reativado. As dicas aparecerão novamente quando você abrir cada área.',
        ),
      ),
    );
  }

  Future<void> _logout() async {
""", 'método reset tutorial')
settings = rep(settings, """          const SizedBox(height: 28),
          Text(
            'Preferências',
""", """          const SizedBox(height: 24),
          Text(
            'Ajuda e mini tutorial',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Icon(Icons.lightbulb_outline_rounded),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'O aplicativo mostra uma dica curta na primeira vez que cada área é aberta. O tutorial pode ser pulado a qualquer momento.',
                          style: TextStyle(fontSize: 12.8, height: 1.35),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: _resetTutorial,
                    icon: const Icon(Icons.replay_rounded),
                    label: const Text('Reiniciar mini tutorial'),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 28),
          Text(
            'Preferências',
""", 'card tutorial settings')
write('lib/screens/settings_screen.dart', settings)

write('ALTERACOES_v3.29.30.txt', '''AUDITAR SST v3.29.30+172 — MINI TUTORIAL GUIADO\n\nNOVO\n- Mini tutorial guiado e pulável no Android e Windows.\n- Exibido automaticamente na primeira vez que cada área principal é aberta.\n- Estado do tutorial separado por conta: uma conta nova recebe as dicas mesmo em um aparelho já usado.\n- Uma instalação nova também inicia o tutorial normalmente.\n- Balões curtos em linguagem simples explicam o objetivo e o uso das principais áreas.\n- Botão “Pular tutorial” na apresentação inicial e “Parar dicas” nas demais telas.\n- Botão de ajuda na tela inicial para rever a dica principal.\n- Configurações > Ajuda e mini tutorial > Reiniciar mini tutorial permite reativar todas as dicas.\n\nÁREAS COBERTAS\n- Início\n- Empresas\n- Área da empresa\n- Vistoria rápida\n- Vistorias\n- Não conformidades\n- Planos de ação\n- Trabalhadores\n- Treinamentos\n- Alertas e obrigações\n- CIPA\n- Biblioteca de checklists\n- Rotina SST\n- Melhorias\n- Indicadores\n- Nova vistoria\n- Configurações\n\nPRESERVADO\n- Login e contas\n- Sincronização celular/PC\n- IA\n- Ronda Expressa\n- Relatórios\n- Painel Gerencial\n- Biblioteca de 248 checklists\n- Todos os dados e recursos existentes\n''')

checks = {
    'pubspec.yaml': ['version: 3.29.30+172'],
    'lib/screens/home_screen.dart': ["tutorialId: 'companies'", 'Ajuda rápida', 'versão 3.29.30'],
    'lib/screens/settings_screen.dart': ['Reiniciar mini tutorial'],
    'lib/screens/login_screen.dart': ["tutorialId: 'home'"],
    'lib/screens/splash_screen.dart': ["tutorialId: 'home'"],
    'lib/widgets/tutorial_bubble.dart': ['Pular tutorial', 'Parar dicas', 'TutorialScreenShell'],
    'lib/services/tutorial_service.dart': ['resetForCurrentAccount', 'disableAll'],
}
for rel, needles in checks.items():
    text = read(rel)
    for needle in needles:
        if needle not in text:
            raise RuntimeError(f'validação falhou em {rel}: {needle}')

print('v3.29.30+172: mini tutorial aplicado com sucesso.')
