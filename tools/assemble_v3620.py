#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run([sys.executable, str(repo / 'tools' / 'assemble_v3610.py')], cwd=repo, check=True)
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.36.1+156', 'version: 3.36.2+157', 'versão 3.36.2')
    pub.write_text(text, encoding='utf-8')

    fieldp = app / 'lib' / 'screens' / 'field_quick_screen.dart'
    field = fieldp.read_text(encoding='utf-8')
    field = replace_once(
        field,
        "class FieldQuickScreen extends StatefulWidget {\n  const FieldQuickScreen({super.key});",
        "class FieldQuickScreen extends StatefulWidget {\n  final bool autoOpenStandalone;\n\n  const FieldQuickScreen({super.key, this.autoOpenStandalone = false});",
        'parâmetro de abertura direta da vistoria avulsa',
    )
    init_insert = """  bool _busy = false;\n\n  @override\n  void initState() {\n    super.initState();\n    if (widget.autoOpenStandalone) {\n      WidgetsBinding.instance.addPostFrameCallback((_) {\n        if (mounted) _openStandaloneDialog();\n      });\n    }\n  }\n\n"""
    field = replace_once(field, "  bool _busy = false;\n\n", init_insert, 'auto abertura da vistoria avulsa')

    build_start = field.find('  @override\n  Widget build(BuildContext context) {')
    helper_start = field.find('  Widget _actionCard({', build_start)
    if build_start < 0 or helper_start < 0:
        raise RuntimeError('Bloco visual do Campo rápido não localizado')

    new_build = r'''  @override
  Widget build(BuildContext context) {
    final wide = MediaQuery.sizeOf(context).width >= 760;
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(title: const Text('Vistoria rápida / avulsa')),
      body: Align(
        alignment: Alignment.topCenter,
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 980),
          child: ListView(
            padding: EdgeInsets.fromLTRB(wide ? 24 : 14, 18, wide ? 24 : 14, 30),
            children: [
              Container(
                padding: EdgeInsets.all(wide ? 24 : 18),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [AuditarBrand.navyDark, AuditarBrand.navy],
                  ),
                  borderRadius: BorderRadius.circular(22),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x160E1A43),
                      blurRadius: 20,
                      offset: Offset(0, 9),
                    ),
                  ],
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: .12),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: Colors.white.withValues(alpha: .16)),
                      ),
                      child: const Icon(
                        Icons.flash_on_rounded,
                        color: AuditarBrand.green,
                        size: 29,
                      ),
                    ),
                    const SizedBox(width: 14),
                    const Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Vistoria rápida / avulsa',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                          SizedBox(height: 5),
                          Text(
                            'Registre uma visita de campo mesmo quando o cliente ainda não está cadastrado. O relatório continua completo e o registro avulso não entra na carteira de empresas.',
                            style: TextStyle(
                              color: Colors.white70,
                              fontSize: 12.5,
                              height: 1.35,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),
              Text(
                'Como deseja iniciar?',
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: AuditarBrand.navy,
                      fontWeight: FontWeight.w900,
                    ),
              ),
              const SizedBox(height: 10),
              if (wide)
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: _standalonePrimaryCard()),
                    const SizedBox(width: 12),
                    Expanded(child: _registeredCompanyCard()),
                  ],
                )
              else ...[
                _standalonePrimaryCard(),
                const SizedBox(height: 10),
                _registeredCompanyCard(),
              ],
              const SizedBox(height: 18),
              Card(
                margin: EdgeInsets.zero,
                elevation: 0,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(18),
                  side: const BorderSide(color: AuditarBrand.line),
                ),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  leading: Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      color: AuditarBrand.navySoft,
                      borderRadius: BorderRadius.circular(13),
                    ),
                    child: const Icon(Icons.auto_awesome_outlined, color: AuditarBrand.navy),
                  ),
                  title: const Text(
                    'Registrar melhoria',
                    style: TextStyle(fontWeight: FontWeight.w900),
                  ),
                  subtitle: const Text('Registre uma melhoria ou oportunidade identificada em campo.'),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => const ImprovementsScreen()),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _standalonePrimaryCard() {
    return Card(
      margin: EdgeInsets.zero,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: BorderSide(color: AuditarBrand.green.withValues(alpha: .48), width: 1.2),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: _busy ? null : _openStandaloneDialog,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 46,
                    height: 46,
                    decoration: BoxDecoration(
                      color: AuditarBrand.green.withValues(alpha: .12),
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.fact_check_outlined, color: AuditarBrand.greenDark),
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
                    decoration: BoxDecoration(
                      color: AuditarBrand.green.withValues(alpha: .10),
                      borderRadius: BorderRadius.circular(999),
                    ),
                    child: const Text(
                      'SEM CADASTRO',
                      style: TextStyle(
                        color: AuditarBrand.greenDark,
                        fontSize: 9.5,
                        fontWeight: FontWeight.w900,
                        letterSpacing: .35,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              const Text(
                'Vistoria avulsa',
                style: TextStyle(
                  color: AuditarBrand.navy,
                  fontSize: 17,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 5),
              const Text(
                'Informe cliente/local, CNPJ opcional e referência. Depois escolha o checklist e faça a vistoria normalmente.',
                style: TextStyle(fontSize: 12.2, height: 1.35, color: Color(0xFF667085)),
              ),
              const SizedBox(height: 15),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: _busy ? null : _openStandaloneDialog,
                  icon: _busy
                      ? const SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.flash_on_rounded),
                  label: Text(_busy ? 'Abrindo...' : 'Iniciar vistoria rápida'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _registeredCompanyCard() {
    return Card(
      margin: EdgeInsets.zero,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: AuditarBrand.line),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute(builder: (_) => const NewInspectionScreen()),
        ),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 46,
                    height: 46,
                    decoration: BoxDecoration(
                      color: AuditarBrand.navySoft,
                      borderRadius: BorderRadius.circular(14),
                    ),
                    child: const Icon(Icons.business_outlined, color: AuditarBrand.navy),
                  ),
                  const Spacer(),
                  const Icon(Icons.chevron_right_rounded, color: AuditarBrand.neutral),
                ],
              ),
              const SizedBox(height: 14),
              const Text(
                'Empresa cadastrada',
                style: TextStyle(
                  color: AuditarBrand.navy,
                  fontSize: 17,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 5),
              const Text(
                'Use a empresa, unidade/CNPJ, setor e PGR que já existem no sistema.',
                style: TextStyle(fontSize: 12.2, height: 1.35, color: Color(0xFF667085)),
              ),
              const SizedBox(height: 15),
              const Text(
                'Selecionar empresa cadastrada',
                style: TextStyle(color: AuditarBrand.navy, fontWeight: FontWeight.w800),
              ),
            ],
          ),
        ),
      ),
    );
  }

'''
    field = field[:build_start] + new_build + field[helper_start:]
    fieldp.write_text(field, encoding='utf-8')

    homep = app / 'lib' / 'screens' / 'home_screen.dart'
    home = homep.read_text(encoding='utf-8')
    home = home.replace("title: 'Campo rápido',", "title: 'Vistoria rápida',", 1)
    home = home.replace(
        "subtitle: 'Vistoria avulsa e registros rápidos fora da carteira',",
        "subtitle: 'Vistoria avulsa sem cadastrar empresa',",
        1,
    )

    old_sidebar = """              if (!Platform.isWindows)\n                Padding(\n                  padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),\n                  child: SizedBox(\n                    width: double.infinity,\n                    child: OutlinedButton.icon(\n                      onPressed: () => _open(const FieldQuickScreen()),\n                      icon: const Icon(Icons.location_on_outlined),\n                      label: const Text('Campo rápido'),\n                    ),\n                  ),\n                ),\n"""
    new_sidebar = """              Padding(\n                padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),\n                child: SizedBox(\n                  width: double.infinity,\n                  child: OutlinedButton.icon(\n                    onPressed: () => _open(\n                      const FieldQuickScreen(autoOpenStandalone: true),\n                    ),\n                    icon: const Icon(Icons.flash_on_rounded),\n                    label: const Text('Vistoria rápida / avulsa'),\n                  ),\n                ),\n              ),\n"""
    home = replace_once(home, old_sidebar, new_sidebar, 'botão lateral da vistoria avulsa')

    old_field_button = """  Widget _fieldQuickButton() {\n    return SizedBox(\n      width: double.infinity,\n      child: OutlinedButton.icon(\n        onPressed: () => _open(const FieldQuickScreen()),\n        icon: const Icon(Icons.location_on_outlined),\n        label: const Text('Campo rápido / vistoria avulsa'),\n      ),\n    );\n  }\n"""
    new_field_button = """  Widget _fieldQuickButton() {\n    return SizedBox(\n      width: double.infinity,\n      child: OutlinedButton.icon(\n        onPressed: () => _open(\n          const FieldQuickScreen(autoOpenStandalone: true),\n        ),\n        icon: const Icon(Icons.flash_on_rounded),\n        label: const Text('Vistoria rápida / avulsa'),\n      ),\n    );\n  }\n"""
    home = replace_once(home, old_field_button, new_field_button, 'botão mobile da vistoria avulsa')
    home = home.replace('Auditar SST • versão 3.36.1', 'Auditar SST • versão 3.36.2')
    home = home.replace('Auditar SST para Windows • versão 3.36.1', 'Auditar SST para Windows • versão 3.36.2')
    homep.write_text(home, encoding='utf-8')

    final_field = fieldp.read_text(encoding='utf-8')
    final_home = homep.read_text(encoding='utf-8')
    checks = {
        'versão': 'version: 3.36.2+157' in pub.read_text(encoding='utf-8'),
        'avulsa direta': 'autoOpenStandalone' in final_field and 'Iniciar vistoria rápida' in final_field,
        'avulsa oculta da carteira': 'active: false' in final_field,
        'layout avulsa': 'SEM CADASTRO' in final_field and 'Como deseja iniciar?' in final_field,
        'atalho home': "const FieldQuickScreen(autoOpenStandalone: true)" in final_home,
        'atalho Windows': "label: const Text('Vistoria rápida / avulsa')" in final_home,
        'sync v2': "'syncProtocol': 2" in (app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8'),
        '44 checklists': (app / 'lib' / 'ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44,
        'assinatura': 'Assinar em tela cheia' in (app / 'lib' / 'screens' / 'signature_screen.dart').read_text(encoding='utf-8'),
        'company_units': 'company_units' in (app / 'lib' / 'database.dart').read_text(encoding='utf-8'),
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações v3.36.2 falharam: ' + ', '.join(missing))

    print(f'Fonte v3.36.2 vistoria rápida/avulsa montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
