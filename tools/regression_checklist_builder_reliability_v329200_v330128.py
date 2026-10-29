#!/usr/bin/env python3
"""Regression guard for the checklist-builder AI timeout/UI fix."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
platform = sys.argv[2] if len(sys.argv) > 2 else "android"
ai = (root / "lib/services/ai_assistant_service.dart").read_text(encoding="utf-8")
screen = (root / "lib/screens/checklist_templates_screen.dart").read_text(encoding="utf-8")
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

start = ai.find("  static Future<AiAssistantReply> _send(")
end = ai.find("  static Uint8List _prepareImage", start)
assert start >= 0 and end > start, "AI _send method not found"
send = ai[start:end]
assert "aiMode == 'checklist_builder'" in send
assert "const Duration(seconds: 120)" in send
assert "A criação do checklist com IA demorou mais que o limite." in send
assert "Nenhum checklist foi salvo." in send
assert "A análise da foto demorou além do limite da IA." in send

start = screen.find("  Future<void> _createChecklistWithAi() async {")
end = screen.find("  Future<void> _addTemplate() async {", start)
assert start >= 0 and end > start, "checklist builder method not found"
method = screen[start:end]
assert "ScaffoldMessenger.of(context).clearSnackBars();" in method
assert "AiAssistantReply reply;" in method
assert "try {" in method and "catch (_)" in method
assert "setState(() => generatingWithAi = false);" in method
assert "Não foi possível concluir a criação do checklist." in method
assert "Salvar checklist" in method
assert "insertChecklistTemplate(template)" in method

version = "3.29.200+342" if platform == "android" else "3.30.128+315"
assert f"version: {version}" in pub
print("CHECKLIST_BUILDER_RELIABILITY_REGRESSION_OK", platform, version)
