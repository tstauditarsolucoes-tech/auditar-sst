import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:image/image.dart' as img;
import 'package:image_picker/image_picker.dart';
import 'package:uuid/uuid.dart';

import '../brand.dart';
import '../services/storage_service.dart';

class FacialConfirmationResult {
  final String confirmationId;
  final String localPath;
  final DateTime confirmedAt;
  final String photoSha256;
  final String proofCode;

  const FacialConfirmationResult({
    required this.confirmationId,
    required this.localPath,
    required this.confirmedAt,
    required this.photoSha256,
    required this.proofCode,
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
  bool participantReviewed = false;
  bool busy = false;
  String photoPath = '';
  String qualityLabel = '';

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
        imageQuality: 82,
        maxWidth: 1080,
        maxHeight: 1440,
      );
      if (shot == null) return;

      final file = File(shot.path);
      final bytes = await file.readAsBytes();
      if (bytes.length < 12000) {
        throw StateError(
          'A foto ficou com qualidade muito baixa. Tire novamente com boa iluminação.',
        );
      }
      final decoded = img.decodeImage(bytes);
      if (decoded == null) {
        throw StateError('Não foi possível validar a imagem capturada.');
      }
      if (decoded.width < 320 || decoded.height < 320) {
        throw StateError(
          'A foto ficou pequena demais. Aproxime o rosto e tente novamente.',
        );
      }

      if (!mounted) return;
      setState(() {
        photoPath = shot.path;
        participantReviewed = false;
        qualityLabel = '${decoded.width} × ${decoded.height} px • foto frontal';
      });
    } catch (error) {
      _toast(error.toString().replaceFirst('Bad state: ', ''));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> _confirm() async {
    if (photoPath.isEmpty || busy || !participantReviewed) return;
    setState(() => busy = true);
    try {
      final persisted = await StorageService.persistImage(
        photoPath,
        folder: 'assinaturas_faciais',
      );
      final bytes = await File(persisted).readAsBytes();
      final digest = sha256.convert(bytes).toString();
      final proofCode = 'FAC-${digest.substring(0, 10).toUpperCase()}';
      if (!mounted) return;
      Navigator.of(context).pop(
        FacialConfirmationResult(
          confirmationId: const Uuid().v4(),
          localPath: persisted,
          confirmedAt: DateTime.now(),
          photoSha256: digest,
          proofCode: proofCode,
        ),
      );
    } catch (error) {
      _toast('Não foi possível salvar a confirmação facial: $error');
      if (mounted) setState(() => busy = false);
    }
  }

  void _reset() {
    setState(() {
      photoPath = '';
      participantReviewed = false;
      qualityLabel = '';
    });
  }

  void _toast(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final ready = photoPath.isNotEmpty && File(photoPath).existsSync();
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
                            'Assinatura facial • confirmação por foto',
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
                      'A câmera frontal registra a foto no momento da ficha. O Auditar vincula a imagem ao participante, data/hora e gera um código de comprovação da evidência.',
                      style: TextStyle(fontSize: 12.5, height: 1.35),
                    ),
                    const SizedBox(height: 8),
                    const Text(
                      'Esta função não faz reconhecimento automático de identidade. A confirmação é feita pelo registro presencial e conferência da foto.',
                      style: TextStyle(
                        fontSize: 11.5,
                        height: 1.35,
                        color: Colors.black54,
                      ),
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
            if (ready)
              ClipRRect(
                borderRadius: BorderRadius.circular(18),
                child: Image.file(
                  File(photoPath),
                  height: 310,
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
            if (qualityLabel.isNotEmpty) ...[
              const SizedBox(height: 7),
              Text(
                qualityLabel,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 11.5,
                  color: Colors.black54,
                ),
              ),
            ],
            const SizedBox(height: 12),
            FilledButton.tonalIcon(
              onPressed: busy || !consent ? null : _capture,
              icon: const Icon(Icons.camera_alt_outlined),
              label: Text(ready ? 'Refazer foto' : 'Abrir câmera frontal'),
            ),
            if (ready) ...[
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: busy ? null : _reset,
                icon: const Icon(Icons.delete_outline),
                label: const Text('Descartar e tirar outra'),
              ),
              const SizedBox(height: 10),
              Card(
                child: CheckboxListTile(
                  value: participantReviewed,
                  controlAffinity: ListTileControlAffinity.leading,
                  title: const Text(
                    'O participante conferiu a foto e confirma o uso desta imagem como comprovação desta ficha.',
                    style: TextStyle(fontSize: 12.5),
                  ),
                  onChanged: busy
                      ? null
                      : (value) => setState(
                            () => participantReviewed = value == true,
                          ),
                ),
              ),
            ],
            const SizedBox(height: 18),
            FilledButton.icon(
              onPressed: ready && participantReviewed && !busy ? _confirm : null,
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
              'A assinatura na tela continua disponível como alternativa.',
              style: TextStyle(fontSize: 11.5, color: Colors.black54),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
