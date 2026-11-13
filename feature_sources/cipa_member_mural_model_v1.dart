import 'dart:typed_data';
import 'package:image/image.dart' as image_codec;

/// Dados mínimos do mural. Fotos jamais são copiadas para o cache offline.
class CipaMuralComment {
  const CipaMuralComment({required this.id,required this.body,
    required this.authorLabel,required this.visibility});
  final String id,body,authorLabel,visibility;
}
class CipaMuralPost {
  const CipaMuralPost({required this.id,required this.place,
    required this.detail,required this.status,required this.visibility,
    required this.createdAt,required this.hasPhoto,required this.isMine,
    required this.comments,this.hasAfter=false,this.afterStatus=''});
  final String id,place,detail,status,visibility,createdAt;
  final bool hasPhoto,isMine,hasAfter;
  final String afterStatus;
  final List<CipaMuralComment> comments;
}
class CipaMuralCodec {
  const CipaMuralCodec._();
  static const int maxPhotoBytes=250000;
  static const int maxSourceBytes=8000000;
  static const int maxSide=960;

  static Uint8List preparePhoto(Uint8List original) {
    if(original.isEmpty||original.length>maxSourceBytes)
      throw StateError('Escolha uma foto de até 8 MB.');
    final decoded=image_codec.decodeImage(original);
    if(decoded==null||decoded.width<8||decoded.height<8||
       decoded.width>10000||decoded.height>10000)
      throw StateError('Não foi possível ler esta imagem.');
    final oriented=image_codec.bakeOrientation(decoded);
    final clean=image_codec.Image(
      width:oriented.width,height:oriented.height,numChannels:3);
    image_codec.compositeImage(clean,oriented);
    final resized=(clean.width>maxSide||clean.height>maxSide)?
      image_codec.copyResize(clean,
        width:clean.width>=clean.height?maxSide:null,
        height:clean.height>clean.width?maxSide:null):clean;
    for(final quality in [74,62,50,40,30]){
      final jpeg=Uint8List.fromList(
        image_codec.encodeJpg(resized,quality:quality));
      if(validPhoto(jpeg))return jpeg;
    }
    throw StateError('Foto muito grande, selecione uma imagem menor.');
  }

  static bool validPhoto(Uint8List data)=>
    data.length>=8&&data.length<=maxPhotoBytes&&
    data[0]==255&&data[1]==216&&data[2]==255&&
    data[data.length-2]==255&&data.last==217;

  static List<CipaMuralPost> parsePosts(dynamic rows){
    if(rows is! List)throw StateError('Mural indisponível.');
    final parsed=<CipaMuralPost>[];
    for(final data in rows.take(70)){
      if(data is! Map)continue;
      String value(String k)=>(data[k]??'').toString();
      final id=value('id');
      if(!RegExp(r'^[A-Za-z0-9_-]{16,120}$').hasMatch(id))continue;
      final cs=<CipaMuralComment>[];
      if(data['comments'] is List){
        for(final raw in (data['comments'] as List).take(15)){
          if(raw is! Map)continue;
          final name=(raw['authorLabel']??'').toString();
          cs.add(CipaMuralComment(
            id:(raw['id']??'').toString(),
            body:(raw['body']??'').toString(),
            authorLabel:name=='Equipe SST'?'Equipe SST':'Cipeiro',
            visibility:(raw['visibility']??'').toString()));
        }
      }
      parsed.add(CipaMuralPost(id:id,place:value('place'),
        detail:value('detail'),status:value('status'),
        visibility:value('visibility'),
        createdAt:value('createdAt'),
        hasPhoto:data['hasPhoto']==true,isMine:data['isMine']==true,
        hasAfter:data['hasAfter']==true,
        afterStatus:value('afterStatus'),
        comments:List.unmodifiable(cs)));
    }
    return List.unmodifiable(parsed);
  }
}
