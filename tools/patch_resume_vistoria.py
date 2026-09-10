#!/usr/bin/env python3
"""Destaca e abre diretamente a vistoria em andamento na home."""
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Marcador não encontrado: {label}")
    return text.replace(old, new, 1)


def patch_history(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "class HistoryScreen extends StatefulWidget {\n  final String? companyId;\n\n  const HistoryScreen({super.key, this.companyId});",
        "class HistoryScreen extends StatefulWidget {\n  final String? companyId;\n  final bool resumeLatestDraft;\n\n  const HistoryScreen({\n    super.key,\n    this.companyId,\n    this.resumeLatestDraft = false,\n  });",
        "parâmetro de retomada do histórico",
    )
    text = replace_once(
        text,
        "class _HistoryScreenState extends State<HistoryScreen> {\n  List<Map<String, Object?>> rows = [];",
        "class _HistoryScreenState extends State<HistoryScreen> {\n  List<Map<String, Object?>> rows = [];\n  bool _autoResumeHandled = false;",
        "controle de retomada automática",
    )
    text = replace_once(
        text,
        """    if (mounted) {\n      setState(() => rows = result);\n    }\n  }\n\n  Future<void> _reopen(""",
        """    if (mounted) {\n      setState(() => rows = result);\n    }\n\n    if (mounted && widget.resumeLatestDraft && !_autoResumeHandled) {\n      _autoResumeHandled = true;\n      Map<String, Object?>? draft;\n      for (final row in result) {\n        if ('${row['status'] ?? ''}' != 'Finalizada') {\n          draft = row;\n          break;\n        }\n      }\n      if (draft != null) {\n        final target = draft;\n        WidgetsBinding.instance.addPostFrameCallback((_) {\n          if (mounted) _reopen(target);\n        });\n      }\n    }\n  }\n\n  Future<void> _reopen(""",
        "retomada automática do rascunho",
    )
    path.write_text(text, encoding="utf-8")


def patch_home(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "Widget _continueInspectionCard()" in text:
        return

    text = replace_once(
        text,
        "  int openNcs = 0;\n  bool loading = true;",
        "  int openNcs = 0;\n  Map<String, Object?>? activeInspection;\n  bool loading = true;",
        "estado da vistoria em andamento",
    )
    text = replace_once(
        text,
        "    final routine = await AppDatabase.instance.getRoutineTodaySummary();\n\n    if (!mounted) return;",
        "    final routine = await AppDatabase.instance.getRoutineTodaySummary();\n    final history = await AppDatabase.instance.getInspectionHistory();\n    Map<String, Object?>? inProgress;\n    for (final row in history) {\n      if ('${row['status'] ?? ''}' != 'Finalizada') {\n        inProgress = row;\n        break;\n      }\n    }\n\n    if (!mounted) return;",
        "leitura da vistoria em andamento",
    )
    text = replace_once(
        text,
        "      openNcs = ncRows.length;\n      loading = false;",
        "      openNcs = ncRows.length;\n      activeInspection = inProgress;\n      loading = false;",
        "estado da vistoria em andamento",
    )
    text = replace_once(
        text,
        "          _overviewPanel(desktop: false),\n          const SizedBox(height: 12),\n          _newInspectionButton(),",
        "          _overviewPanel(desktop: false),\n          const SizedBox(height: 12),\n          _continueInspectionCard(),\n          if (activeInspection != null) const SizedBox(height: 9),\n          _newInspectionButton(),",
        "atalho de retomada no celular",
    )
    text = replace_once(
        text,
        "                _overviewPanel(desktop: true),\n                const SizedBox(height: 22),",
        "                _overviewPanel(desktop: true),\n                const SizedBox(height: 12),\n                _continueInspectionCard(),\n                const SizedBox(height: 22),",
        "atalho de retomada no computador",
    )
    marker = "  Widget _newInspectionButton() {\n"
    card = """  Widget _continueInspectionCard() {\n    final inspection = activeInspection;\n    if (inspection == null) return const SizedBox.shrink();\n\n    final company = '${inspection['company_name'] ?? 'Empresa'}';\n    final area = '${inspection['area'] ?? ''}'.trim();\n    final site = '${inspection['worksite_name'] ?? ''}'.trim();\n    final sector = '${inspection['sector_name'] ?? ''}'.trim();\n    final location = [sector, area, site]\n        .where((value) => value.isNotEmpty)\n        .toSet()\n        .join(' • ');\n\n    return Card(\n      margin: EdgeInsets.zero,\n      color: const Color(0xFFFFF8E8),\n      child: InkWell(\n        borderRadius: BorderRadius.circular(16),\n        onTap: () => _open(const HistoryScreen(resumeLatestDraft: true)),\n        child: Padding(\n          padding: const EdgeInsets.all(14),\n          child: Row(\n            children: [\n              Container(\n                width: 44,\n                height: 44,\n                decoration: BoxDecoration(\n                  color: const Color(0xFFFFE7B5),\n                  borderRadius: BorderRadius.circular(12),\n                ),\n                child: const Icon(\n                  Icons.play_circle_outline_rounded,\n                  color: Color(0xFF9A5A00),\n                ),\n              ),\n              const SizedBox(width: 11),\n              Expanded(\n                child: Column(\n                  crossAxisAlignment: CrossAxisAlignment.start,\n                  children: [\n                    const Text(\n                      'Continuar vistoria em andamento',\n                      style: TextStyle(\n                        color: Color(0xFF6D4300),\n                        fontWeight: FontWeight.w900,\n                      ),\n                    ),\n                    const SizedBox(height: 3),\n                    Text(\n                      location.isEmpty ? company : '$company • $location',\n                      maxLines: 2,\n                      overflow: TextOverflow.ellipsis,\n                      style: const TextStyle(\n                        color: Color(0xFF805A1A),\n                        fontSize: 11.5,\n                      ),\n                    ),\n                  ],\n                ),\n              ),\n              const Icon(\n                Icons.chevron_right_rounded,\n                color: Color(0xFF9A5A00),\n              ),\n            ],\n          ),\n        ),\n      ),\n    );\n  }\n\n"""
    if marker not in text:
        raise RuntimeError("Marcador não encontrado: botão de nova vistoria")
    text = text.replace(marker, card + marker, 1)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: patch_resume_vistoria.py <pasta-do-projeto>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    patch_home(root / "lib" / "screens" / "home_screen.dart")
    patch_history(root / "lib" / "screens" / "history_screen.dart")
    print("Atalho de continuar vistoria aplicado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
