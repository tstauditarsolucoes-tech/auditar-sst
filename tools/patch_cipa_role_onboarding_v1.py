#!/usr/bin/env python3
"""Acrescenta orientação ao cadastro real CIPA, sem reconfigurar permissões.

A versão em campo NÃO é alterada automaticamente. Executar apenas em
cópia de homologação já preparada com a biblioteca de papéis.
"""
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("Uso: patch_cipa_role_onboarding_v1.py <APP_DIR>")
app=Path(sys.argv[1])
screen=app/"lib/screens/cipa_management_screen.dart"
roles=app/"lib/services/cipa_member_role_meetings.dart"
assert screen.is_file() and roles.is_file(), "Instale primeiro o módulo de papéis"
s=screen.read_text(encoding="utf-8")
assert "import '../services/cipa_member_role_meetings.dart';" not in s, (
    "Guia já aplicado; não sobrescrever")
def once(text,old,new,label):
    count=text.count(old)
    if count!=1:
        raise RuntimeError(label+": "+str(count)+" ocorrências")
    return text.replace(old,new,1)
s=once(s,"import '../services/cipa_management_service.dart';",
  "import '../services/cipa_management_service.dart';\n"
  "import '../services/cipa_member_role_meetings.dart';","import")
start=s.index("  Future<void> _editMember([SstRecord? current]) async {")
end=s.index("  Future<void> _editMeeting",start)
part=s[start:end]
part=once(part,
  "decoration: const InputDecoration(labelText: 'Função na CIPA'),",
  "isExpanded: true,\n"
  "                  decoration: const InputDecoration(\n"
  "                    labelText: 'Escolha a função na CIPA',\n"
  "                    helperText: 'Diferente do cargo na empresa'),",
  "descrição da função")
before="""                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: representation,"""
after="""                const SizedBox(height: 10),
                Text(CipaRoleGuide.summary(cipaRole),
                  style: const TextStyle(fontSize: 15)),
                const SizedBox(height: 4),
                Text(CipaRoleGuide.hint(cipaRole),
                  style: const TextStyle(fontSize: 12)),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: representation,"""
part=once(part,before,after,"mostrar atribuições")
before="""                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: status,"""
after="""                if (!CipaRoleGuide.consistent(cipaRole, representation))
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 10),
                    child: Text(
                      'A função e a representação não combinam. '
                      'Presidente: empregador. Vice-presidente: empregados. '
                      'Representante nomeado: designado. Confira os '
                      'documentos da CIPA antes de salvar.',
                      style: TextStyle(fontWeight: FontWeight.w700),
                    ),
                  ),
                const SizedBox(height: 10),
                DropdownButtonFormField<String>(
                  value: status,"""
part=once(part,before,after,"alerta de inconsistência")
before="""            FilledButton(
              onPressed: () => Navigator.pop(dialogContext, true),
              child: const Text('Salvar'),
            ),"""
after="""            FilledButton(
              onPressed: CipaRoleGuide.consistent(cipaRole, representation)
                ? () => Navigator.pop(dialogContext, true)
                : null,
              child: const Text('Salvar'),
            ),"""
part=once(part,before,after,"não salvar representação incompatível")
before="""    if (save != true) return;
    final worker = _workerById(workerId);"""
after="""    if (save != true) return;
    if (!CipaRoleGuide.consistent(cipaRole, representation)) {
      _message('Confira a função e a representação da CIPA.');
      return;
    }
    final worker = _workerById(workerId);"""
part=once(part,before,after,"proteção final")
s=s[:start]+part+s[end:]
screen.write_text(s,encoding="utf-8",newline="\n")
assert "cipaRole: cipaRole" in part, "Persistência original da função alterada"
print("CIPA_ROLE_ONBOARDING_GUIDED_NO_PERMISSIONS_CHANGED")
