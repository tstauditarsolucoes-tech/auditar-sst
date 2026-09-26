#!/usr/bin/env python3
"""Render two protected photos per record in both field report styles."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); platform=sys.argv[2]
assert platform in ('android','windows')
p=root/'lib/services/express_round_pdf_service.dart'
s=p.read_text(encoding='utf-8')
def one(old,new,label):
 global s
 count=s.count(old)
 if count!=1:raise RuntimeError(f'{label}: expected 1 match, got {count}')
 s=s.replace(old,new,1)

one("""    final photo = _photo(record);
    final p = record.payload;
    final conform = _conformity(record);""",
"""    final photo = _photo(record);
    final photo2 = _secondPhoto(record);
    final p = record.payload;
    final conform = _conformity(record);""",'photo second declaration')
one("""                      : pw.Image(
                        photo,
                        width: 225,
                        height: 145,
                        fit: pw.BoxFit.contain,
                      ),
            ),
            pw.Container(width: .6, height: 155, color: PdfColors.grey500),""",
"""                      : photo2 == null
                          ? pw.Image(photo,width:225,height:145,
                              fit:pw.BoxFit.contain)
                          : pw.Row(children:[
                              pw.Image(photo,width:110,height:145,
                                  fit:pw.BoxFit.contain),
                              pw.SizedBox(width:5),
                              pw.Image(photo2,width:110,height:145,
                                  fit:pw.BoxFit.contain),
                            ]),
            ),
            pw.Container(width: .6, height: 155, color: PdfColors.grey500),""",'photo + text card with two evidence slots')
one("""    final p = record.payload;
    final photo = _photo(record);
    final conform = _conformity(record);""",
"""    final p = record.payload;
    final photo = _photo(record);
    final photo2 = _secondPhoto(record);
    final conform = _conformity(record);""",'technical photo2 declaration')
one("""      if (includePhoto && photo != null) ...[
        pw.SizedBox(height: 7),
        pw.Container(
          height: 180,
          width: double.infinity,
          child: pw.Image(photo, height: 180, fit: pw.BoxFit.contain),
        ),
      ],""",
"""      if (includePhoto && (photo != null || photo2 != null)) ...[
        pw.SizedBox(height:7),
        pw.Container(height:180,width:double.infinity,
          child:pw.Row(mainAxisAlignment:pw.MainAxisAlignment.center,
            children:[
              if(photo != null) pw.Image(photo,width:230,height:175,
                fit:pw.BoxFit.contain),
              if(photo != null && photo2 != null) pw.SizedBox(width:8),
              if(photo2 != null) pw.Image(photo2,width:230,height:175,
                fit:pw.BoxFit.contain),
            ],
          ),
        ),
      ],""",'technical photo pair')
needle="""  static Future<pw.ImageProvider?> _localImage(String path) async {"""
assert s.count(needle)==1
s=s.replace(needle,"""  static pw.MemoryImage? _secondPhoto(SstRecord record) {
    final path='${record.payload['photoPath2'] ?? ''}'.trim();
    if(path.isEmpty) return null;
    final f=File(path);
    if(!f.existsSync()) return null;
    try { return pw.MemoryImage(f.readAsBytesSync()); }
    catch (_) { return null; }
  }

"""+needle,1)
assert 'final photo2 = _secondPhoto(record);' in s
p.write_text(s,encoding='utf-8',newline='\n')
print('FIELD_REPORT_SECOND_PHOTO_OK',platform)
