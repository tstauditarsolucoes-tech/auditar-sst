/// Cria chaves locais sem colisões entre identificadores que contêm
/// '_' ou outros separadores. Os comprimentos referem-se ao texto URI
/// codificado; em cada segmento o separador '|' torna-se '%7C'.
///
/// Exemplo da colisão antiga:
///   usuário a_b / empresa c  ==  usuário a / empresa b_c
/// no formato a_b_c. Esta codificação evita a ambiguidade.
String sstScopedKey(String namespace, List<String> segments) {
  if (!RegExp(r'^[a-z0-9_]{2,60}$').hasMatch(namespace) ||
      segments.isEmpty || segments.length > 7) {
    throw ArgumentError('Namespace SST inválido');
  }
  final encoded = <String>[];
  for (final segment in segments) {
    if (segment.isEmpty || segment.length > 512) {
      throw ArgumentError('Identificador SST ausente ou excessivo');
    }
    final value = Uri.encodeComponent(segment);
    encoded.add('${value.length}:$value');
  }
  return '$namespace|${encoded.join('|')}';
}
