#!/usr/bin/env python3
from pathlib import Path
import re,sys

if len(sys.argv)<2:
    raise SystemExit("uso: patch_worker_pdf_local_android_v32996.py <APP_DIR> [android|windows]")

root=Path(sys.argv[1])
platform=(sys.argv[2] if len(sys.argv)>2 else "android").lower()
p=root/"lib/services/worker_import_service.dart"
s=p.read_text(encoding="utf-8")

old="""    Uint8List uploadBytes = bytes;
    if ((Platform.isAndroid || Platform.isIOS) &&
        localPath != null &&
        localPath.trim().isNotEmpty) {
      try {
        final extracted = await ReadPdfText.getPDFtext(localPath)
            .timeout(const Duration(seconds: 20));
        final normalized = _normalizeExtractedRhText(extracted);
        if (normalized.length >= 80) {
          final localTable = _parseExtractedRhText(normalized);
          if (localTable != null) {
            return localTable;
          }
          uploadBytes = await _buildLightweightRhPdf(normalized);
        }
      } catch (_) {
        // PDF escaneado, protegido ou sem camada de texto: usa o original.
      }
    }
"""
new="""    Uint8List uploadBytes = bytes;
    File? temporaryPdf;
    String? extractionPath = localPath?.trim();

    // No Android, o FilePicker pode devolver apenas bytes/content URI e deixar
    // selected.path nulo. Antes essa situacao pulava toda a leitura local e
    // mandava o PDF direto para a internet. Gravamos uma copia temporaria para
    // garantir que o parser local seja sempre tentado primeiro.
    if (Platform.isAndroid || Platform.isIOS) {
      try {
        if (extractionPath == null ||
            extractionPath.isEmpty ||
            !await File(extractionPath).exists()) {
          final tempDir = await Directory.systemTemp.createTemp('auditar_rh_');
          temporaryPdf = File(
            '${tempDir.path}${Platform.pathSeparator}lista_rh.pdf',
          );
          await temporaryPdf.writeAsBytes(bytes, flush: true);
          extractionPath = temporaryPdf.path;
        }

        final extracted = await ReadPdfText.getPDFtext(extractionPath)
            .timeout(const Duration(seconds: 25));
        final normalized = _normalizeExtractedRhText(extracted);
        if (normalized.length >= 40) {
          final localTable = _parseExtractedRhText(normalized);
          if (localTable != null) {
            return localTable;
          }
          // Se a estrutura local nao foi reconhecida, envia apenas um PDF de
          // texto bem leve para a IA, nunca o arquivo original pesado.
          uploadBytes = await _buildLightweightRhPdf(normalized);
        }
      } catch (_) {
        // PDF escaneado/protegido: mantem o fallback existente da IA.
      } finally {
        try {
          final file = temporaryPdf;
          if (file != null && await file.exists()) {
            final parent = file.parent;
            await file.delete();
            if (await parent.exists()) {
              await parent.delete(recursive: true);
            }
          }
        } catch (_) {}
      }
    }
"""
if s.count(old)!=1:
    raise RuntimeError("bloco de leitura local do RH diferente do esperado")
s=s.replace(old,new,1)

# Reduz apenas o timeout do fallback do RH. Se a leitura local falhar, o app nao
# fica mais preso por 90 s. Nenhum transporte de sync/IA de foto e alterado.
old_timeout="""          .timeout(
            const Duration(seconds: 90),
            onTimeout: () {
              // Fecha o socket desta importacao sem afetar qualquer requisicao
              // de sincronizacao que esteja acontecendo em paralelo.
              client.close();
              throw const WorkerImportException(
                'A leitura do PDF passou de 90 segundos e foi cancelada. '
                'Nenhum trabalhador existente foi alterado. '
                'Tente novamente com internet estavel ou com um PDF mais leve.',
              );
            },
          );
"""
new_timeout="""          .timeout(
            const Duration(seconds: 35),
            onTimeout: () {
              // O cadastro local continua intacto; apenas o fallback online do
              // PDF e cancelado. A leitura local ja foi tentada antes.
              client.close();
              throw const WorkerImportException(
                'Nao foi possivel concluir a leitura complementar do PDF pela internet. '
                'Tente novamente ou use um PDF com texto pesquisavel. '
                'Nenhum trabalhador existente foi alterado.',
              );
            },
          );
"""
if s.count(old_timeout)!=1:
    raise RuntimeError("timeout antigo do RH nao localizado")
s=s.replace(old_timeout,new_timeout,1)

p.write_text(s,encoding="utf-8",newline="\n")

pubp=root/"pubspec.yaml"
pub=pubp.read_text(encoding="utf-8")
version="3.30.23+210" if platform=="windows" else "3.29.96+238"
pub,n=re.subn(r"(?m)^version:\s*[^\r\n]+$",f"version: {version}",pub,count=1)
if n!=1:
    raise RuntimeError("versao nao localizada")
pubp.write_text(pub,encoding="utf-8",newline="\n")

check=p.read_text(encoding="utf-8")
for marker in [
    "Directory.systemTemp.createTemp('auditar_rh_')",
    "await temporaryPdf.writeAsBytes(bytes, flush: true)",
    "ReadPdfText.getPDFtext(extractionPath)",
    "const Duration(seconds: 35)",
    "Nenhum trabalhador existente foi alterado",
]:
    assert marker in check, marker
assert "const Duration(seconds: 90)" not in check
assert f"version: {version}" in pubp.read_text(encoding="utf-8")
print("WORKER_PDF_LOCAL_ANDROID_OK",platform,version)
