import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import '../lib/services/sst_document_signature_models.dart';

const png = 'iVBORw0KGgoAAAANSUhEUgAAAGQAAAAtCAIAAADX11mnAAABmklEQVR4nO2awRKCMAxErf//z3hwZJxCt9kkW8TJO3hwsAnPDVORtm3bo7DxvLqBO1GyCEoWQckiKFkEJYugZBHcXlZrbX9VkyNr73VN013dZb5afAd/7HLBr4KRGmlpyRiqv2SwvrR0VNaoOVHTrbXpyjpfIVm4rfSmTxfcPkhLv8kcQ13To0B9l1vgyy+r62bvNb1pEKjjm7mlO5yycB9ZTVsCJSp9Ss4YTr9kB/ZA4dKJvjyyRgPY8f0+1bEjUPjILF+0LKqww5c7UKC0vTomOobUOUy3GsFAZX1wBCfLOIDgGGoT6wgUqB4PFyHLYer0yG6d9ECBdYK+rLKCZUa+RIECRE7Eec1ynMzRlzRQuLRvHZMs9wB24A9KA5Xiay4rdxNs2ZSJiPuixzB+Vt0K0kDh0qyviaysAezYBa1/0iLiC8lS3/C86pkUty9iDP/peRufr6Es0QD+Dg5fQ1krr7tXwfqajOFVl+FlgBvTR+bXrD829cYeiNv/fZ+CMRAli6BkEZQsgpJFULIIShZBySIoWQQli+AFeGQCTZnCS3cAAAAASUVORK5CYII=';

SstHandwrittenMark mark(String snapshot, {String role = 'author'}) =>
    SstHandwrittenMark(
      roleCode: role, roleLabel: 'Elaborador - ciência',
      declaredName: 'Pessoa de Teste', declaredFunction: 'TST',
      signedAt: '2026-11-25T21:00:00Z',
      documentSnapshot: snapshot, pngBase64: png,
    );

void main() {
  test('rubrica não certificada é vinculada à versão do formulário', () {
    final a = mark('{"atividade":"A","status":"rascunho"}');
    expect(a.isCurrent('{"atividade":"A","status":"rascunho"}'), isTrue);
    expect(a.isCurrent('{"atividade":"B","status":"rascunho"}'), isFalse);
  });

  test('metadados da assinatura e PNG sobrevivem ao JSON', () {
    final restored = SstHandwrittenMark.fromJson(mark('versao-1').toJson());
    expect(restored.declaredName, 'Pessoa de Teste');
    expect(restored.roleCode, 'author');
    expect(base64Decode(restored.pngBase64).length, greaterThan(100));
  });

  test('PNG inválido ou imagem vazia são rejeitados', () {
    final json = mark('versao-1').toJson();
    json['pngBase64'] = base64Encode(utf8.encode('arquivo falso'));
    expect(() => SstHandwrittenMark.fromJson(json), throwsFormatException);
  });

  test('assinaturas isoladas por usuário empresa tipo e id', () {
    expect(SstHandwrittenSignatureStore.key('u1','e1','apr','d1'),
      isNot(SstHandwrittenSignatureStore.key('u2','e1','apr','d1')));
    expect(SstHandwrittenSignatureStore.key('u1','e1','apr','d1'),
      isNot(SstHandwrittenSignatureStore.key('u1','e2','apr','d1')));
    expect(SstHandwrittenSignatureStore.key('u1','e1','apr','d1'),
      isNot(SstHandwrittenSignatureStore.key('u1','e1','pet','d1')));
    expect(SstHandwrittenSignatureStore.key('u1','e1','apr','d1'),
      isNot(SstHandwrittenSignatureStore.key('u1','e1','apr','d2')));
  });

  test('salvar não mistura empresas nem documentos; versão alterada excluída', () async {
    final settings = <String,String>{};
    final store = SstHandwrittenSignatureStore(
      read: (k) async => settings[k] ?? '',
      write: (k,v) async { settings[k] = v; },
    );
    await store.save(
      user: 'u1', company: 'e1', kind: 'risk_apr', id: 'doc-1',
      allowedRoles: {'author','reviewer'}, mark: mark('estado-1'),
    );
    expect((await store.validForDocument(
      user: 'u1', company: 'e1', kind: 'risk_apr', id: 'doc-1',
      snapshot: 'estado-1')).length, 1);
    expect(await store.validForDocument(
      user: 'u1', company: 'e1', kind: 'risk_apr', id: 'doc-1',
      snapshot: 'estado-2'), isEmpty);
    expect(await store.load(
      user: 'u2', company: 'e1', kind: 'risk_apr', id: 'doc-1'), isEmpty);
    expect(await store.load(
      user: 'u1', company: 'e2', kind: 'risk_apr', id: 'doc-1'), isEmpty);
    expect(await store.load(
      user: 'u1', company: 'e1', kind: 'risk_pt', id: 'doc-1'), isEmpty);
  });

  test('função não permitida é rejeitada', () async {
    final store = SstHandwrittenSignatureStore(
      read: (_) async => '',
      write: (_,__) async {},
    );
    await expectLater(store.save(
      user: 'u1', company: 'e1', kind: 'pet_nr33', id: 'doc-1',
      allowedRoles: {'supervisor_ack','attendant_ack'},
      mark: mark('versao', role: 'author'),
    ), throwsStateError);
  });

  test('nova rubrica da mesma função substitui só a anterior', () async {
    final settings = <String,String>{};
    final store = SstHandwrittenSignatureStore(
      read: (k) async => settings[k] ?? '',
      write: (k,v) async { settings[k] = v; },
    );
    for (final m in [mark('v1'), mark('v1',role:'reviewer'),mark('v2')]) {
      await store.save(
        user: 'u1', company: 'e1', kind: 'risk_ar', id: 'doc-1',
        allowedRoles: {'author','reviewer'}, mark: m);
    }
    final all = await store.load(
      user:'u1',company:'e1',kind:'risk_ar',id:'doc-1');
    expect(all.length, 2);
    expect(all.firstWhere((e) => e.roleCode=='author').documentSnapshot,
      'v2');
    expect(all.firstWhere((e) => e.roleCode=='reviewer').documentSnapshot,
      'v1');
  });
}
