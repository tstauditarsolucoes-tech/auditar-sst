import 'dart:convert';
import 'package:crypto/crypto.dart';
import 'sst_scope_key.dart';

/// Impressão da versão do documento, sem copiar os campos SST para o
/// registro de assinatura; não é certificação digital.
String sstDocumentFingerprint(Map<String, dynamic> fields) =>
    sha256.convert(utf8.encode(jsonEncode(fields))).toString();

/// Assinatura desenhada na tela: registro de ciência, NÃO assinatura digital
/// certificada, identidade verificada nem autorização de PT ou PET.
class SstHandwrittenMark {
  const SstHandwrittenMark({
    required this.roleCode,
    required this.roleLabel,
    required this.declaredName,
    required this.declaredFunction,
    required this.signedAt,
    required this.documentSnapshot,
    required this.pngBase64,
  });
  final String roleCode, roleLabel, declaredName, declaredFunction;
  final String signedAt, documentSnapshot, pngBase64;

  bool isCurrent(String snapshot) => documentSnapshot == snapshot;

  Map<String, dynamic> toJson() => {
    'roleCode': roleCode,
    'roleLabel': roleLabel,
    'declaredName': declaredName,
    'declaredFunction': declaredFunction,
    'signedAt': signedAt,
    'documentSnapshot': documentSnapshot,
    'pngBase64': pngBase64,
  };

  factory SstHandwrittenMark.fromJson(Map<String, dynamic> json) {
    String field(String key, int max) {
      final v = json[key];
      if (v is! String || v.length > max) {
        throw const FormatException('Assinatura com campo inválido');
      }
      return v.trim();
    }
    final item = SstHandwrittenMark(
      roleCode: field('roleCode', 60),
      roleLabel: field('roleLabel', 120),
      declaredName: field('declaredName', 160),
      declaredFunction: field('declaredFunction', 160),
      signedAt: field('signedAt', 80),
      documentSnapshot: field('documentSnapshot', 64),
      pngBase64: field('pngBase64', 230000),
    );
    if (!RegExp(r'^[a-z][a-z0-9_]{2,60}$').hasMatch(item.roleCode) ||
        item.declaredName.isEmpty || item.declaredFunction.isEmpty ||
        item.signedAt.isEmpty ||
        !RegExp(r'^[a-f0-9]{64}$').hasMatch(item.documentSnapshot) ||
        item.pngBase64.isEmpty ||
        !RegExp(r'^[A-Za-z0-9+/]+={0,2}$').hasMatch(item.pngBase64)) {
      throw const FormatException('Assinatura incompleta ou inválida');
    }
    final raw = base64Decode(item.pngBase64);
    if (raw.length < 100 || raw.length > 170000 ||
        raw.length < 8 || raw[0] != 137 || raw[1] != 80 ||
        raw[2] != 78 || raw[3] != 71) {
      throw const FormatException('Imagem de assinatura inválida');
    }
    return item;
  }
}

/// Armazena separado do formulário e vincula cada rubrica à versão EXATA
/// do conteúdo antes da assinatura. Se qualquer campo mudar, ela caduca.
class SstHandwrittenSignatureStore {
  const SstHandwrittenSignatureStore({
    required this.read,
    required this.write,
  });
  final Future<String> Function(String) read;
  final Future<void> Function(String, String) write;

  static String key(String user, String company, String kind, String id) =>
      sstScopedKey('sst_hand_sign_v2', [user, company, kind, id]);

  Future<List<SstHandwrittenMark>> load({
    required String user,
    required String company,
    required String kind,
    required String id,
  }) async {
    final raw = await read(key(user, company, kind, id));
    if (raw.isEmpty) return const [];
    final decoded = jsonDecode(raw);
    if (decoded is! Map ||
        decoded['version'] != 1 ||
        decoded['user'] != user ||
        decoded['company'] != company ||
        decoded['kind'] != kind ||
        decoded['id'] != id || decoded['marks'] is! List) {
      throw const FormatException('Assinaturas de outro documento');
    }
    final rows = decoded['marks'] as List;
    if (rows.length > 6) throw const FormatException('Assinaturas excedidas');
    final list = <SstHandwrittenMark>[];
    final seen = <String>{};
    for (final row in rows) {
      if (row is! Map) throw const FormatException('Assinatura inválida');
      final mark = SstHandwrittenMark.fromJson(
          Map<String, dynamic>.from(row));
      if (!seen.add(mark.roleCode)) {
        throw const FormatException('Papel de assinatura repetido');
      }
      list.add(mark);
    }
    return List.unmodifiable(list);
  }

  Future<void> save({
    required String user,
    required String company,
    required String kind,
    required String id,
    required SstHandwrittenMark mark,
    required Set<String> allowedRoles,
  }) async {
    if (!allowedRoles.contains(mark.roleCode) ||
        allowedRoles.length > 6 || allowedRoles.isEmpty) {
      throw StateError('Função sem permissão para assinatura');
    }
    // Validar PNG e metadados antes da escrita.
    final clean = SstHandwrittenMark.fromJson(mark.toJson());
    final existing = await load(
      user: user, company: company, kind: kind, id: id);
    final next = [
      ...existing.where((m) => m.roleCode != clean.roleCode),
      clean,
    ];
    if (next.length > 6) throw StateError('Número de assinaturas excedido');
    await write(key(user, company, kind, id), jsonEncode({
      'version': 1,
      'user': user,
      'company': company,
      'kind': kind,
      'id': id,
      'marks': next.map((m) => m.toJson()).toList(),
    }));
  }

  Future<List<SstHandwrittenMark>> validForDocument({
    required String user,
    required String company,
    required String kind,
    required String id,
    required String snapshot,
  }) async => (await load(
    user: user, company: company, kind: kind, id: id,
  )).where((mark) => mark.isCurrent(snapshot)).toList(growable: false);
}
