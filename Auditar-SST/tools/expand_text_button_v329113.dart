import 'package:flutter/material.dart';

/// Allows editing multi-line inspection text without losing the original draft.
class ExpandTextButton extends StatelessWidget {
  final TextEditingController? controller;
  final String title;

  const ExpandTextButton({
    super.key,
    required this.controller,
    this.title = 'Texto completo',
  });

  @override
  Widget build(BuildContext context) => IconButton(
    tooltip: 'Abrir texto em tela cheia',
    icon: const Icon(Icons.open_in_full_rounded, size: 20),
    onPressed: controller == null ? null : () async {
      final original = controller!;
      final edited = await Navigator.of(context).push<String>(
        MaterialPageRoute<String>(
          fullscreenDialog: true,
          builder: (_) => _ExpandedTextEditor(
            title: title,
            initialText: original.text,
          ),
        ),
      );
      if (edited == null) return;
      original.value = TextEditingValue(
        text: edited,
        selection: TextSelection.collapsed(offset: edited.length),
      );
    },
  );
}

class _ExpandedTextEditor extends StatefulWidget {
  final String title;
  final String initialText;
  const _ExpandedTextEditor({required this.title, required this.initialText});

  @override
  State<_ExpandedTextEditor> createState() => _ExpandedTextEditorState();
}

class _ExpandedTextEditorState extends State<_ExpandedTextEditor> {
  late final TextEditingController draft;

  @override
  void initState() {
    super.initState();
    draft = TextEditingController(text: widget.initialText);
  }

  @override
  void dispose() {
    draft.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: Text(widget.title),
      actions: [
        TextButton.icon(
          onPressed: () => Navigator.of(context).pop(draft.text),
          icon: const Icon(Icons.check_rounded),
          label: const Text('Salvar texto'),
        ),
      ],
    ),
    body: SafeArea(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: TextField(
          controller: draft,
          autofocus: true,
          expands: true,
          minLines: null,
          maxLines: null,
          keyboardType: TextInputType.multiline,
          textCapitalization: TextCapitalization.sentences,
          textAlignVertical: TextAlignVertical.top,
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'Escreva ou revise o texto completo aqui.',
            alignLabelWithHint: true,
          ),
        ),
      ),
    ),
  );
}
