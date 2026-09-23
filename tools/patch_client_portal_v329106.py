#!/usr/bin/env python3
"""Pós-patch v3.29.105/v3.30.29. Não toca sync, IA nem banco local."""
import sys,re
from pathlib import Path
root=Path(sys.argv[1]); platform=sys.argv[2] if len(sys.argv)>2 else 'android'
assert platform in ('android','windows')
source=Path(__file__).resolve().parent.parent/'build_sources/v3.29.106-client-portal'
backend=root/'painel_web_google_apps_script'
def patch(s,old,new,label):
    if new in s:return s
    if old not in s:raise RuntimeError('Âncora ausente: '+label)
    return s.replace(old,new,1)
def edit(path,fn):
    p=root/path;s=p.read_text(encoding='utf-8');p.write_text(fn(s),encoding='utf-8',newline='\n')
for filename in ('ClientPortal.gs','ClientPortal.html'):
    (backend/filename).write_bytes((source/filename).read_bytes())
def code_patch(s):
    s=patch(s,"      request.__authUser = authorization.user;\n      request.syncKey = expectedKey;",
    """      request.__authUser = authorization.user;
      if (authorization.user.role === 'cliente') {
        return jsonResponse_({ok:false,code:'ACCESS_DENIED',
          message:'Cliente acessa somente o Painel Gerencial.'});
      }
      request.syncKey = expectedKey;""",'bloquear rotas operacionais')
    s=patch(s,"  const params = (e && e.parameter) || {};\n",
    """  const params = (e && e.parameter) || {};
  if (String(params.cliente || '') === '1') {
    return HtmlService.createHtmlOutputFromFile('ClientPortal')
      .setTitle('Área do Cliente • Auditar SST');
  }
""",'web login')
    return s
edit('painel_web_google_apps_script/Code.gs',code_patch)
def multi_patch(s):
    ops=[
    ("'active', 'all_companies', 'company_ids_json', 'created_at', 'updated_at', 'last_login_at'",
     "'active', 'all_companies', 'company_ids_json', 'created_at', 'updated_at', 'last_login_at', 'client_permissions_json'",'coluna opcional'),
    ("getRange(2, 1, lastRow - 1, 12).getValues().map((row, index)",
     "getRange(2, 1, lastRow - 1, 13).getValues().map((row, index)",'ler permissões'),
    ("role: String(row[5] || 'tecnico').toLowerCase() === 'admin' ? 'admin' : 'tecnico',",
     """role: ['admin','tecnico','cliente'].indexOf(String(row[5] || '').toLowerCase()) >= 0
      ? String(row[5]).toLowerCase() : 'tecnico',""",'perfil'),
    ("    companyIds: authCompanyIds_(row[8]),\n    createdAt:",
     """    companyIds: authCompanyIds_(row[8]),
    clientPermissions: (function() {
      try { return clientPortalPermissions_(JSON.parse(String(row[12] || '{}'))); }
      catch (_) { return clientPortalPermissions_({}); }
    })(),
    createdAt:""",'permissões usuário'),
    ("  if (!id) return true;\n  return user.role === 'admin' || user.allCompanies || user.companyIds.indexOf(id) >= 0;",
     """  if (!id) return user.role !== 'cliente';
  if (user.role === 'cliente') {
    return !user.allCompanies && user.companyIds.length === 1 && user.companyIds[0] === id;
  }
  return user.role === 'admin' || user.allCompanies || user.companyIds.indexOf(id) >= 0;""",'deny default'),
    ("    companyIds: user.role === 'admin' || user.allCompanies ? [] : user.companyIds\n",
     """    companyIds: user.role === 'admin' || user.allCompanies ? [] : user.companyIds,
    clientPermissions: clientPortalPermissions_(user.clientPermissions)
""",'public user'),
    ("  const user = users.find(item => item.email === email);",
     """  const user = users.find(item => item.email === email);
  if (user && user.role === 'cliente') {
    return {ok:false,code:'CLIENT_PORTAL_ONLY',
      message:'Esta conta acessa somente o Painel Gerencial no navegador.'};
  }""",'login app'),
    ("  const role = String(input.role || '').toLowerCase() === 'admin' ? 'admin' : 'tecnico';",
     """  const requestedRole = String(input.role || '').toLowerCase();
  const role = ['admin','tecnico','cliente'].indexOf(requestedRole) >= 0
    ? requestedRole : 'tecnico';""",'save role'),
    ("  const allCompanies = role === 'admin' ? true : input.allCompanies === true;",
     "  const allCompanies = role === 'admin' ? true : (role === 'cliente' ? false : input.allCompanies === true);",'scope'),
    ("  const password = String(input.password || '');",
     """  const clientPermissions = role === 'cliente'
    ? clientPortalPermissions_(input.clientPermissions || clientPortalDefaultPermissions_())
    : clientPortalPermissions_({});
  const password = String(input.password || '');
  if (role === 'cliente' && companyIds.length !== 1) {
    return {ok:false, message:'Selecione exatamente uma empresa para o cliente.'};
  }""",'one company'),
    ("      companyIds: companyIds,\n      createdAt: now,",
     "      companyIds: companyIds,\n      clientPermissions: clientPermissions,\n      createdAt: now,",'new perms'),
    ("      now, now, ''\n    ]);",
     "      now, now, '', JSON.stringify(user.clientPermissions)\n    ]);",'insert 13'),
    ("    user.companyIds = companyIds;\n    user.updatedAt = now;",
     "    user.companyIds = companyIds;\n    user.clientPermissions = clientPermissions;\n    user.updatedAt = now;",'edit perms'),
    ("    sheet.getRange(user.rowNumber, 1, 1, 12).setValues([[",
     "    sheet.getRange(user.rowNumber, 1, 1, 13).setValues([[",'update 13'),
    ("      user.createdAt, now, user.lastLoginAt\n    ]]);",
     "      user.createdAt, now, user.lastLoginAt, JSON.stringify(user.clientPermissions)\n    ]]);",'update perms')
    ]
    for old,new,label in ops:s=patch(s,old,new,label)
    return s
edit('painel_web_google_apps_script/MultiUser.gs',multi_patch)
version='3.29.106+248' if platform=='android' else '3.30.30+217'
edit('pubspec.yaml',lambda s:re.sub(r'(?m)^version:\s*[^\n]+','version: '+version,s,count=1))
print('CLIENT_PORTAL_BACKEND_PATCH_OK',platform,version)
