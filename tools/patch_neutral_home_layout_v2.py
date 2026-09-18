#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1] if len(sys.argv)>1 else 'app/Auditar_SST_v1_5_dashboard')
path=root/'lib/screens/home_screen.dart'
text=path.read_text(encoding='utf-8')

def replace_between(src,start,end,new):
    a=src.find(start)
    if a<0: raise SystemExit('Marcador inicial não encontrado: '+start)
    b=src.find(end,a)
    if b<0: raise SystemExit('Marcador final não encontrado: '+end)
    return src[:a]+new+src[b:]

mobile=r'''  Widget _mobileBody() {
    const quickIds = {'companies', 'epi', 'field_quick', 'history'};
    final quickModules = _modules
        .where((module) => quickIds.contains(module.tutorialId))
        .toList(growable: false);
    final moreModules = _modules
        .where((module) => !quickIds.contains(module.tutorialId))
        .toList(growable: false);

    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView(
        controller: _mobileScrollController,
        padding: const EdgeInsets.fromLTRB(14, 12, 14, 26),
        children: [
          _workspaceHeader(desktop: false),
          const SizedBox(height: 12),
          _overviewPanel(desktop: false),
          if (activeInspection != null) ...[
            const SizedBox(height: 10),
            _continueInspectionCard(),
          ],
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 54,
                  child: FilledButton.icon(
                    onPressed: () => _open(
                      const NewInspectionScreen(),
                      tutorialId: 'new_inspection',
                    ),
                    icon: const Icon(Icons.add_a_photo_outlined, size: 20),
                    label: const Text(
                      'Nova vistoria',
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: SizedBox(
                  height: 54,
                  child: OutlinedButton.icon(
                    onPressed: () => _open(
                      const CompaniesScreen(selectForExpressRound: true),
                      tutorialId: 'companies',
                    ),
                    icon: const Icon(Icons.route_rounded, size: 20),
                    label: const Text(
                      'Ronda expressa',
                      textAlign: TextAlign.center,
                    ),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          _sectionHeader(
            'Acesso rápido',
            'As funções mais usadas no dia a dia de campo',
          ),
          const SizedBox(height: 10),
          _moduleWrap(quickModules, minWidth: 145, maxColumns: 2),
          const SizedBox(height: 18),
          _routinePanel(),
          const SizedBox(height: 22),
          Container(
            key: _modulesKey,
            child: _sectionHeader(
              'Todos os módulos',
              'Gestão, controles, obrigações e indicadores',
            ),
          ),
          const SizedBox(height: 10),
          _moduleWrap(moreModules, minWidth: 145, maxColumns: 2),
          const SizedBox(height: 12),
          _companyResourcesCard(),
          const SizedBox(height: 18),
          const Center(
            child: Text(
              'SST Gestão',
              style: TextStyle(fontSize: 10.5, color: Colors.black45),
            ),
          ),
        ],
      ),
    );
  }
'''

workspace=r'''  Widget _workspaceHeader({required bool desktop}) {
    return Container(
      padding: EdgeInsets.all(desktop ? 20 : 15),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFF063B59), Color(0xFF0B6674)],
        ),
        borderRadius: BorderRadius.circular(22),
        boxShadow: const [
          BoxShadow(
            color: Color(0x18063B59),
            blurRadius: 20,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: desktop ? 58 : 50,
            height: desktop ? 58 : 50,
            padding: const EdgeInsets.all(5),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(15),
            ),
            child: Image.asset(
              AuditarBrand.iconAsset,
              fit: BoxFit.contain,
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'SST Gestão',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: desktop ? 24 : 20,
                    fontWeight: FontWeight.w900,
                    letterSpacing: -.2,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  desktop
                      ? 'Empresas, vistorias, EPI, pendências e resultados em um único painel.'
                      : 'Seu painel de Segurança do Trabalho.',
                  style: const TextStyle(
                    color: Colors.white70,
                    fontSize: 12,
                    height: 1.3,
                  ),
                ),
              ],
            ),
          ),
          if (desktop)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: .10),
                borderRadius: BorderRadius.circular(999),
                border: Border.all(color: Colors.white.withValues(alpha: .18)),
              ),
              child: const Text(
                'CENTRAL SST',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 10.5,
                  fontWeight: FontWeight.w900,
                  letterSpacing: .4,
                ),
              ),
            ),
        ],
      ),
    );
  }
'''

overview=r'''  Widget _overviewPanel({required bool desktop}) {
    final inspections = summary['inspections'] ?? 0;
    final pending = summary['pending'] ?? 0;
    final overdue = summary['ncOverdue'] ?? 0;

    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: EdgeInsets.all(desktop ? 20 : 14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Expanded(
                  child: Text(
                    'Visão geral',
                    style: TextStyle(
                      color: AuditarBrand.navy,
                      fontSize: 18,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ),
                Icon(
                  Icons.insights_rounded,
                  color: AuditarBrand.greenDark,
                  size: 21,
                ),
              ],
            ),
            const SizedBox(height: 12),
            ResponsiveWrap(
              minItemWidth: desktop ? 150 : 128,
              maxColumns: desktop ? 4 : 2,
              children: [
                _metric(
                  'Empresas',
                  companyCount,
                  Icons.business_outlined,
                  AuditarBrand.navy,
                ),
                _metric(
                  'Vistorias',
                  inspections,
                  Icons.fact_check_outlined,
                  AuditarBrand.info,
                ),
                _metric(
                  'Problemas abertos',
                  openNcs,
                  Icons.warning_amber_rounded,
                  AuditarBrand.danger,
                ),
                _metric(
                  'Ações pendentes',
                  pending,
                  Icons.assignment_outlined,
                  AuditarBrand.warning,
                ),
              ],
            ),
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              decoration: BoxDecoration(
                color: overdue > 0
                    ? const Color(0xFFFFF0F0)
                    : AuditarBrand.greenSoft,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Icon(
                    overdue > 0
                        ? Icons.event_busy_outlined
                        : Icons.verified_outlined,
                    size: 19,
                    color: overdue > 0
                        ? AuditarBrand.danger
                        : AuditarBrand.greenDark,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      overdue > 0
                          ? '$overdue correção(ões) vencida(s)'
                          : 'Nenhuma correção vencida',
                      style: TextStyle(
                        color: overdue > 0
                            ? AuditarBrand.danger
                            : AuditarBrand.greenDark,
                        fontSize: 12,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
'''

text=replace_between(text,'  Widget _mobileBody() {','\n\n  Widget _desktopBody() {',mobile)
text=replace_between(text,'  Widget _workspaceHeader({required bool desktop}) {','\n\n  Widget _overviewPanel({required bool desktop}) {',workspace)
text=replace_between(text,'  Widget _overviewPanel({required bool desktop}) {','\n\n  Widget _metric(',overview)

path.write_text(text,encoding='utf-8',newline='\n')
print('SST_HOME_LAYOUT_V2_OK: home móvel reorganizada, EPI em acesso rápido e visão geral compacta.')
