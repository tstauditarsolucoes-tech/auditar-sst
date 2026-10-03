import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../models.dart';
import '../services/document_delivery_service.dart';

/// Reusable button action for every existing PDF-producing module.
class DocumentDispatchDialog {
  static Future<bool> send(
    BuildContext context, {
    required Company company,
    required String documentId,
    required String category,
    required String title,
    required String fileName,
    required Future<Uint8List> Function() generatePdf,
  }) async {
    if (company.reportEmail.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Cadastre o e-mail de relatórios na ficha da empresa.')));
      return false;
    }
    final confirmed = await showDialog<bool>(context: context, builder: (dialogContext) => AlertDialog(
      title: const Text('Enviar documento por e-mail?'),
      content: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start,
        children: [Text('Empresa: ${company.name}'), const SizedBox(height: 8),
          Text('Documento: $title'), const SizedBox(height: 8),
          Text('Para: ${company.reportEmail}'),
          if (company.secondaryReportEmail.trim().isNotEmpty)
            Text('Cópia: ${company.secondaryReportEmail}'),
          const SizedBox(height: 8),
          const Text('Será gerado um PDF com os registros e evidências disponíveis.')]),
      actions: [TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const Text('Cancelar')),
        FilledButton(onPressed: () => Navigator.pop(dialogContext, true), child: const Text('Confirmar envio'))],
    ));
    if (confirmed != true || !context.mounted) return false;
    try {
      final bytes = await generatePdf();
      if (bytes.isEmpty || bytes.length > 7500000) {
        throw StateError('PDF acima do limite de 7 MB ou vazio.');
      }
      final result = await DocumentDeliveryService.send(
        companyId: company.id, companyName: company.name, documentId: documentId,
        category: category, title: title, to: company.reportEmail,
        cc: company.secondaryReportEmail, fileName: fileName, bytes: bytes);
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(result)));
      return true;
    } catch (error) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Envio não confirmado: $error')));
      return false;
    }
  }
}