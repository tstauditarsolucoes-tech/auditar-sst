import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('logo oficial SST está empacotada e pode ser incorporada ao PDF', () async {
    final data = await rootBundle.load('assets/branding/sst_green_official.png');
    final bytes = data.buffer.asUint8List();
    expect(bytes.length, greaterThan(3000));
    expect(bytes.sublist(0, 8), <int>[137, 80, 78, 71, 13, 10, 26, 10]);

    final image = pw.MemoryImage(bytes);
    final doc = pw.Document();
    doc.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        build: (_) => pw.Row(children: [
          pw.Image(image, width: 64, height: 64, fit: pw.BoxFit.contain),
          pw.Spacer(),
          pw.Image(image, width: 64, height: 64, fit: pw.BoxFit.contain),
        ]),
      ),
    );
    final result = await doc.save();
    expect(result.length, greaterThan(1000));
  });
}
