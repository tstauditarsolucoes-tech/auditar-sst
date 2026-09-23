#!/usr/bin/env python3
"""Make training signatures usable and create company-scoped client entry."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
def edit(rel,fn):
    p=root/rel; s=p.read_text(encoding='utf-8')
    p.write_text(fn(s),encoding='utf-8',newline='\n')
def rep(s,a,b,label):
    count=s.count(a)
    if count!=1:raise RuntimeError(f'{label}: {count} anchors')
    return s.replace(a,b,1)

def training(s):
    s=rep(s,"import 'package:flutter/material.dart';",
       "import 'package:flutter/material.dart';\nimport 'package:flutter/services.dart';",'orientation import')
    key="  Future<void> _save() async {"
    loc=s.index(key,s.index("class _TrainingRecordSignatureScreenState"))
    full="""  Future<void> _openFullScreen() async {
    if (saving) return;
    final participantName = widget.participant['name']?.toString().trim() ?? '';
    final landscape = Platform.isAndroid;
    if (landscape) {
      await SystemChrome.setPreferredOrientations(const [
        DeviceOrientation.landscapeLeft, DeviceOrientation.landscapeRight,
      ]);
    }
    var complete = false;
    try {
      if (!mounted) return;
      complete = await Navigator.of(context).push<bool>(
        MaterialPageRoute(
          fullscreenDialog: true,
          builder: (pageContext) => Scaffold(
            appBar: AppBar(
              title: Text(
                'ASSINANDO AGORA • $participantName',
                maxLines: 1, overflow: TextOverflow.ellipsis,
              ),
              actions: [
                IconButton(
                  tooltip: 'Limpar assinatura',
                  icon: const Icon(Icons.delete_outline),
                  onPressed: controller.clear,
                ),
              ],
            ),
            body: SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(10),
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border.all(color: const Color(0xFFBFC6D2)),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  clipBehavior: Clip.antiAlias,
                  child: Signature(
                    controller: controller,
                    backgroundColor: Colors.white,
                  ),
                ),
              ),
            ),
            bottomNavigationBar: SafeArea(
              minimum: const EdgeInsets.fromLTRB(12, 5, 12, 10),
              child: FilledButton.icon(
                icon: const Icon(Icons.check),
                label: const Text('Concluir assinatura'),
                onPressed: () {
                  if (controller.isEmpty) {
                    ScaffoldMessenger.of(pageContext).showSnackBar(
                      const SnackBar(content: Text('Assine antes de concluir.')));
                    return;
                  }
                  Navigator.pop(pageContext, true);
                },
              ),
            ),
          ),
        ),
      ) ?? false;
    } finally {
      if (landscape) {
        await SystemChrome.setPreferredOrientations(const <DeviceOrientation>[]);
      }
    }
    if (complete && mounted) await _save();
  }

"""
    s=s[:loc]+full+s[loc:]
    start=s.index("            const SizedBox(height: 10),\n            Row(\n              children: [\n                Expanded(\n                  child: OutlinedButton.icon(",
                  s.index("class _TrainingRecordSignatureScreenState"))
    end=s.index("            ],\n          ),\n        ),\n      ),\n    );",start)
    part=s[start:end]
    if 'Confirmar assinatura' not in part: raise RuntimeError('training action block changed')
    s=s[:start]+s[end:]
    before="""      appBar: AppBar(title: const Text('Assinatura do treinamento')),
      body: SafeArea("""
    after="""      appBar: AppBar(title: const Text('Assinatura do treinamento')),
      bottomNavigationBar: SafeArea(
        minimum: const EdgeInsets.fromLTRB(12, 6, 12, 10),
        child: Row(children: [
          IconButton(
            tooltip: 'Limpar assinatura',
            onPressed: saving ? null : controller.clear,
            icon: const Icon(Icons.delete_outline),
          ),
          IconButton(
            tooltip: 'Assinar em tela cheia',
            onPressed: saving ? null : _openFullScreen,
            icon: const Icon(Icons.fullscreen),
          ),
          const SizedBox(width: 6),
          Expanded(child: FilledButton.icon(
            onPressed: saving ? null : _save,
            icon: const Icon(Icons.check_circle_outline),
            label: Text(saving ? 'Salvando...' : 'Confirmar assinatura',
              maxLines: 1, overflow: TextOverflow.ellipsis),
          )),
        ]),
      ),
      body: SafeArea("""
    s=rep(s,before,after,'training bottom actions')
    s=rep(s,"""                        fontSize: 25,
                        height: 1.08,""","""                        fontSize: 20,
                        height: 1.1,""",'long names fit')
    s=rep(s,"""                padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),""",
      """                padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),""",'header space')
    return s
edit('lib/screens/training_records_screen.dart',training)

def users(s):
    s=rep(s,"""class UsersScreen extends StatefulWidget {
  const UsersScreen({super.key});""","""class UsersScreen extends StatefulWidget {
  final String? initialCompanyId;

  const UsersScreen({super.key, this.initialCompanyId});""",'initial company entry')
    s=rep(s,"""  List<Company> companies = const [];

  @override""","""  List<Company> companies = const [];
  bool _openedCompanyClientEditor = false;

  @override""",'initial editor flag')
    key="""        loading = false;
      });
    } catch (e) {"""
    value="""        loading = false;
      });
      if (widget.initialCompanyId != null && !_openedCompanyClientEditor) {
        _openedCompanyClientEditor = true;
        WidgetsBinding.instance.addPostFrameCallback((_) {
          if (mounted) _edit();
        });
      }
    } catch (e) {"""
    s=rep(s,key,value,'open editor after load')
    s=rep(s,"""        companies: companies,
      ),""","""        companies: companies,
        initialCompanyId: widget.initialCompanyId,
      ),""",'editor receives company')
    s=rep(s,"""  final List<Company> companies;

  const _UserEditorDialog({required this.user, required this.companies});""",
       """  final List<Company> companies;
  final String? initialCompanyId;

  const _UserEditorDialog({
    required this.user, required this.companies, this.initialCompanyId,
  });""",'editor field')
    s=rep(s,"    role = user?.role ?? 'tecnico';",
       "    role = user?.role ?? (widget.initialCompanyId == null ? 'tecnico' : 'cliente');",
       'client default')
    s=rep(s,"    selectedCompanies = {...?user?.companyIds};",
       "    selectedCompanies = user == null && widget.initialCompanyId != null\n        ? {widget.initialCompanyId!} : {...?user?.companyIds};",
       'one chosen company')
    return s
edit('lib/screens/users_screen.dart',users)

def panel(s):
    s=rep(s,"import 'training_records_screen.dart';",
       "import 'training_records_screen.dart';\nimport 'users_screen.dart';\nimport '../services/auth_service.dart';",
       'user navigation imports')
    marker="            if (configured) ...[\n              Row("
    s=rep(s,marker,"""            if (AuthService.isAdmin) ...[
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.person_add_alt_1_outlined),
                  label: const Text('Cadastrar acesso do cliente'),
                  onPressed: () => Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => UsersScreen(
                      initialCompanyId: widget.company.id,
                    )),
                  ),
                ),
              ),
              const SizedBox(height: 10),
            ],
            if (configured) ...[
              Row(""",'company user button')
    return s
edit('lib/screens/management_panel_screen.dart',panel)
pub=root/'pubspec.yaml'
version=pub.read_text(encoding='utf-8')
old,new={'android':('3.29.109+251','3.29.110+252'),
         'windows':('3.30.33+220','3.30.34+221')}[platform]
if version.count('version: '+old)!=1:
    raise RuntimeError('Unexpected version before field UX '+old)
pub.write_text(version.replace('version: '+old,'version: '+new,1),
               encoding='utf-8',newline='\\n')
print('TRAINING_SIGNING_COMPANY_CLIENT_ENTRY_OK',platform,new)
