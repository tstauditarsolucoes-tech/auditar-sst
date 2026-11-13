import 'dart:typed_data';
import 'package:image/image.dart' as img;

/// Uma foto de perfil NÃO é prova de identidade nem confirmação de presença.
/// Nunca salva original na galeria do aplicativo, apenas envia JPEG reduzido.
class CipaAvatarImage {
  const CipaAvatarImage._();
  static const int maxBytes=150000;
  static const int maxSourceBytes=8000000;
  static const int maxSize=320;

  static Uint8List prepare(Uint8List source) {
    if(source.isEmpty||source.length>maxSourceBytes)
      throw StateError('Escolha uma foto de até 8 MB.');
    final decoded=img.decodeImage(source);
    if(decoded==null)throw StateError('Imagem inválida. Escolha outra foto.');
    if(decoded.width<8||decoded.height<8||
       decoded.width>10000||decoded.height>10000)
      throw StateError('Dimensões da imagem não permitidas.');
    final oriented=img.bakeOrientation(decoded);
    // Corte central quadrado para caber no perfil, sem EXIF ou metadados.
    final side=oriented.width<oriented.height?
      oriented.width:oriented.height;
    final cropped=img.copyCrop(oriented,
      x:(oriented.width-side)~/2,y:(oriented.height-side)~/2,
      width:side,height:side);
    final clean=img.Image(width:side,height:side,numChannels:3);
    img.compositeImage(clean,cropped);
    final resized=side>maxSize?
      img.copyResize(clean,width:maxSize,height:maxSize):clean;
    // O resultado é menor, suficiente para avatar e nunca uma foto de vistoria.
    for(final quality in [75,65,55,45]){
      final jpeg=Uint8List.fromList(img.encodeJpg(resized,quality:quality));
      if(jpeg.length<=maxBytes&&jpeg.length>=8)return jpeg;
    }
    throw StateError('Não foi possível reduzir a foto. Escolha outra imagem.');
  }

  static bool validUpload(Uint8List bytes)=>
    bytes.length>=8&&bytes.length<=maxBytes&&
    bytes[0]==255&&bytes[1]==216&&bytes[2]==255&&
    bytes[bytes.length-2]==255&&bytes.last==217;
}
