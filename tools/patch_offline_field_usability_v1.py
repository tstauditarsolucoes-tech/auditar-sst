#!/usr/bin/env python3
"""Aprimoramento discreto das sugestões offline durante a vistoria.

Executar APÓS patch_sst_deep_catalog_v2.py (Android/Windows).
Mantém Aplicar / Ajustar / Outras opções e os formulários originais.
Adiciona atalhos de consulta e permite ignorar uma sugestão só para a busca
atual, sem alterar/acrescentar nenhum registro ou memória persistida.
"""
from pathlib import Path
import hashlib
import re
import sys

if len(sys.argv) != 2:
    raise SystemExit("Uso: patch_offline_field_usability_v1.py <APP_DIR>")
root = Path(sys.argv[1])
widget = root / "lib/widgets/offline_report_inline_suggestions.dart"
if not widget.is_file():
    raise SystemExit("Tela de sugestão offline não localizada")
all_files = [
    p for folder in (root / "lib", root / "painel_web_google_apps_script")
    if folder.is_dir() for p in folder.rglob("*") if p.is_file() and p != widget
]
protected = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in all_files}
source = widget.read_text(encoding="utf-8")
if "class _OfflineReportInlineSuggestionsState extends State<" in source:
    raise SystemExit("Atalhos já instalados; não duplicar a melhoria")

def replace_one(old, new, label):
    global source
    n = source.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: encontradas {n} ocorrências (esperada 1)")
    source = source.replace(old, new, 1)

replace_one(
    "class OfflineReportInlineSuggestions extends StatelessWidget {",
    "class OfflineReportInlineSuggestions extends StatefulWidget {",
    "Componente atual",
)
replace_one(
    "  final ValueChanged<OfflineInlineSuggestion> onSelected;\n\n  Widget _row(",
    """  final ValueChanged<OfflineInlineSuggestion> onSelected;

  @override
  State<OfflineReportInlineSuggestions> createState() =>
      _OfflineReportInlineSuggestionsState();
}

class _OfflineReportInlineSuggestionsState
    extends State<OfflineReportInlineSuggestions> {
  // Feedback LOCAL e temporário: nada é excluído da biblioteca.
  final Set<String> _ignoredForThisDescription = <String>{};

  @override
  void didUpdateWidget(covariant OfflineReportInlineSuggestions oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.query != widget.query ||
        oldWidget.contextTerms.join('|') != widget.contextTerms.join('|')) {
      _ignoredForThisDescription.clear();
    }
  }

  void _ignore(OfflineInlineSuggestion item) {
    if (mounted) {
      setState(() => _ignoredForThisDescription.add(item.id));
    }
  }

  Widget _row(""",
    "Estado da lista sem alterar sua API",
)
# No cartão principal, X ignora o modelo atual em UM toque.
replace_one(
    "            const Icon(Icons.chevron_right_rounded, size: 18),",
    """            if (compact)
              IconButton(
                key: const ValueKey('offline-suggestion-ignore'),
                tooltip: 'Não corresponde à situação',
                icon: const Icon(Icons.close_rounded, size: 19),
                onPressed: () => _ignore(item),
                constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
                padding: EdgeInsets.zero,
              )
            else
              const Icon(Icons.chevron_right_rounded, size: 18),""",
    "Ignorar com um toque",
)
source, n = re.subn(
    r"_OfflineReviewDialog\(\s*item:\s*item\s*\)",
    "_OfflineReviewDialog(item: item, onDismiss: () => _ignore(item))",
    source,
)
if n != 1:
    raise RuntimeError(f"Feedback na revisão: {n} chamadas")
replace_one(
    "if (selected != null && context.mounted) onSelected(selected);",
    "if (selected != null && context.mounted) widget.onSelected(selected);",
    "Seleção revisada",
)
source, n = re.subn(
    r"(?<![\w.])onSelected\s*\(\s*OfflineInlineSuggestion\(",
    "widget.onSelected(OfflineInlineSuggestion(",
    source,
)
if n != 1:
    raise RuntimeError(f"Aplicação original: {n} chamadas")
replace_one(
    "  Future<void> _browseCatalog(BuildContext context) async {\n"
    "    final search = TextEditingController();\n"
    "    var selected = 'Todas';",
    """  Future<void> _browseCatalog(
    BuildContext context, {
    String initialSearch = '',
    String initialStandard = 'Todas',
  }) async {
    final search = TextEditingController(text: initialSearch);
    var selected = initialStandard;""",
    "Pesquisa da biblioteca já existente",
)
pattern = re.compile(
    r"  Widget _browseButton\(BuildContext context\)\s*=>\s*"
    r"OutlinedButton\.icon\((?:(?!\n  \);)[\s\S])*\n  \);"
)
matches = list(pattern.finditer(source))
if len(matches) != 1:
    raise RuntimeError(f"Botão de consulta por NR: {len(matches)} ocorrências")
old_button = matches[0].group(0)
button = """  Widget _browseButton(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 8),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        OutlinedButton.icon(
          onPressed: () => _browseCatalog(context),
          icon: const Icon(Icons.menu_book_outlined),
          label: const Text('Consultar biblioteca por NR'),
        ),
        const SizedBox(height: 6),
        Wrap(
          spacing: 6,
          runSpacing: 2,
          children: [
            ActionChip(
              key: const ValueKey('offline-shortcut-extintor'),
              label: const Text('Extintor'),
              onPressed: () => _browseCatalog(
                context, initialSearch: 'extintor'),
            ),
            ActionChip(
              key: const ValueKey('offline-shortcut-maquinas'),
              label: const Text('Máquinas'),
              onPressed: () => _browseCatalog(
                context, initialStandard: 'NR-12'),
            ),
            ActionChip(
              key: const ValueKey('offline-shortcut-altura'),
              label: const Text('Altura'),
              onPressed: () => _browseCatalog(
                context, initialStandard: 'NR-35'),
            ),
            ActionChip(
              key: const ValueKey('offline-shortcut-epi'),
              label: const Text('EPI'),
              onPressed: () => _browseCatalog(
                context, initialStandard: 'NR-06'),
            ),
          ],
        ),
      ],
    ),
  );"""
source = source.replace(old_button, button, 1)

# Só no build do widget: nunca modificar o algoritmo de correspondência.
start = source.index("class _OfflineReportInlineSuggestionsState")
build = source.index("  @override\n  Widget build(BuildContext context) {", start)
end = source.index("class _OfflineReviewDialog extends StatefulWidget", build)
body = source[build:end]
body = re.sub(r"(?<![\w.])\bquery\b", "widget.query", body)
body = re.sub(r"(?<![\w.])\bcontextTerms\b", "widget.contextTerms", body)
raw_line = "        final items = snapshot.data ?? const <OfflineInlineSuggestion>[];"
if body.count(raw_line) != 1:
    raise RuntimeError("Lista original de resultados diferente do esperado")
body = body.replace(
    raw_line,
    """        final rawItems = snapshot.data ?? const <OfflineInlineSuggestion>[];
        final items = rawItems
            .where((item) => !_ignoredForThisDescription.contains(item.id))
            .toList(growable: false);""",
    1,
)
message = "OfflineReasoning.explicitSafeOrUncertain(widget.query)"
# O aviso ao ignorar tudo é mais fiel que a mensagem padrão de "nenhum modelo".
if message not in body:
    raise RuntimeError("Mensagem de resultados ausentes modificada")
body = body.replace(
    message,
    """rawItems.isNotEmpty
                           ? 'Sugestões ignoradas para esta descrição. '
                             'Ajuste o texto para buscar novamente.'
                           : OfflineReasoning.explicitSafeOrUncertain(widget.query)""",
    1,
)
source = source[:build] + body + source[end:]

# Mesmo no diálogo de revisão, a escolha "Não corresponde" é reversível
# quando o técnico alterar o texto da descrição.
replace_one(
    "  const _OfflineReviewDialog({required this.item});\n"
    "  final OfflineInlineSuggestion item;",
    """  const _OfflineReviewDialog({required this.item, this.onDismiss});
  final OfflineInlineSuggestion item;
  final VoidCallback? onDismiss;""",
    "Feedback opcional na revisão",
)
dialog_at = source.index("class _OfflineReviewDialogState")
action_at = source.index("actions: [", dialog_at)
if source.find("actions: [", action_at + 1) != -1:
    raise RuntimeError("Múltiplos blocos de ações no diálogo")
source = source[:action_at] + source[action_at:].replace(
    "actions: [",
    """actions: [
        TextButton(
          onPressed: busy ? null : () {
            widget.onDismiss?.call();
            Navigator.pop(context);
          },
          child: const Text('Não corresponde'),
        ),""",
    1,
)
# Não altera arquivos fora do widget, não aprende o feedback como erro global.
widget.write_text(source, encoding="utf-8", newline="\n")
for path, digest in protected.items():
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, (
        "Arquivo protegido alterado: " + str(path)
    )
assert "OfflineReportInlineSuggestionService.learnApplied" in source
assert "if (compact)" in source
assert "widget.onSelected(selected)" in source
assert "Consultar biblioteca por NR" in source
assert "Aplicar texto revisado" in source
print("OFFLINE_FIELD_USABILITY_V1_OK | UI_PRESERVED | LOCAL_IGNORE_ONLY")
