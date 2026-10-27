import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/services/report_pdf_emphasis_scope.dart';
void main() {
 test('opção desligada por padrão e isolada por emissão', () async {
   expect(ReportPdfEmphasisScope.enabled, false);
   final result=await Future.wait([
     ReportPdfEmphasisScope.run(true,() async {
       await Future<void>.delayed(const Duration(milliseconds:1));
       return ReportPdfEmphasisScope.enabled;
     }),
     ReportPdfEmphasisScope.run(false,() async {
       await Future<void>.delayed(const Duration(milliseconds:1));
       return ReportPdfEmphasisScope.enabled;
     }),
   ]);
   expect(result,[true,false]);
   expect(ReportPdfEmphasisScope.enabled,false);
 });
}
