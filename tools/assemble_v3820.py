#!/usr/bin/env python3
from __future__ import annotations

import shutil
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
        [sys.executable, str(repo / 'tools' / 'assemble_v3810.py')],
        cwd=repo,
        check=True,
    )
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    template_dir = repo / 'tools' / 'v3820'

    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.38.1+160', 'version: 3.38.2+161', 'versão 3.38.2')
    text = replace_once(text, '  archive: ^4.0.9\n', '  archive: ^4.0.9\n  xml: ^6.5.0\n', 'dependência XML para Excel')
    pub.write_text(text, encoding='utf-8')

    shutil.copyfile(
        template_dir / 'training_import_service.dart',
        app / 'lib' / 'services' / 'training_import_service.dart',
    )

    p = app / 'lib' / 'screens' / 'trainings_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "import '../services/ai_assistant_service.dart';\n",
        "import '../services/ai_assistant_service.dart';\nimport '../services/training_import_service.dart';\n",
        'import do serviço de treinamentos',
    )
    fragment = (template_dir / 'trainings_import_fragment.txt').read_text(encoding='utf-8')
    text = replace_once(
        text,
        '  Future<void> _openRequirements() async {\n',
        fragment + '  Future<void> _openRequirements() async {\n',
        'fluxo da importação inteligente',
    )
    old_actions = """                _trainingActionCard(\n                  icon: Icons.groups_rounded,\n                  title: 'Criar turma',\n                  subtitle: 'Selecionar quem precisa',\n                  color: AuditarBrand.navy,\n                  onTap: _addTrainingBatch,\n                ),\n                _trainingActionCard(\n                  icon: Icons.history_rounded,\n"""
    new_actions = """                _trainingActionCard(\n                  icon: Icons.groups_rounded,\n                  title: 'Criar turma',\n                  subtitle: 'Selecionar quem precisa',\n                  color: AuditarBrand.navy,\n                  onTap: _addTrainingBatch,\n                ),\n                _trainingActionCard(\n                  icon: Icons.upload_file_outlined,\n                  title: 'Importar com IA',\n                  subtitle: 'PDF, Excel ou CSV',\n                  color: AuditarBrand.navy,\n                  onTap: _importTrainingDocument,\n                ),\n                _trainingActionCard(\n                  icon: Icons.history_rounded,\n"""
    text = replace_once(text, old_actions, new_actions, 'atalho Importar com IA')
    p.write_text(text, encoding='utf-8')

    p = app / 'lib' / 'screens' / 'home_screen.dart'
    text = p.read_text(encoding='utf-8').replace('versão 3.38.1', 'versão 3.38.2')
    p.write_text(text, encoding='utf-8')

    p = app / 'painel_web_google_apps_script' / 'Code.gs'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "['checklist_photo', 'safety_observation_photo', 'report_conclusion', 'company_priorities', 'training_management', 'employee_pdf_import', 'medical_pdf_import', 'pgr_extract', 'pgr_question', 'checklist_builder', 'dds_suggestions', 'dds_generate', 'prevention_suggestions']",
        "['checklist_photo', 'safety_observation_photo', 'report_conclusion', 'company_priorities', 'training_management', 'training_document_import', 'employee_pdf_import', 'medical_pdf_import', 'pgr_extract', 'pgr_question', 'checklist_builder', 'dds_suggestions', 'dds_generate', 'prevention_suggestions']",
        'modo IA para importar treinamentos',
    )

    pdf_validation = """  if (mode === 'employee_pdf_import' || mode === 'medical_pdf_import') {\n    if (document.indexOf('data:application/pdf;base64,') !== 0) {\n      return {ok: false, message: mode === 'medical_pdf_import'\n        ? 'Selecione um PDF válido com o controle de periódicos.'\n        : 'Selecione um PDF válido com a lista de funcionários.'};\n    }\n    if (document.length > 18000000) {\n      return {ok: false, message: 'O PDF ultrapassou o limite da importação.'};\n    }\n  }\n"""
    training_validation = pdf_validation + """\n  if (mode === 'training_document_import') {\n    const extractedText = String(payload.extractedText || '').trim();\n    const hasPdf = document.indexOf('data:application/pdf;base64,') === 0;\n    if (!hasPdf && !extractedText) {\n      return {ok: false, message: 'Selecione um PDF, Excel ou CSV com o registro do treinamento.'};\n    }\n    if (hasPdf && document.length > 18000000) {\n      return {ok: false, message: 'O PDF ultrapassou o limite da importação.'};\n    }\n    if (extractedText.length > 220000) {\n      return {ok: false, message: 'A planilha ficou grande demais para uma única análise.'};\n    }\n  }\n"""
    text = replace_once(text, pdf_validation, training_validation, 'validação do documento de treinamento')

    text = replace_once(
        text,
        "  if (mode === 'employee_pdf_import' || mode === 'medical_pdf_import') {\n    const match = document.match(/^data:(application\\/pdf);base64,(.+)$/);\n",
        "  if (mode === 'employee_pdf_import' || mode === 'medical_pdf_import' || mode === 'training_document_import') {\n    const match = document.match(/^data:(application\\/pdf);base64,(.+)$/);\n",
        'anexo PDF do treinamento',
    )
    text = replace_once(
        text,
        "      maxOutputTokens: mode === 'employee_pdf_import' || mode === 'medical_pdf_import'\n        ? 12000\n",
        "      maxOutputTokens: mode === 'employee_pdf_import' || mode === 'medical_pdf_import' || mode === 'training_document_import'\n        ? 12000\n",
        'limite da resposta da importação',
    )

    prompt_marker = "  if (mode === 'employee_pdf_import') {\n"
    prompt = """  if (mode === 'training_document_import') {\n    return [\n      'Leia este registro de treinamento e extraia somente o que estiver claramente documentado.',\n      'A empresa selecionada no aplicativo é: ' + String(payload.companyName || '') + '.',\n      'Identifique NR/código, nome do treinamento, data, vencimento/reciclagem quando existir, carga horária, instrutor e participantes.',\n      'Converta datas válidas para AAAA-MM-DD. Quando um dado não estiver claro, retorne texto vazio em vez de inventar.',\n      'Para participantes, inclua somente pessoas que aparecem como treinandos, participantes ou presentes. Não inclua instrutor, responsável técnico, assinantes administrativos ou pessoas citadas fora da lista de participantes.',\n      'Transcreva o nome do participante como aparece no documento. Retorne CPF somente quando ele estiver claramente associado àquela pessoa; caso contrário use texto vazio.',\n      'Cargo/função deve ser retornado somente quando estiver indicado. Não deduza cargo pelo nome ou setor.',\n      'Não invente NR, validade legal, carga horária, instrutor ou participantes. A validade/reciclagem só deve ser preenchida se o próprio registro trouxer uma data de vencimento/validade.',\n      'Use confidence como Alta, Média ou Baixa conforme a clareza geral da leitura.',\n      'Em warnings, liste ambiguidades importantes, campos ausentes ou trechos que precisam de conferência humana.',\n      String(payload.extractedText || '').trim()\n        ? 'Conteúdo extraído da planilha:\\n' + String(payload.extractedText || '')\n        : 'O conteúdo está anexado em PDF.'\n    ].join('\\n');\n  }\n"""
    text = replace_once(text, prompt_marker, prompt + prompt_marker, 'prompt da importação de treinamento')

    schema_marker = "  if (mode === 'employee_pdf_import') {\n"
    schema = """  if (mode === 'training_document_import') {\n    return {\n      type: 'object',\n      properties: {\n        code: {type: 'string'},\n        title: {type: 'string'},\n        trainingDate: {type: 'string'},\n        expiryDate: {type: 'string'},\n        workload: {type: 'string'},\n        instructor: {type: 'string'},\n        confidence: {type: 'string'},\n        warnings: {type: 'array', items: {type: 'string'}},\n        participants: {\n          type: 'array',\n          items: {\n            type: 'object',\n            properties: {\n              name: {type: 'string'},\n              cpf: {type: 'string'},\n              role: {type: 'string'}\n            },\n            required: ['name', 'cpf', 'role']\n          }\n        }\n      },\n      required: ['code', 'title', 'trainingDate', 'expiryDate', 'workload', 'instructor', 'confidence', 'warnings', 'participants']\n    };\n  }\n"""
    schema_start = text.index('function aiOutputSchema_(mode)')
    schema_pos = text.find(schema_marker, schema_start)
    if schema_pos < 0:
        raise RuntimeError('Trecho esperado não encontrado: schema da importação de treinamento')
    text = text[:schema_pos] + schema + text[schema_pos:]
    p.write_text(text, encoding='utf-8')

    notes = app / 'MUDANCAS_V3_38_2_IMPORTACAO_TREINAMENTOS.txt'
    notes.write_text(
        '''AUDITAR SST v3.38.2\n\nIMPORTAÇÃO INTELIGENTE DE TREINAMENTOS\n\n- Nova opção "Importar com IA" dentro de Treinamentos.\n- Aceita PDF, Excel (.xlsx) e CSV.\n- IA identifica NR/código, treinamento, data, carga horária, instrutor e participantes.\n- Participantes são vinculados ao cadastro existente por CPF ou nome.\n- Registros duplicados da mesma pessoa/treinamento/data são bloqueados.\n- Antes de salvar, o Técnico confere e pode corrigir os dados e desmarcar participantes.\n- Pessoas não encontradas no cadastro aparecem como alerta e não são registradas automaticamente.\n- O arquivo original é guardado como evidência em cada registro importado.\n- Quando não há vencimento no documento, a matriz por cargo continua podendo fornecer a validade.\n\nIMPORTANTE\nO Code.gs desta versão adiciona o modo training_document_import. A implantação do Apps Script precisa ser atualizada para a IA de PDF/planilha funcionar.\n''',
        encoding='utf-8',
    )

    print(f'Fonte v3.38.2 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
