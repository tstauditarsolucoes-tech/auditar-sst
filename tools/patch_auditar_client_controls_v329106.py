#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
if platform not in ('android','windows'):raise SystemExit('platform')
service=root/'lib/services/management_panel_service.dart'
screen=root/'lib/screens/management_panel_screen.dart'
pub=root/'pubspec.yaml'
def once(s,old,new,label):
    if s.count(old)!=1:raise RuntimeError(label+': '+str(s.count(old)))
    return s.replace(old,new,1)
s=service.read_text(encoding='utf-8')
s=once(s,'class ManagementPanelService {\n',r'''class ManagementPanelService {
  // Auditar remains an internal product. This controls only public web data.
  static const Map<String, bool> defaultClientPortalModules = {
    'overview': true,
    'actions': true,
    'inspections': true,
    'training': false,
    'safety': false,
    'improvements': false,
    'agenda': false,
    'extinguishers': false,
  };

  static Future<Map<String, bool>> loadClientPortalModules(
      String companyId) async {
    final values = Map<String, bool>.from(defaultClientPortalModules);
    final db = AppDatabase.instance;
    for (final key in defaultClientPortalModules.keys) {
      if (key == 'overview') continue;
      final value = (await db.getSetting(
        'client_portal_' + companyId + '_' + key,
        fallback: '',
      )).trim();
      if (value == '1') values[key] = true;
      if (value == '0') values[key] = false;
    }
    return values;
  }

  static Future<void> saveClientPortalModule({
    required String companyId,
    required String module,
    required bool enabled,
  }) async {
    if (module == 'overview' ||
        !defaultClientPortalModules.containsKey(module)) {
      throw ArgumentError.value(module, 'module', 'Módulo inválido.');
    }
    await AppDatabase.instance.setSetting(
      'client_portal_' + companyId + '_' + module,
      enabled ? '1' : '0',
    );
  }

''','client service methods')
s=once(s,"      'enabled': enabled,\n      'updatedAt': DateTime.now().toIso8601String(),",
"""      'enabled': enabled,
      'clientPortal': {
        'version': 2,
        'modules': await loadClientPortalModules(company.id),
      },
      'updatedAt': DateTime.now().toIso8601String(),""",'portal snapshot')
marker="""      await db.updateManagementPanelSync(
        companyId: company.id,
        status: 'Sincronizado',
      );"""
s=once(s,marker,"""      if (body == null || body['clientPortalVersion'] != 2) {
        throw Exception(
          'Atualize Code.gs e Index.html do Painel Web antes de publicar '
          'as permissões do cliente. A sincronização do aplicativo é independente.',
        );
      }

"""+marker,'server version confirmation')
service.write_text(s,encoding='utf-8',newline='\n')
s=screen.read_text(encoding='utf-8')
s=once(s,"  bool enabled = true;\n","""  bool enabled = true;
  Map<String, bool> clientPortalModules =
      Map<String, bool>.from(ManagementPanelService.defaultClientPortalModules);
""",'portal state')
s=once(s,"    final url =\n        await ManagementPanelService.panelUrlForCompany(widget.company.id);",
"""    final url =
        await ManagementPanelService.panelUrlForCompany(widget.company.id);
    final loadedClientPortal =
        await ManagementPanelService.loadClientPortalModules(widget.company.id);""",
'portal load')
s=once(s,"      panelUrl = url;\n      loading = false;",
"""      panelUrl = url;
      clientPortalModules = loadedClientPortal;
      loading = false;""",'loaded scopes')
anchor="  Future<void> _sync() async {"
addition=r'''  Future<void> _setClientPortalModule(String module, bool value) async {
    if (syncing || !enabled || panelUrl.isEmpty) return;
    final old = clientPortalModules[module] ?? false;
    setState(() {
      syncing = true;
      clientPortalModules = Map<String, bool>.from(clientPortalModules)
        ..[module] = value;
    });
    try {
      await ManagementPanelService.saveClientPortalModule(
        companyId: widget.company.id, module: module, enabled: value,
      );
      final result = await ManagementPanelService.syncCompany(widget.company);
      if (!result.success) {
        await ManagementPanelService.saveClientPortalModule(
          companyId: widget.company.id, module: module, enabled: old,
        );
        _showMessage('Permissão não publicada; seleção anterior restaurada. '
            + result.message);
      } else {
        _showMessage('Permissão publicada para esta empresa.');
      }
    } catch (error) {
      await ManagementPanelService.saveClientPortalModule(
        companyId: widget.company.id, module: module, enabled: old,
      );
      _showMessage('Falha ao publicar: ' + error.toString());
    } finally {
      if (mounted) {
        setState(() => syncing = false);
        await _load();
      }
    }
  }

  Widget _clientPortalCard() {
    const labels = <String, (String, String)>{
      'actions': ('Não conformidades e ações', 'Prazos e tratativas'),
      'inspections': ('Vistorias e relatórios', 'Histórico gerencial'),
      'training': ('Treinamentos', 'Inclui nomes e situação de treinamento'),
      'safety': ('Atos e condições inseguras', 'Registros e responsáveis'),
      'improvements': ('Melhorias', 'Sugestões e ações executadas'),
      'agenda': ('Agenda SST', 'Atividades programadas'),
      'extinguishers': ('Extintores', 'Inventário e pendências por setor'),
    };
    return Card(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 8),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 10),
              child: Text('Acesso do cliente • somente consulta',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
            ),
            const Padding(
              padding: EdgeInsets.fromLTRB(10, 5, 10, 10),
              child: Text('O Painel Gerencial completo continua exclusivo '
                  'da Auditar. Escolha os módulos liberados para esta '
                  'empresa. Outros dados não são enviados ao navegador.'),
            ),
            for (final entry in labels.entries)
              SwitchListTile.adaptive(
                dense: true,
                title: Text(entry.value.$1),
                subtitle: Text(entry.value.$2),
                value: clientPortalModules[entry.key] ?? false,
                onChanged: enabled && panelUrl.isNotEmpty && !syncing
                    ? (value) => _setClientPortalModule(entry.key, value)
                    : null,
              ),
            const Padding(
              padding: EdgeInsets.fromLTRB(10, 5, 10, 0),
              child: Text(
                'A visão geral permanece disponível. Dados médicos, '
                'documentos pessoais, CPF, e-mails e recursos administrativos '
                'não são publicados. Compartilhe o link apenas com '
                'responsáveis autorizados.',
                style: TextStyle(fontSize: 11.5, color: Colors.black54),
              ),
            ),
          ],
        ),
      ),
    );
  }

'''
s=once(s,anchor,addition+anchor,'client card methods')
s=once(s,"                  _linkCard(),\n                  const SizedBox(height: 16),",
       "                  _linkCard(),\n                  const SizedBox(height: 10),\n                  _clientPortalCard(),\n                  const SizedBox(height: 16),",'client card entry')
screen.write_text(s,encoding='utf-8',newline='\n')
before='3.29.105+247' if platform=='android' else '3.30.29+216'
after='3.29.106+248' if platform=='android' else '3.30.30+217'
p=pub.read_text(encoding='utf-8')
pub.write_text(once(p,'version: '+before,'version: '+after,'version'),encoding='utf-8',newline='\n')
print('AUDITAR_INTERNAL_CLIENT_PORTAL_OK',platform,after)
