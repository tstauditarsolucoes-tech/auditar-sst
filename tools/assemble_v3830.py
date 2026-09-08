#!/usr/bin/env python3
from __future__ import annotations

import base64
import io
import subprocess
import sys
import tarfile
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise RuntimeError(f'Trecho esperado não encontrado: {label}')
    return text.replace(old, new, 1)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, str(repo / 'tools' / 'assemble_v3820.py')],
        cwd=repo,
        check=True,
    )
    app = repo / 'app' / 'Auditar_SST_v1_5_dashboard'
    payload_path = repo / 'tools' / 'v3830' / 'payload.b64'

    pub = app / 'pubspec.yaml'
    text = pub.read_text(encoding='utf-8')
    text = replace_once(text, 'version: 3.38.2+161', 'version: 3.38.3+162', 'versão 3.38.3')
    pub.write_text(text, encoding='utf-8')

    payload = base64.b64decode(payload_path.read_text(encoding='utf-8').strip())
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:gz') as archive:
        screen = archive.extractfile('dds_signature_screen.dart')
        service = archive.extractfile('dds_pdf_service.dart')
        if screen is None or service is None:
            raise RuntimeError('Payload DDS v3.38.3 incompleto')
        (app / 'lib' / 'screens' / 'dds_signature_screen.dart').write_bytes(screen.read())
        (app / 'lib' / 'services' / 'dds_pdf_service.dart').write_bytes(service.read())

    p = app / 'lib' / 'screens' / 'sst_records_screen.dart'
    text = p.read_text(encoding='utf-8')
    text = replace_once(
        text,
        "import 'dds_ai_screen.dart';\n",
        "import 'dds_ai_screen.dart';\nimport 'dds_signature_screen.dart';\n",
        'import do DDS por assinatura',
    )

    marker = "  Future<void> _openDdsAi() async {\n"
    method = """  Future<void> _openDdsSignature([SstRecord? record]) async {\n    final changed = await Navigator.of(context).push<bool>(\n      MaterialPageRoute(\n        builder: (_) => DdsSignatureScreen(\n          companyId: widget.companyId,\n          record: record,\n        ),\n      ),\n    );\n    if (mounted) await _load();\n  }\n\n"""
    text = replace_once(text, marker, method + marker, 'abrir DDS por assinatura')

    old_dds_cards = """                  if (widget.type == 'DDS') ...[\n                    _ddsAiCard(),\n                    const SizedBox(height: 14),\n                  ],\n"""
    new_dds_cards = """                  if (widget.type == 'DDS') ...[\n                    _ddsSignatureCard(),\n                    const SizedBox(height: 10),\n                    _ddsAiCard(),\n                    const SizedBox(height: 14),\n                  ],\n"""
    text = replace_once(text, old_dds_cards, new_dds_cards, 'card DDS por assinatura')
    text = text.replace(
        "? 'Use o DDS Inteligente ou toque no botão + para criar um tema manualmente.'",
        "? 'Registre o DDS com assinatura pelo celular, use a IA para sugerir temas ou toque no botão + para um registro manual.'",
        1,
    )

    ai_marker = "  Widget _ddsAiCard() => Card(\n"
    signature_card = """  Widget _ddsSignatureCard() => Card(\n        margin: EdgeInsets.zero,\n        child: InkWell(\n          borderRadius: BorderRadius.circular(16),\n          onTap: () => _openDdsSignature(),\n          child: Padding(\n            padding: const EdgeInsets.all(14),\n            child: Row(\n              crossAxisAlignment: CrossAxisAlignment.start,\n              children: [\n                Container(\n                  width: 46,\n                  height: 46,\n                  decoration: BoxDecoration(\n                    color: const Color(0xFFF0F3F8),\n                    borderRadius: BorderRadius.circular(13),\n                  ),\n                  child: const Icon(Icons.draw_outlined, color: AuditarBrand.navy),\n                ),\n                const SizedBox(width: 12),\n                const Expanded(\n                  child: Column(\n                    crossAxisAlignment: CrossAxisAlignment.start,\n                    children: [\n                      Text(\n                        'DDS por assinatura',\n                        style: TextStyle(\n                          color: AuditarBrand.navy,\n                          fontSize: 16,\n                          fontWeight: FontWeight.w900,\n                        ),\n                      ),\n                      SizedBox(height: 4),\n                      Text(\n                        'Selecione os trabalhadores e passe o celular para cada participante assinar na tela.',\n                        style: TextStyle(height: 1.25),\n                      ),\n                    ],\n                  ),\n                ),\n                const SizedBox(width: 8),\n                const Icon(Icons.chevron_right_rounded),\n              ],\n            ),\n          ),\n        ),\n      );\n\n"""
    text = replace_once(text, ai_marker, signature_card + ai_marker, 'widget DDS por assinatura')

    old_card_start = """    return Card(\n      child: InkWell(\n        borderRadius: BorderRadius.circular(16),\n        onTap: () => _edit(record),\n"""
    new_card_start = """    final signedDds = widget.type == 'DDS' &&\n        '${record.payload['signatureMode'] ?? ''}' == 'mobile';\n    final signedCount = int.tryParse('${record.payload['signedCount'] ?? 0}') ?? 0;\n    final participantCount =\n        int.tryParse('${record.payload['participantCount'] ?? 0}') ?? 0;\n\n    return Card(\n      child: InkWell(\n        borderRadius: BorderRadius.circular(16),\n        onTap: () => signedDds ? _openDdsSignature(record) : _edit(record),\n"""
    text = replace_once(text, old_card_start, new_card_start, 'abrir DDS assinado no fluxo próprio')

    old_meta_priority = """                        if (record.priority.isNotEmpty)\n                          _meta(Icons.flag_outlined, record.priority),\n"""
    new_meta_priority = """                        if (signedDds)\n                          _meta(\n                            Icons.draw_outlined,\n                            '$signedCount/$participantCount assinaturas',\n                          ),\n                        if (record.priority.isNotEmpty)\n                          _meta(Icons.flag_outlined, record.priority),\n"""
    text = replace_once(text, old_meta_priority, new_meta_priority, 'contador de assinaturas no histórico')

    old_menu = """              PopupMenuButton<String>(\n                onSelected: (value) {\n                  if (value == 'edit') _edit(record);\n                  if (value == 'delete') _delete(record);\n                },\n                itemBuilder:\n                    (_) => const [\n                      PopupMenuItem(value: 'edit', child: Text('Editar')),\n                      PopupMenuItem(value: 'delete', child: Text('Excluir')),\n                    ],\n              ),\n"""
    new_menu = """              PopupMenuButton<String>(\n                onSelected: (value) {\n                  if (value == 'sign') _openDdsSignature(record);\n                  if (value == 'edit') _edit(record);\n                  if (value == 'delete') _delete(record);\n                },\n                itemBuilder: (_) => [\n                  if (widget.type == 'DDS')\n                    PopupMenuItem(\n                      value: 'sign',\n                      child: Text(signedDds ? 'Abrir registro assinado' : 'Coletar assinaturas'),\n                    ),\n                  if (!signedDds)\n                    const PopupMenuItem(value: 'edit', child: Text('Editar')),\n                  const PopupMenuItem(value: 'delete', child: Text('Excluir')),\n                ],\n              ),\n"""
    text = replace_once(text, old_menu, new_menu, 'menu do DDS com assinatura')
    p.write_text(text, encoding='utf-8')

    p = app / 'lib' / 'database.dart'
    text = p.read_text(encoding='utf-8')
    old_delete = """  Future<void> deleteSstRecord(String id) async {\n    final db = await database;\n    await db.delete('sst_records', where: 'id = ?', whereArgs: [id]);\n  }\n"""
    new_delete = """  Future<void> deleteSstRecord(String id) async {\n    final db = await database;\n    final assets = await db.query(\n      'media_assets',\n      columns: ['local_path'],\n      where: 'entity_type = ? AND entity_id LIKE ?',\n      whereArgs: ['dds_signature', '$id::%'],\n    );\n    for (final asset in assets) {\n      final localPath = '${asset['local_path'] ?? ''}'.trim();\n      if (localPath.isEmpty) continue;\n      try {\n        final file = File(localPath);\n        if (await file.exists()) await file.delete();\n      } catch (_) {}\n    }\n    await db.transaction((txn) async {\n      await txn.delete(\n        'media_assets',\n        where: 'entity_type = ? AND entity_id LIKE ?',\n        whereArgs: ['dds_signature', '$id::%'],\n      );\n      await txn.delete('sst_records', where: 'id = ?', whereArgs: [id]);\n    });\n  }\n"""
    text = replace_once(text, old_delete, new_delete, 'limpeza das assinaturas ao excluir DDS')
    p.write_text(text, encoding='utf-8')

    p = app / 'lib' / 'screens' / 'home_screen.dart'
    text = p.read_text(encoding='utf-8').replace('versão 3.38.2', 'versão 3.38.3')
    p.write_text(text, encoding='utf-8')

    notes = app / 'MUDANCAS_V3_38_3_DDS_ASSINATURA_MOBILE.txt'
    notes.write_text(
        '''AUDITAR SST v3.38.3\n\nDDS POR ASSINATURA NO CELULAR\n\n- Novo cartão "DDS por assinatura" dentro da área de DDS.\n- Seleção dos funcionários já cadastrados na empresa.\n- Inclusão manual para visitante, terceirizado ou pessoa ainda não cadastrada.\n- Cada participante assina diretamente na tela do celular, com opção de refazer.\n- Assinatura é vinculada ao nome, função e horário da coleta.\n- O DDS é salvo automaticamente como "Em coleta" enquanto houver assinatura pendente e vira "Realizado" quando todos assinarem.\n- O histórico mostra quantas assinaturas foram coletadas.\n- Registros antigos de DDS também podem receber assinaturas pelo menu "Coletar assinaturas".\n- Geração e compartilhamento de comprovante PDF com lista de presença e assinaturas.\n- As assinaturas usam a infraestrutura de mídia já existente, portanto sincronizam entre celular e PC pela Central Online.\n\nNão há alteração necessária no Code.gs para esta função.\n''',
        encoding='utf-8',
    )

    print(f'Fonte v3.38.3 montada em {app}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
