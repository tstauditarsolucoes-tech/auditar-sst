#!/usr/bin/env python3
"""Integra cadastro do perfil Cliente na tela Usuários e acessos existente."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def patch(s,a,b,label):
    if b in s:return s
    if a not in s:raise RuntimeError('Âncora ausente: '+label)
    return s.replace(a,b,1)
p=root/'lib/services/auth_service.dart';s=p.read_text(encoding='utf-8')
for a,b,label in [
("  final List<String> companyIds;\n",
 "  final List<String> companyIds;\n  final Map<String, bool> clientPermissions;\n",'model'),
("    required this.companyIds,\n",
 "    required this.companyIds,\n    required this.clientPermissions,\n",'constructor'),
("      companyIds: rawCompanies is List\n",
 """      clientPermissions: map['clientPermissions'] is Map
          ? (map['clientPermissions'] as Map).map<String, bool>(
              (key, value) => MapEntry('$key', value == true))
          : const <String, bool>{},
      companyIds: rawCompanies is List
""",'parse'),
("        'companyIds': companyIds,\n",
 "        'companyIds': companyIds,\n        'clientPermissions': clientPermissions,\n",'serialize'),
("    final isAdmin = rawUser is Map &&\n",
 """    if (rawUser is Map && rawUser['role'].toString().toLowerCase() == 'cliente') {
      throw StateError('Conta de cliente: entre pelo Painel Gerencial no navegador.');
    }
    final isAdmin = rawUser is Map &&
""",'restrict app login'),
("    required List<String> companyIds,\n    String password = '',",
 "    required List<String> companyIds,\n    Map<String, bool> clientPermissions = const {},\n    String password = '',",'param'),
("        'companyIds': companyIds,\n        if (password.isNotEmpty)",
 "        'companyIds': companyIds,\n        'clientPermissions': clientPermissions,\n        if (password.isNotEmpty)",'wire')
]:s=patch(s,a,b,label)
p.write_text(s,encoding='utf-8',newline='\n')
p=root/'lib/screens/users_screen.dart';s=p.read_text(encoding='utf-8')
for a,b,label in [
("user.isAdmin ? Icons.admin_panel_settings_rounded : Icons.engineering_rounded",
 "user.isAdmin ? Icons.admin_panel_settings_rounded : user.role == 'cliente' ? Icons.business_rounded : Icons.engineering_rounded",'icon'),
("user.isAdmin ? 'Administrador' : 'Técnico'",
 "user.isAdmin ? 'Administrador' : user.role == 'cliente' ? 'Cliente • Painel' : 'Técnico'",'label'),
("  late Set<String> selectedCompanies;\n",
 "  late Set<String> selectedCompanies;\n  late Map<String, bool> clientPermissions;\n",'permissions state'),
("    role = user?.isAdmin == true ? 'admin' : 'tecnico';",
 "    role = user?.role ?? 'tecnico';",'editor role'),
("    selectedCompanies = {...?user?.companyIds};",
 """    selectedCompanies = {...?user?.companyIds};
    clientPermissions = {
      'indicadores': true, 'naoConformidades': true,
      'acoesCorretivas': true, 'relatorios': true, 'enviarEvidencia': false,
      ...?user?.clientPermissions
    };""",'permissions init'),
("        allCompanies: role == 'admin' ? true : allCompanies,",
 "        allCompanies: role == 'admin' ? true : role == 'cliente' ? false : allCompanies,",'all companies'),
("        companyIds: role == 'admin' || allCompanies ? const [] : selectedCompanies.toList(),",
 """        companyIds: role == 'admin' || (role == 'tecnico' && allCompanies)
            ? const [] : selectedCompanies.toList(),
        clientPermissions: clientPermissions,""",'save permissions'),
("                  DropdownMenuItem(value: 'tecnico', child: Text('Técnico SST')),\n                  DropdownMenuItem(value: 'admin', child: Text('Administrador')),",
 """                  DropdownMenuItem(value: 'tecnico', child: Text('Técnico SST')),
                  DropdownMenuItem(value: 'cliente', child: Text('Cliente • Painel Gerencial')),
                  DropdownMenuItem(value: 'admin', child: Text('Administrador')),""",'roles'),
("                  if (role == 'admin') allCompanies = true;",
 """                  if (role == 'admin') allCompanies = true;
                  if (role == 'cliente') {
                    allCompanies = false;
                    selectedCompanies.clear();
                  }""",'role constraints'),
("              if (role != 'admin') ...[\n                SwitchListTile(",
 "              if (role != 'admin') ...[\n                if (role == 'tecnico') SwitchListTile(",'tech switch'),
("                if (!allCompanies) ...[",
 "                if (role == 'cliente' || !allCompanies) ...[",'company chooser'),
("                  const Text('Empresas liberadas', style: TextStyle(fontWeight: FontWeight.w800)),",
 """                  Text(role == 'cliente' ? 'Empresa do cliente (selecione uma)' : 'Empresas liberadas',
                    style: const TextStyle(fontWeight: FontWeight.w800)),""",'company label'),
("                                  if (checked == true) {\n                                    selectedCompanies.add(company.id);",
 """                                  if (checked == true) {
                                    if (role == 'cliente') selectedCompanies.clear();
                                    selectedCompanies.add(company.id);""",'single company')
]:s=patch(s,a,b,label)
needle="    setState(() {\n      saving = true;\n      error = '';\n    });"
s=patch(s,needle,"""    if (role == 'cliente' && selectedCompanies.length != 1) {
      setState(() => error = 'Selecione exatamente uma empresa para o cliente.');
      return;
    }
"""+needle,'client validation')
needle="              if (error.isNotEmpty) ...["
widgets="""              if (role == 'cliente') ...[
                const SizedBox(height: 12),
                const Text('Permissões do Painel Gerencial',
                  style: TextStyle(fontWeight: FontWeight.w800)),
                ...const [
                  ('indicadores', 'Consultar indicadores'),
                  ('naoConformidades', 'Consultar não conformidades'),
                  ('acoesCorretivas', 'Consultar ações corretivas'),
                  ('relatorios', 'Consultar relatórios e vistorias'),
                  ('enviarEvidencia', 'Enviar evidências de correção')
                ].map((item) => CheckboxListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  value: clientPermissions[item.$1] == true,
                  title: Text(item.$2),
                  onChanged: (value) => setState(
                    () => clientPermissions[item.$1] = value == true),
                )),
              ],
"""
s=patch(s,needle,widgets+needle,'permission checklist')
p.write_text(s,encoding='utf-8',newline='\n')
print('CLIENT_ACCOUNT_UI_OK')
