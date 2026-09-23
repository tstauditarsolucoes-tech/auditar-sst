import 'package:flutter/material.dart';

/// Opens a large editor for descriptions, observations and recommendations.
/// Changes are committed only after Save. Existing small field is unchanged.
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
      final draft = TextEditingController(text: original.text);
      try {
        final edited = await Navigator.of(context).push<String>(
          MaterialPageRoute<String>(
            fullscreenDialog: true,
            builder: (pageContext) => Scaffold(
              appBar: AppBar(
                title: Text(title),
                actions: [
                  TextButton.icon(
                    onPressed: () => Navigator.of(pageContext).pop(draft.text),
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
            ),
          ),
        );
        if (edited != null) {
          original.value = TextEditingValue(
            text: edited,
            selection: TextSelection.collapsed(offset: edited.length),
          );
        }
      } finally {
        draft.dispose();
      }
    },
  );
