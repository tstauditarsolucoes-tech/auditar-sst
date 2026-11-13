#!/usr/bin/env python3
"""Área administrativa de contas dos membros: somente módulo CIPA staff.

Instalar depois dos patches de guia e rótulo da CIPA. Não altera
autenticação, sincronização, database, fotos, Drive ou Apps Script.
"""
from pathlib import Path
import hashlib
import shutil
import sys

if len(sys.argv)!=2:
    raise SystemExit("Uso: patch_cipa_member_admin_ui_v1.py <APP_DIR>")
app=Path(sys.argv[1])
repo=Path(__file__).resolve().parents[1]
screen=app/"lib/screens/cipa_management_screen.dart"
admin=app/"lib/screens/cipa_member_admin_screen.dart"
role_guide=app/"lib/services/cipa_member_role_meetings.dart"
mural_moderator=app/"lib/widgets/cipa_mural_moderation_panel.dart"
minute_review=app/"lib/widgets/cipa_minutes_review_panel.dart"
assert screen.is_file() and (app/"lib/services/cipa_member_identity.dart").is_file()
assert not admin.exists() and not role_guide.exists() and not mural_moderator.exists() and not minute_review.exists(),(
    "Tela ou biblioteca de cargos já existe: não sobrescrever")
allowed={screen,admin,role_guide,mural_moderator,minute_review}
protected={
    p:hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in [app/"lib",app/"painel_web_google_apps_script"]
    if folder.is_dir()
    for p in folder.rglob("*")
    if p.is_file() and p not in allowed
}
def once(s,old,new,name):
    n=s.count(old)
    if n!=1:raise RuntimeError(f"{name}: {n} ocorrências")
    return s.replace(old,new,1)
s=screen.read_text(encoding="utf-8")
if "import '../services/auth_service.dart';" not in s:
    s=once(s,"import '../services/cipa_management_service.dart';",
        "import '../services/cipa_management_service.dart';\n"
        "import '../services/auth_service.dart';","auth import")
s=once(s,"import 'cipa_screen.dart';",
    "import 'cipa_screen.dart';\n"
    "import 'cipa_member_admin_screen.dart';","admin import")
s=once(s,"          title: const Text('CIPA'),\n          actions: [",
    """          title: const Text('CIPA'),
          actions: [
            if (AuthService.isAdmin)
              IconButton(
                tooltip: 'Acessos individuais dos membros da CIPA',
                icon: const Icon(Icons.manage_accounts_outlined),
                onPressed: activeMandate == null ? null : () =>
                  Navigator.of(context).push(MaterialPageRoute(builder: (_) =>
                    CipaMemberAdminScreen(
                      companyId: widget.companyId,
                      mandateId: activeMandate!.id,
                      members: activeMembers.map((m) =>
                        CipaAdminMemberOption(
                          memberId: m.id,
                          workerId: (m.payload['workerId'] ?? '').toString(),
                          name: m.title,
                          cipaRole: (m.payload['cipaRole'] ?? '').toString(),
                        )).toList(),
                      actions: mandateActions.where((a) =>
                        a.status != 'Resolvida').map((a) =>
                        CipaAdminActionOption(id: a.id, title: a.title))
                        .toList(),
                      documents: mandateDocuments.map((d) =>
                        CipaAdminDocumentOption(
                          id: d.id,
                          title: d.title,
                          category: (d.payload['category'] ?? '').toString(),
                        )).toList(),
                    ))),
              ),""",
    "botão admin no app da CIPA")
screen.write_text(s,encoding="utf-8",newline="\n")
shutil.copyfile(repo/"feature_sources/cipa_member_admin_screen_v1.dart",admin)
shutil.copyfile(repo/"feature_sources/cipa_member_role_meetings_v1.dart",role_guide)
mural_moderator.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(repo/"feature_sources/cipa_mural_moderation_panel_v1.dart",
                mural_moderator)
shutil.copyfile(repo/"feature_sources/cipa_minutes_review_panel_v1.dart",
                minute_review)
for p,d in protected.items():
    assert hashlib.sha256(p.read_bytes()).hexdigest()==d,str(p)
assert s.count("CipaMemberAdminScreen(")==1
print("CIPA_MEMBER_ADMIN_UI_ONLY_ADDED_CORE_UNCHANGED")
