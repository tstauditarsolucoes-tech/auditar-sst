import 'dart:async';
/// Escopo isolado por operação: não grava opções em banco nem usa flags globais.
class ReportPdfEmphasisScope {
  ReportPdfEmphasisScope._();
  static const Symbol _key = #auditarReportEmphasis;
  static bool get enabled => Zone.current[_key] == true;
  static Future<T> run<T>(bool selected, Future<T> Function() build) {
    return runZoned<Future<T>>(build, zoneValues: {_key: selected});
  }
}
