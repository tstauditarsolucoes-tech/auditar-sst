/// Centraliza validação, remoção de duplicatas e limite dos destinatários.
/// A lista de adicionais reutiliza a coluna textual secondary_report_email;
/// não exige migração do banco nem alteração do protocolo de sincronização.
class ReportRecipients {
  static const int maxRecipients = 10;
  static final RegExp _email = RegExp(r'^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$');

  static List<String> _parts(String raw) => raw
      .split(RegExp(r'[,;\r\n]+'))
      .map((value) => value.trim().toLowerCase())
      .where((value) => value.isNotEmpty)
      .toList();

  static List<String> parse(String primary, String additional) {
    final unique = <String>{};
    for (final address in [..._parts(primary), ..._parts(additional)]) {
      unique.add(address);
    }
    return unique.toList(growable: false);
  }

  static List<String> additional(String primary, String raw) =>
      parse(primary, raw).where((email) => email != primary.trim().toLowerCase()).toList();

  static String? validationError(String primary, String additional) {
    final main = primary.trim().toLowerCase();
    if (main.isNotEmpty && !_email.hasMatch(main)) {
      return 'Confira o e-mail principal da empresa.';
    }
    final recipients = parse(primary, additional);
    if (recipients.length > maxRecipients) {
      return 'Cadastre até $maxRecipients e-mails por empresa.';
    }
    for (final address in recipients) {
      if (address.length > 254 || !_email.hasMatch(address)) {
        return 'Confira o endereço $address.';
      }
    }
    return null;
  }

  static String normalizedAdditional(String primary, String additional) =>
      ReportRecipients.additional(primary, additional).join(', ');
}
