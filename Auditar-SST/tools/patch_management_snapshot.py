#!/usr/bin/env python3
"""Inclui Agenda SST no snapshot do painel sem substituir o serviço original.

A alteração é deliberadamente pequena: preserva integralmente o arquivo
management_panel_service.dart vindo da base e acrescenta apenas os dados que o
painel gerencial 3.22 precisa para exibir a agenda semanal.
"""
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Marcador não encontrado ao aplicar {label}.")
    return text.replace(old, new, 1)


def patch(path: Path) -> None:
    if not path.exists():
        raise RuntimeError(f"Serviço do painel não encontrado: {path}")

    text = path.read_text(encoding="utf-8")
    if "'agendaSummary': agendaSummary" in text and "final agendaRecords" in text:
        return

    text = replace_once(
        text,
        """    final improvements = await db.getSstRecords(\n      type: 'MELHORIA',\n      companyId: company.id,\n    );\n    final snapshotNow = DateTime.now();""",
        """    final improvements = await db.getSstRecords(\n      type: 'MELHORIA',\n      companyId: company.id,\n    );\n    final agendaRecords = await db.getSstRecords(\n      type: 'AGENDA',\n      companyId: company.id,\n    );\n    final snapshotNow = DateTime.now();""",
        "leitura dos registros de Agenda SST",
    )

    agenda_logic = """    final improvementRows = improvements.map(cleanImprovement).toList();\n\n    Map<String, Object?> cleanAgenda(SstRecord record) {\n      final payload = record.payload;\n      return {\n        'id': record.id,\n        'title': record.title,\n        'date': record.date.toIso8601String(),\n        'dueDate': record.dueDate?.toIso8601String() ?? '',\n        'status': record.status,\n        'priority': record.priority,\n        'sector': sectorNameFor(record.sectorId),\n        'location': '${payload['location'] ?? ''}',\n        'responsible': '${payload['responsible'] ?? ''}',\n        'description': '${payload['description'] ?? ''}',\n        'notes': '${payload['notes'] ?? ''}',\n        'subtype': '${payload['subtype'] ?? ''}',\n      };\n    }\n\n    final agendaRows = agendaRecords.map(cleanAgenda).toList()\n      ..sort((a, b) {\n        final aDate = DateTime.tryParse('${a['date'] ?? ''}');\n        final bDate = DateTime.tryParse('${b['date'] ?? ''}');\n        if (aDate == null && bDate == null) return 0;\n        if (aDate == null) return 1;\n        if (bDate == null) return -1;\n        return aDate.compareTo(bDate);\n      });\n\n    final todayAgenda = DateTime(now.year, now.month, now.day);\n    final weekAgendaEnd = todayAgenda.add(const Duration(days: 7));\n\n    bool agendaCompleted(SstRecord record) {\n      final value = record.status.toLowerCase();\n      return value.contains('conclu') || value.contains('realiz');\n    }\n\n    bool agendaOverdue(SstRecord record) {\n      if (agendaCompleted(record)) return false;\n      final day = DateTime(record.date.year, record.date.month, record.date.day);\n      return day.isBefore(todayAgenda);\n    }\n\n    bool agendaThisWeek(SstRecord record) {\n      final day = DateTime(record.date.year, record.date.month, record.date.day);\n      return !day.isBefore(todayAgenda) && day.isBefore(weekAgendaEnd);\n    }\n\n    final agendaSummary = <String, Object?>{\n      'total': agendaRecords.length,\n      'today': agendaRecords.where((record) {\n        final day = DateTime(record.date.year, record.date.month, record.date.day);\n        return day.isAtSameMomentAs(todayAgenda) && !agendaCompleted(record);\n      }).length,\n      'next7Days': agendaRecords.where(agendaThisWeek).length,\n      'overdue': agendaRecords.where(agendaOverdue).length,\n      'completed': agendaRecords.where(agendaCompleted).length,\n    };\n"""

    text = replace_once(
        text,
        "    final improvementRows = improvements.map(cleanImprovement).toList();\n",
        agenda_logic,
        "tratamento dos dados da Agenda SST",
    )

    text = replace_once(
        text,
        "      'schemaVersion': 9,\n",
        "      'schemaVersion': 10,\n",
        "versão do snapshot",
    )

    text = replace_once(
        text,
        "      'improvementSummary': improvementSummary,\n      'improvements': improvementRows,\n",
        "      'improvementSummary': improvementSummary,\n      'improvements': improvementRows,\n      'agendaSummary': agendaSummary,\n      'agenda': agendaRows,\n",
        "campos da Agenda SST no snapshot",
    )

    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: patch_management_snapshot.py <pasta-do-projeto>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    patch(root / "lib" / "services" / "management_panel_service.dart")
    print("Agenda SST adicionada ao snapshot gerencial sem substituir o serviço original.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
