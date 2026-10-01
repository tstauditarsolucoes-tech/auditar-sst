class CorrectionRecurrenceGroup {
  final String sector;
  final List<Map<String, Object?>> records;

  const CorrectionRecurrenceGroup({
    required this.sector,
    required this.records,
  });

  int get count => records.length;
}

class CorrectionRecurrenceDetector {
  static const Set<String> _stopWords = {
    'a', 'ao', 'aos', 'as', 'com', 'da', 'das', 'de', 'do', 'dos', 'e', 'em',
    'esta', 'este', 'foi', 'local', 'na', 'nas', 'no', 'nos', 'o', 'os',
    'para', 'por', 'que', 'se', 'setor', 'uma', 'um',
  };

  static String _value(Map<String, Object?> row, String key) =>
      '\${row[key] ?? ''}'.trim();

  static String _fold(String value) {
    var text = value.toLowerCase().trim();
    const from = 'áàâãäéèêëíìîïóòôõöúùûüç';
    const to = 'aaaaaeeeeiiiiooooouuuuc';
    for (var i = 0; i < from.length; i++) {
      text = text.replaceAll(from[i], to[i]);
    }
    return text.replaceAll(RegExp(r'[^a-z0-9]+'), ' ').trim();
  }

  static Set<String> _tokens(String value) {
    final normalized = _fold(value);
    if (normalized.isEmpty) return const <String>{};
    return normalized
        .split(RegExp(r'\s+'))
        .where((word) => word.length >= 3 && !_stopWords.contains(word))
        .toSet();
  }

  static double similarity(String left, String right) {
    final a = _tokens(left);
    final b = _tokens(right);
    if (a.isEmpty || b.isEmpty) return 0;
    if (_fold(left) == _fold(right)) return 1;
    if (a.length < 2 || b.length < 2) return 0;
    final intersection = a.intersection(b).length;
    final smaller = a.length < b.length ? a.length : b.length;
    return smaller == 0 ? 0 : intersection / smaller;
  }

  static String sectorOf(Map<String, Object?> row) {
    final sector = _value(row, 'sector_name');
    if (sector.isNotEmpty) return sector;
    return _value(row, 'area');
  }

  static List<CorrectionRecurrenceGroup> detect(
    List<Map<String, Object?>> rows, {
    double threshold = 0.66,
  }) {
    if (rows.length < 2) return const <CorrectionRecurrenceGroup>[];
    final parent = List<int>.generate(rows.length, (index) => index);

    int find(int value) {
      var cursor = value;
      while (parent[cursor] != cursor) {
        parent[cursor] = parent[parent[cursor]];
        cursor = parent[cursor];
      }
      return cursor;
    }

    void join(int a, int b) {
      final pa = find(a);
      final pb = find(b);
      if (pa != pb) parent[pb] = pa;
    }

    for (var i = 0; i < rows.length; i++) {
      final descriptionA = _value(rows[i], 'description');
      final sectorA = _fold(sectorOf(rows[i]));
      if (descriptionA.isEmpty || sectorA.isEmpty) continue;
      for (var j = i + 1; j < rows.length; j++) {
        final sectorB = _fold(sectorOf(rows[j]));
        if (sectorA != sectorB || sectorB.isEmpty) continue;
        final descriptionB = _value(rows[j], 'description');
        if (descriptionB.isEmpty) continue;
        if (similarity(descriptionA, descriptionB) >= threshold) {
          join(i, j);
        }
      }
    }

    final grouped = <int, List<Map<String, Object?>>>{};
    for (var i = 0; i < rows.length; i++) {
      final root = find(i);
      (grouped[root] ??= <Map<String, Object?>>[]).add(rows[i]);
    }

    final result = <CorrectionRecurrenceGroup>[];
    for (final records in grouped.values) {
      if (records.length < 2) continue;
      result.add(
        CorrectionRecurrenceGroup(
          sector: sectorOf(records.first),
          records: List<Map<String, Object?>>.unmodifiable(records),
        ),
      );
    }
    result.sort((a, b) => b.count.compareTo(a.count));
    return result;
  }
}
