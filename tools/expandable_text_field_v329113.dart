import 'package:flutter/material.dart';

/// Campo multilinha com edição ampliada sem trocar o controller original.
/// Ao fechar a tela ampliada, o conteúdo já permanece no formulário de origem.
class ExpandableTextField extends StatelessWidget {
  final TextEditingController controller;
  final InputDecoration decoration;
  final int minLines;
  final int maxLines;
  final String? Function(String?)? validator;
  final TextCapitalization textCapitalization;
  final bool enabled;
  final bool autofocus;

  const ExpandableTextField({
    super.key,
    required this.controller,
    required this.decoration,
    this.minLines = 2,
    this.maxLines = 4,
    this.validator,
    this.textCapitalization = TextCapitalization.sentences,
    this.enabled = true,
    this.autofocus = false,
  });

  String get _title {
    final label = decoration.labelText?.trim();
    return (label == null || label.isEmpty) ? 'Texto completo' : label;
  }

  @override
  Widget build(BuildContext context) {
    return TextFormField(
      controller: controller,
      enabled: enabled,
      autofocus: autofocus,
      minLines: minLines,
      maxLines: maxLines,
      textCapitalization: textCapitalization,
      validator: validator,
      decoration: decoration.copyWith(
        suffixIcon: IconButton(
          tooltip: 'Expandir texto',
          onPressed: enabled ? () => _openExpanded(context) : null,
          icon: const Icon(Icons.open_in_full_rounded),
        ),
      ),
    );
  }

  Future<void> _openExpanded(BuildContext context) async {
    final focus = FocusNode();
    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (pageContext) => Scaffold(
          appBar: AppBar(
            title: Text(_title, maxLines: 1, overflow: TextOverflow.ellipsis),
            actions: [
              TextButton.icon(
                onPressed: () => Navigator.pop(pageContext),
                icon: const Icon(Icons.check_rounded),
                label: const Text('Concluir'),
              ),
            ],
          ),
          body: SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                controller: controller,
                focusNode: focus,
                autofocus: true,
                expands: true,
                minLines: null,
                maxLines: null,
                textAlignVertical: TextAlignVertical.top,
                textCapitalization: textCapitalization,
                decoration: InputDecoration(
                  labelText: _title,
                  alignLabelWithHint: true,
                  hintText: decoration.hintText,
                  helperText: 'Edite o texto completo. As alterações são salvas no campo original.',
                  border: const OutlineInputBorder(),
                ),
              ),
            ),
          ),
          bottomNavigationBar: SafeArea(
            minimum: const EdgeInsets.all(12),
            child: FilledButton.icon(
              onPressed: () => Navigator.pop(pageContext),
              icon: const Icon(Icons.check_circle_outline),
              label: const Text('Voltar para a vistoria'),
            ),
          ),
        ),
      ),
    );
    focus.dispose();
  }
}
