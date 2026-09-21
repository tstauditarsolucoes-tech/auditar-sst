import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:uuid/uuid.dart';

import '../brand.dart';
import '../services/storage_service.dart';

class FacialConfirmationResult {
  final String confirmationId;
  final String localPath;
  final DateTime confirmedAt;

  const FacialConfirmationResult({
    required this.confirmationId,
    required this.localPath,
    required this.confirmedAt,
  });
}

class FacialConfirmationScreen extends StatefulWidget {
  final String participantName;
  final String contextLabel;

  const FacialConfirmationScreen({
    super.key,
    required this.participantName,
    required this.contextLabel,
  });

  @override
  State<FacialConfirmationScreen> createState() =>
      _FacialConfirmationScreenState();
}

class _FacialConfirmationScreenState extends State<FacialConfirmationScreen> {
  final picker = ImagePicker();

  bool consent = false;
  bool busy = false;
  String photoPath = '';

  Future<void> _capture() async {
    if (!consent) {
      _toast('Confirme que o participante foi informado sobre a foto.');
      return;
    }
    setState(() => busy = true);
    try {
      final shot = await picker.pickImage(
        source: ImageSource.camera,
        preferredCameraDevice: CameraDevice.front,
        imageQuality: 78,
        maxWidth: 900,
        maxHeight: 1200,
      );
      if (shot == null) return;
      if (!mounted) return;
      setState(() => photoPath = shot.path);
    } catch (error) {
      _toast('Não foi possível abrir a câmera: $error');
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _confirm() async {
    if (photoPath.isEmpty || busy) return;
    setState(() => busy = true);
    try {
      final persisted = await StorageService.persistImage(
        photoPath,
        folder: 'assinaturas_faciais',
      );
      if (!mounted) return;
      Navigator.of(context).pop(
        FacialConfirmationResult(
          confirmationId: const Uuid().v4(),
          localPath: persisted,
          confirmedAt: DateTime.now(),
        ),
      );
    } catch (error) {
      _toast('Não foi possível salvar a confirmação facial: $error');
      if (mounted) setState(() => busy = false);
    }
  }

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final ready = photoPath.isNotEmpty;
    return Scaffold(
      appBar: AppBar(title: const Text('Assinatura facial')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              widget.participantName,
              style: const TextStyle(
                fontSize: 21,
                fontWeight: FontWeight.w900,
                color: AuditarBrand.navy,
              ),
            ),
            const SizedBox(height: 3),
            Text(
              widget.contextLabel,
              style: const TextStyle(color: Colors.black54),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(
                          Icons.face_retouching_natural_outlined,
                          color: AuditarBrand.greenDark,
                        ),
                        SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Confirmação facial',
                            style: TextStyle(
                              fontWeight: FontWeight.w900,
                              color: AuditarBrand.navy,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'A foto será vinculada a esta ficha como confirmação do participante, junto com a data e hora do registro.',
                      style: TextStyle(fontSize: 12.5, height: 1.35),
                    ),
                    const SizedBox(height: 10),
                    CheckboxListTile(
                      contentPadding: EdgeInsets.zero,
                      value: consent,
                      controlAffinity: ListTileControlAffinity.leading,
                      title: const Text(
                        'O participante foi informado e concordou com o registro da foto nesta ficha.',
                        style: TextStyle(fontSize: 12.5),
                      ),
                      onChanged: busy
                          ? null
                          : (value) =>
                              setState(() => consent = value == true),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 10),
            if (ready && File(photoPath).existsSync())
              ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: Image.file(
                  File(photoPath),
                  height: 300,
                  fit: BoxFit.cover,
                ),
              )
            else
              Container(
                height: 230,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(18),
                  color: const Color(0xFFF1F5F6),
                  border: Border.all(color: const Color(0xFFD8E3E2)),
                ),
                child: const Icon(
                  Icons.face_outlined,
                  size: 76,
                  color: Colors.black26,
                ),
              ),
            const SizedBox(height: 12),
            FilledButton.tonalIcon(
              onPressed: busy || !consent ? null : _capture,
              icon: const Icon(Icons.camera_alt_outlined),
              label: Text(
                ready ? 'Refazer foto' : 'Abrir câmera frontal',
              ),
            ),
            const SizedBox(height: 18),
            FilledButton.icon(
              onPressed: ready && !busy ? _confirm : null,
              icon: busy
                  ? const SizedBox(
                      width: 17,
                      height: 17,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.verified_user_outlined),
              label: const Text('Confirmar assinatura facial'),
            ),
            const SizedBox(height: 10),
            const Text(
              'A assinatura desenhada continua disponível como alternativa.',
              style: TextStyle(
                fontSize: 11.5,
                color: Colors.black54,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
