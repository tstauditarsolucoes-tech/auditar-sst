#!/usr/bin/env python3
from pathlib import Path
import re, shutil, sys

root=Path(sys.argv[1])
repo_root=Path(__file__).resolve().parents[1]
pubp=root/'pubspec.yaml'
companyp=root/'lib/screens/company_detail_screen.dart'
codep=root/'painel_web_google_apps_script/Code.gs'

src_service=repo_root/'build_sources/v3.29.76-cipa/cipa_management_service.dart'
src_screen=repo_root/'build_sources/v3.29.76-cipa/cipa_management_screen.dart'
dst_service=root/'lib/services/cipa_management_service.dart'
dst_screen=root/'lib/screens/cipa_management_screen.dart'
dst_service.parent.mkdir(parents=True,exist_ok=True)
dst_screen.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(src_service,dst_service)
shutil.copyfile(src_screen,dst_screen)

pub=pubp.read_text(encoding='utf-8')
pub,n=re.subn(r'^version:\s*[^\n]+','version: 3.29.76+218',pub,count=1,flags=re.M)
if n!=1:
    raise RuntimeError('Versão do app não localizada.')
pubp.write_text(pub,encoding='utf-8',newline='\n')

company=companyp.read_text(encoding='utf-8')
if "import 'cipa_management_screen.dart';" not in company:
    company=company.replace(
        "import 'cipa_screen.dart';\n",
        "import 'cipa_screen.dart';\nimport 'cipa_management_screen.dart';\n",
        1,
    )
company=company.replace(
    "title: 'CIPA',\n                subtitle: 'Eleições e votação',\n                onTap: () => _open(CipaScreen(companyId: widget.company.id)),",
    "title: 'CIPA',\n                subtitle: 'Gestão completa, reuniões, atas, ações e eleições',\n                onTap: () => _open(CipaManagementScreen(companyId: widget.company.id)),",
    1,
)
if 'CipaManagementScreen(companyId: widget.company.id)' not in company:
    raise RuntimeError('Atalho Empresa > CIPA não foi atualizado.')
companyp.write_text(company,encoding='utf-8',newline='\n')

code=codep.read_text(encoding='utf-8')
old_modes="['checklist_photo', 'safety_observation_photo', 'report_conclusion', 'report_review_chat', 'company_priorities', 'training_management', 'training_record_import', 'employee_pdf_import', 'medical_pdf_import', 'pgr_extract', 'pgr_question', 'checklist_builder']"
new_modes="['checklist_photo', 'safety_observation_photo', 'report_conclusion', 'report_review_chat', 'company_priorities', 'training_management', 'cipa_minutes_import', 'training_record_import', 'employee_pdf_import', 'medical_pdf_import', 'pgr_extract', 'pgr_question', 'checklist_builder']"
if new_modes not in code:
    if old_modes not in code:
        raise RuntimeError('Whitelist de modos da IA não localizada.')
    code=code.replace(old_modes,new_modes,1)

validation_marker="""  if (mode === 'training_record_import' || mode === 'employee_pdf_import' || mode === 'medical_pdf_import') {
    if (document.indexOf('data:application/pdf;base64,') !== 0) {
"""
if "if (mode === 'cipa_minutes_import')" not in code[code.find('const document'):code.find('const model')]:
    idx=code.find(validation_marker)
    if idx<0:
        raise RuntimeError('Validação de documento IA não localizada.')
    cipa_validation="""  if (mode === 'cipa_minutes_import') {
    if (!/^data:(application\\/pdf|image\\/[a-zA-Z0-9.+-]+);base64,/.test(document)) {
      return {ok: false, message: 'Selecione uma ata em PDF ou imagem para leitura pela IA.'};
    }
    if (document.length > 18000000) {
      return {ok: false, message: 'A ata ultrapassou o limite da análise.'};
    }
  }

"""
    code=code[:idx]+cipa_validation+code[idx:]

parts_marker="""  if (mode === 'training_record_import' || mode === 'employee_pdf_import' || mode === 'medical_pdf_import') {
    const match = document.match(/^data:(application\/pdf);base64,(.+)$/);
    if (match) {
      parts.push({inlineData: {mimeType: match[1], data: match[2]}});
    }
  }
"""
if "mode === 'cipa_minutes_import'" not in code[code.find('const parts'):code.find('const body')]:
    if parts_marker not in code:
        raise RuntimeError('Bloco inlineData de documentos não localizado.')
    cipa_parts="""  if (mode === 'cipa_minutes_import') {
    const match = document.match(/^data:(application\/pdf|image\/[a-zA-Z0-9.+-]+);base64,(.+)$/);
    if (match) {
      parts.push({inlineData: {mimeType: match[1], data: match[2]}});
    }
  }
"""
    code=code.replace(parts_marker,cipa_parts+parts_marker,1)

code=code.replace(
    "maxOutputTokens: mode === 'training_record_import' || mode === 'employee_pdf_import' || mode === 'medical_pdf_import'\n        ? 12000",
    "maxOutputTokens: mode === 'cipa_minutes_import'\n        ? 5200\n        : mode === 'training_record_import' || mode === 'employee_pdf_import' || mode === 'medical_pdf_import'\n        ? 12000",
    1,
)

prompt_anchor="  if (mode === 'training_record_import') {\n"
prompt_text=r"""  if (mode === 'cipa_minutes_import') {
    return [
      'Leia o documento como ata ou registro de reunião da CIPA.',
      'Empresa esperada: ' + String(payload.companyName || 'não informada') + '.',
      'Extraia somente informações presentes no documento. Não invente nomes, cargos, decisões, responsáveis ou prazos.',
      'Identifique a data da reunião e devolva em AAAA-MM-DD quando estiver legível.',
      'Em participants liste somente participantes/membros que aparecem como presentes, assinantes ou participantes da reunião.',
      'Em subjects liste os assuntos efetivamente discutidos.',
      'Em decisions liste deliberações ou decisões tomadas.',
      'Em responsibles liste responsáveis citados nas decisões ou ações.',
      'Em deadlines liste prazos explicitamente informados. Não crie datas por inferência.',
      'Se não for possível confirmar a empresa, mantenha company como texto vazio.',
      'Não inclua CPF, telefone, endereço, assinatura biométrica nem dados médicos.'
    ].join('\n');
  }
"""
u0=code.find('function aiUserPrompt_')
u1=code.find('function aiOutputSchema_')
if u0<0 or u1<0:
    raise RuntimeError('Funções IA não localizadas.')
if "if (mode === 'cipa_minutes_import')" not in code[u0:u1]:
    pos=code.find(prompt_anchor,u0,u1)
    if pos<0:
        raise RuntimeError('Ponto de inserção do prompt CIPA não localizado.')
    code=code[:pos]+prompt_text+code[pos:]

schema_anchor="  if (mode === 'training_record_import') {\n"
schema_text=r"""  if (mode === 'cipa_minutes_import') {
    return {
      type: 'object',
      properties: {
        company: {type: 'string'},
        title: {type: 'string'},
        date: {type: 'string'},
        participants: {type: 'array', items: {type: 'string'}},
        subjects: {type: 'array', items: {type: 'string'}},
        decisions: {type: 'array', items: {type: 'string'}},
        responsibles: {type: 'array', items: {type: 'string'}},
        deadlines: {type: 'array', items: {type: 'string'}}
      },
      required: ['company', 'title', 'date', 'participants', 'subjects', 'decisions', 'responsibles', 'deadlines']
    };
  }
"""
s0=code.find('function aiOutputSchema_')
if s0<0:
    raise RuntimeError('Schema IA não localizado.')
if "if (mode === 'cipa_minutes_import')" not in code[s0:]:
    pos=code.find(schema_anchor,s0)
    if pos<0:
        raise RuntimeError('Ponto de inserção do schema CIPA não localizado.')
    code=code[:pos]+schema_text+code[pos:]

codep.write_text(code,encoding='utf-8',newline='\n')

assert 'version: 3.29.76+218' in pub
assert 'CipaManagementScreen(companyId: widget.company.id)' in company
assert "cipa_minutes_import" in code
assert (root/'lib/services/cipa_management_service.dart').exists()
assert (root/'lib/screens/cipa_management_screen.dart').exists()
print('CIPA_MANAGEMENT_V32976_OK')
