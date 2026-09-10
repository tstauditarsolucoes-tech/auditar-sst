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
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3610.py')],
        cwd=repo,
        check=True,
    )
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'

    # Versão Windows desta entrega.
    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(
        text,
        'version: 3.36.1+156',
        'version: 3.36.2+157',
        'versão 3.36.2',
    )
    pub.write_text(text, encoding='utf-8')

    # Home Windows: a vistoria rápida/avulsa volta a ficar visível logo abaixo
    # de Nova vistoria, mantendo o layout enxuto da Central Auditar.
    homep = app / 'lib' / 'screens' / 'home_screen.dart'
    home = homep.read_text(encoding='utf-8')
    old_quick = """              if (!Platform.isWindows)\n                Padding(\n                  padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),\n                  child: SizedBox(\n                    width: double.infinity,\n                    child: OutlinedButton.icon(\n                      onPressed: () => _open(const FieldQuickScreen()),\n                      icon: const Icon(Icons.location_on_outlined),\n                      label: const Text('Campo rápido'),\n                    ),\n                  ),\n                ),\n"""
    new_quick = """              Padding(\n                padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),\n                child: SizedBox(\n                  width: double.infinity,\n                  child: OutlinedButton.icon(\n                    onPressed: () => _open(const FieldQuickScreen()),\n                    icon: const Icon(Icons.bolt_rounded),\n                    label: const Text('Vistoria rápida / avulsa'),\n                  ),\n                ),\n              ),\n"""
    home = replace_once(
        home,
        old_quick,
        new_quick,
        'atalho Windows da vistoria rápida/avulsa',
    )
    home = replace_once(
        home,
        "'Escolha a empresa, entre em campo ou acompanhe as pendências gerais',",
        "'Inicie uma vistoria vinculada ou uma vistoria rápida / avulsa e acompanhe as pendências gerais',",
        'descrição de ações principais no Windows',
    )
    home = home.replace('Auditar SST • versão 3.36.1', 'Auditar SST • versão 3.36.2')
    home = home.replace(
        'Auditar SST para Windows • versão 3.36.1',
        'Auditar SST para Windows • versão 3.36.2',
    )
    homep.write_text(home, encoding='utf-8')

    # Campo rápido: no Windows vira uma central própria de vistoria rápida/avulsa,
    # aproveitando tela larga. O fluxo mobile original permanece intacto.
    fieldp = app / 'lib' / 'screens' / 'field_quick_screen.dart'
    field = fieldp.read_text(encoding='utf-8')
    if "import 'dart:io';" not in field:
        field = "import 'dart:io';\n\n" + field

    field = replace_once(
        field,
        """      appBar: AppBar(title: const Text('Campo rápido')),\n      body: ListView(\n""",
        """      appBar: AppBar(\n        title: Text(\n          Platform.isWindows ? 'Vistoria rápida / avulsa' : 'Campo rápido',\n        ),\n      ),\n      body: Platform.isWindows ? _windowsBody() : ListView(\n""",
        'corpo responsivo do Campo rápido',
    )

    windows_layout = r'''
  Widget _windowsBody() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 1050
            ? 3
            : constraints.maxWidth >= 720
                ? 2
                : 1;
        return Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1180),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 32),
              children: [
                Container(
                  padding: const EdgeInsets.all(22),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [AuditarBrand.navyDark, AuditarBrand.navy],
                    ),
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: const [
                      BoxShadow(
                        color: Color(0x180E1A43),
                        blurRadius: 18,
                        offset: Offset(0, 8),
                      ),
                    ],
                  ),
                  child: const Row(
                    children: [
                      Icon(
                        Icons.bolt_rounded,
                        color: AuditarBrand.green,
                        size: 32,
                      ),
                      SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Vistoria rápida / avulsa',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 22,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                            SizedBox(height: 4),
                            Text(
                              'Inicie uma visita de campo sem precisar cadastrar a empresa na carteira. O checklist e o relatório seguem o fluxo normal.',
                              style: TextStyle(
                                color: Colors.white70,
                                height: 1.35,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Como deseja iniciar?',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 10),
                GridView.count(
                  crossAxisCount: columns,
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  mainAxisSpacing: 12,
                  crossAxisSpacing: 12,
                  childAspectRatio: columns == 1
                      ? 3.8
                      : columns == 2
                          ? 2.05
                          : 1.65,
                  children: [
                    _windowsActionCard(
                      icon: Icons.fact_check_outlined,
                      title: 'Vistoria avulsa',
                      subtitle:
                          'Cliente ou local ainda não cadastrado. Informe nome, CNPJ e referência e siga direto para a vistoria.',
                      primary: true,
                      onTap: _busy ? null : _openStandaloneDialog,
                    ),
                    _windowsActionCard(
                      icon: Icons.business_outlined,
                      title: 'Empresa cadastrada',
                      subtitle:
                          'Selecione empresa, unidade / CNPJ, setor e PGR antes de iniciar.',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => const NewInspectionScreen(),
                        ),
                      ),
                    ),
                    _windowsActionCard(
                      icon: Icons.auto_awesome_outlined,
                      title: 'Registrar melhoria',
                      subtitle:
                          'Registre rapidamente uma melhoria ou oportunidade identificada durante a visita.',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => const ImprovementsScreen(),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                Card(
                  margin: EdgeInsets.zero,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.info_outline_rounded,
                          color: AuditarBrand.navy,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            'A vistoria avulsa fica fora da carteira de empresas. Ela serve para atendimento rápido, visita pontual, obra ou local ainda não cadastrado.',
                            style: TextStyle(
                              color: Colors.black.withValues(alpha: .68),
                              height: 1.35,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _windowsActionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback? onTap,
    bool primary = false,
  }) {
    final accent = primary ? AuditarBrand.greenDark : AuditarBrand.navy;
    return Card(
      margin: EdgeInsets.zero,
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 44,
                height: 44,
                decoration: BoxDecoration(
                  color: primary
                      ? AuditarBrand.green.withValues(alpha: .14)
                      : AuditarBrand.navySoft,
                  borderRadius: BorderRadius.circular(13),
                ),
                child: Icon(icon, color: accent),
              ),
              const Spacer(),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                subtitle,
                maxLines: 4,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 12.5, height: 1.3),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Text(
                    primary ? 'Iniciar agora' : 'Abrir',
                    style: TextStyle(
                      color: accent,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Icon(Icons.arrow_forward_rounded, color: accent, size: 17),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

'''
    field = replace_once(
        field,
        '  Widget _actionCard({\n',
        windows_layout + '  Widget _actionCard({\n',
        'layout Windows da vistoria rápida/avulsa',
    )
    fieldp.write_text(field, encoding='utf-8')

    # Validações de preservação: a mudança é de interface/entrada no Windows.
    final_home = homep.read_text(encoding='utf-8')
    final_field = fieldp.read_text(encoding='utf-8')
    checks = {
        'versão': 'version: 3.36.2+157' in pub.read_text(encoding='utf-8'),
        'atalho Windows': "label: const Text('Vistoria rápida / avulsa')" in final_home,
        'layout Windows': 'Widget _windowsBody()' in final_field and 'Widget _windowsActionCard' in final_field,
        'avulsa funcional': '_openStandaloneDialog' in final_field and '_startStandaloneInspection' in final_field,
        'empresa temporária oculta': 'active: false' in final_field,
        'fluxo normal': 'NewInspectionScreen(' in final_field and 'fieldMode: true' in final_field,
        'sync v2': "'syncProtocol': 2" in (app / 'lib' / 'services' / 'device_sync_service.dart').read_text(encoding='utf-8'),
        '44 checklists': (app / 'lib' / 'ready_checklists.dart').read_text(encoding='utf-8').count('  ReadyChecklistDefinition(') == 44,
        'assinatura preservada': 'Assinar em tela cheia' in (app / 'lib' / 'screens' / 'signature_screen.dart').read_text(encoding='utf-8'),
        'multi-CNPJ preservado': 'company_units' in (app / 'lib' / 'database.dart').read_text(encoding='utf-8'),
        'relatório Windows preservado': "? 'Salvar PDF'" in (app / 'lib' / 'screens' / 'report_screen.dart').read_text(encoding='utf-8'),
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Validações v3.36.2 falharam: ' + ', '.join(missing))

    print(f'Fonte v3.36.2 Windows com vistoria rápida/avulsa montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
