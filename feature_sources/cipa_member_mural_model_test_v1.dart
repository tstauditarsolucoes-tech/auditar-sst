import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:image/image.dart' as image_codec;
import 'package:auditar_sst/services/cipa_member_mural_model.dart';

void main(){
  test('mural ignora ID inválido e não aceita dados imprevistos',(){
    expect(()=>CipaMuralCodec.parsePosts(null),throwsStateError);
    final valid=CipaMuralCodec.parsePosts([
      {'id':'mural-post-1234567890123456','place':'Produção',
       'detail':'Corredor com material na passagem','status':'Em análise',
       'visibility':'Aprovado','isMine':true,'hasPhoto':false,
       'comments':[{'id':'comment-1','body':'Analisar.',
         'visibility':'Aprovado','authorLabel':'Equipe SST'}]},
      {'id':'outro','place':'Fora','detail':'Nada'},
    ]);
    expect(valid.length,1);
    expect(valid.single.comments.single.authorLabel,'Equipe SST');
  });
  test('foto é recomprimida com tamanho limitado',(){
    final image=image_codec.Image(width:55,height:50);
    final original=Uint8List.fromList(image_codec.encodePng(image));
    final output=CipaMuralCodec.preparePhoto(original);
    expect(CipaMuralCodec.validPhoto(output),true);
    expect(output.length,lessThanOrEqualTo(250000));
    expect(()=>CipaMuralCodec.preparePhoto(Uint8List(0)),throwsStateError);
    expect(CipaMuralCodec.validPhoto(Uint8List.fromList([1,2,3])),false);
  });
}
