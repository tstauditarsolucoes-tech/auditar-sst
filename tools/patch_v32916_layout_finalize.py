#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    app = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('app/Auditar_SST_v1_5_dashboard')

    # Completa o layout refinado da Central Auditar sem mexer nos fluxos de IA.
    homep = app / 'lib' / 'screens' / 'home_screen.dart'
    home = homep.read_text(encoding='utf-8')

    home = replace_once(
        home,
        "      if (mounted && result.received > 0) _refresh();",
        "      if (mounted && result.received > 0) {\n        unawaited(_refresh(showLoading: false));\n      }",
        'refresh silencioso após sincronização',
    )
    home = replace_once(
        home,
        "  Future<void> _refresh() async {\n    if (mounted) setState(() { loading = true; loadError = ''; });",
        "  Future<void> _refresh({bool showLoading = true}) async {\n    if (showLoading && mounted) {\n      setState(() {\n        loading = true;\n        loadError = '';\n      });\n    }",
        'assinatura do refresh silencioso',
    )
    home = replace_once(
        home,
        "    } catch (e) {\n      if (!mounted) return;\n      setState(() {\n        loading = false;\n        loadError = '$e'.replaceFirst('Bad state: ', '').trim();\n      });\n    }",
        "    } catch (e) {\n      if (!mounted) return;\n      if (showLoading) {\n        setState(() {\n          loading = false;\n          loadError = '$e'.replaceFirst('Bad state: ', '').trim();\n        });\n      }\n    }",
        'erro do refresh silencioso',
    )
    home = replace_once(
        home,
        "    await _refresh();\n  }\n\n  Future<void> _showModules()",
        "    await _refresh(showLoading: false);\n  }\n\n  Future<void> _showModules()",
        'refresh depois da navegação',
    )
    home = replace_once(
        home,
        "            onPressed: _refresh,\n            icon: const Icon(Icons.refresh_rounded),",
        "            onPressed: () => _refresh(showLoading: false),\n            icon: const Icon(Icons.refresh_rounded),",
        'botão atualizar sem tela de loading',
    )

    home = home.replace("    final conformity = summary['conformity'] ?? 0;\n", '', 1)
    old_header = """            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Visão geral',
                    style: TextStyle(
                      color: AuditarBrand.navy,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
                Text(
                  '$conformity% conforme',
                  style: TextStyle(
                    color: conformity >= 80
                        ? AuditarBrand.greenDark
                        : AuditarBrand.warning,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ],
            ),
"""
    new_header = """            const Row(
              children: [
                Expanded(
                  child: Text(
                    'Prioridades da carteira',
                    style: TextStyle(
                      color: AuditarBrand.navy,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
                Text(
                  'Todas as empresas',
                  style: TextStyle(
                    color: AuditarBrand.neutral,
                    fontSize: 11.5,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
"""
    home = replace_once(home, old_header, new_header, 'título das prioridades da carteira')
    home = home.replace('maxColumns: desktop ? 6 : 2,', 'maxColumns: desktop ? 5 : 2,', 1)
    home = replace_once(
        home,
        "                _metric('Conformidade', conformity, Icons.verified_outlined, AuditarBrand.greenDark, suffix: '%'),\n",
        '',
        'remover conformidade duplicada das prioridades',
    )
    homep.write_text(home, encoding='utf-8')

    # Ações rápidas dentro da empresa selecionada, como no layout refinado citado.
    detailp = app / 'lib' / 'screens' / 'company_detail_screen.dart'
    detail = detailp.read_text(encoding='utf-8')
    detail = replace_once(
        detail,
        "import 'management_panel_screen.dart';\n",
        "import 'management_panel_screen.dart';\nimport 'new_inspection_screen.dart';\n",
        'import da nova vistoria na empresa',
    )
    detail = replace_once(
        detail,
        """          const SizedBox(height: 10),
          ResponsiveWrap(
            minItemWidth: 138,
            maxColumns: 3,
""",
        """          const SizedBox(height: 12),
          _companyQuickActions(),
          const SizedBox(height: 12),
          ResponsiveWrap(
            minItemWidth: 138,
            maxColumns: 3,
""",
        'atalhos da empresa acima dos indicadores',
    )
    quick_actions = r'''
  Widget _companyQuickActions() {
    return ResponsiveWrap(
      minItemWidth: 175,
      maxColumns: 2,
      spacing: 9,
      runSpacing: 9,
      children: [
        _shortcut(
          icon: Icons.add_task_rounded,
          title: 'Nova vistoria',
          subtitle: 'Iniciar já vinculada a esta empresa',
          onTap: () => _open(
            NewInspectionScreen(initialCompany: widget.company),
          ),
        ),
        _shortcut(
          icon: Icons.description_outlined,
          title: 'PGR + IA',
          subtitle: hasPgr
              ? 'PGR disponível para consulta e análise'
              : 'Cadastrar ou analisar PGR',
          onTap: () => _open(PgrScreen(company: widget.company)),
        ),
      ],
    );
  }

'''
    detail = replace_once(
        detail,
        '  Widget _inspectionsTab() {',
        quick_actions + '  Widget _inspectionsTab() {',
        'método de atalhos da empresa',
    )
    detailp.write_text(detail, encoding='utf-8')

    checks = {
        'prioridades': 'Prioridades da carteira' in homep.read_text(encoding='utf-8'),
        'todas empresas': 'Todas as empresas' in homep.read_text(encoding='utf-8'),
        'refresh silencioso': '_refresh(showLoading: false)' in homep.read_text(encoding='utf-8'),
        'nova vistoria empresa': "title: 'Nova vistoria'" in detailp.read_text(encoding='utf-8'),
        'PGR IA empresa': "title: 'PGR + IA'" in detailp.read_text(encoding='utf-8'),
        'vistoria avulsa': 'Vistoria rápida / avulsa' in (app / 'lib' / 'screens' / 'field_quick_screen.dart').read_text(encoding='utf-8'),
        'IA foto': "'mode': 'checklist_photo'" in (app / 'lib' / 'services' / 'ai_assistant_service.dart').read_text(encoding='utf-8'),
        'PGR múltiplo': 'Adicionar outro PGR' in (app / 'lib' / 'screens' / 'pgr_screen.dart').read_text(encoding='utf-8'),
    }
    missing = [name for name, ok in checks.items() if not ok]
    if missing:
        raise RuntimeError('Finalização de layout v3.29.16 falhou: ' + ', '.join(missing))

    print('Layout v3.29.16 finalizado: prioridades, atalhos da empresa e refresh silencioso.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
