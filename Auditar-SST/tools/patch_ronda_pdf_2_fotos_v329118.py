#!/usr/bin/env python3
"""Render two photo evidence slots in the Ronda PDF without altering checklist or sync."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
p=root/'lib/services/express_round_pdf_service.dart'
s=p.read_text(encoding='utf-8')
def once(old,new,label):
    global s
    hits=s.count(old)
    if hits!=1: raise RuntimeError(f'{label}: expected once, found {hits}')
    s=s.replace(old,new,1)

once("""    final photo = _photo(record);
    final p = record.payload;
    final conform = _conformity(record);""", """    final firstPhoto = _photo(record);
    final secondPhoto = _secondPhoto(record);
    final photo = firstPhoto ?? secondPhoto;
    final photo2 = firstPhoto == null ? null : secondPhoto;
    final p = record.payload;
    final conform = _conformity(record);""", 'photographic photo vars')
once("""                      : pw.Image(
                        photo,
                        width: 225,
                        height: 145,
                        fit: pw.BoxFit.contain,
                      ),""","""                      : photo2 == null
                          ? pw.Image(photo, width: 225, height: 145,
                              fit: pw.BoxFit.contain)
                          : pw.Row(children: [
                              pw.Image(photo, width: 110, height: 145,
                                  fit: pw.BoxFit.contain),
                              pw.SizedBox(width: 4),
                              pw.Image(photo2, width: 110, height: 145,
                                  fit: pw.BoxFit.contain),
                            ]),""",'photographic two images')
once("""    final p = record.payload;
    final photo = _photo(record);
    final conform = _conformity(record);""","""    final p = record.payload;
    final photo = _photo(record);
    final photo2 = _secondPhoto(record);
    final conform = _conformity(record);""",'technical photo vars')
once("""      if (includePhoto && photo != null) ...[
        pw.SizedBox(height: 7),
        pw.Container(
          height: 180,
          width: double.infinity,
          child: pw.Image(photo, height: 180, fit: pw.BoxFit.contain),
        ),
      ],""","""      if (includePhoto && (photo != null || photo2 != null)) ...[
        pw.SizedBox(height: 7),
        pw.Container(
          height: 180,
          width: double.infinity,
          child: pw.Row(
            mainAxisAlignment: pw.MainAxisAlignment.center,
            children: [
              if (photo != null)
                pw.Image(photo, width: photo2 == null ? 470 : 230,
                  height: 175, fit: pw.BoxFit.contain),
              if (photo != null && photo2 != null) pw.SizedBox(width: 8),
              if (photo2 != null)
                pw.Image(photo2, width: photo == null ? 470 : 230,
                  height: 175, fit: pw.BoxFit.contain),
            ],
          ),
        ),
      ],""",'technical two images')
once("""  static pw.MemoryImage? _photo(SstRecord record) {
""","""  static pw.MemoryImage? _secondPhoto(SstRecord record) {
    final path = '${record.payload['photoPath2'] ?? ''}'.trim();
    if (path.isEmpty) return null;
    final file = File(path);
    if (!file.existsSync()) return null;
    try {
      return pw.MemoryImage(file.readAsBytesSync());
    } catch (_) {
      return null;
    }
  }

  static pw.MemoryImage? _photo(SstRecord record) {
""",'second photo source')
p.write_text(s,encoding='utf-8',newline='\n')
assert s.count('final photo2 = ') == 2
assert "photoPath2" in s
print('ROUND_PDF_TWO_PHOTOS_OK',platform)
