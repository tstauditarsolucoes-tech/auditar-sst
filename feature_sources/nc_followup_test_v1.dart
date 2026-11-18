import 'nc_followup_v1.dart';

void check(bool value, String why) {
  if (!value) throw StateError('NC_FOLLOWUP: ' + why);
}

NcFollowupEvent event(String id, String cid, String nc, String uid,
    {NcFollowupKind kind = NcFollowupKind.persists,
    String note = 'Proteção continua ausente'}) => NcFollowupEvent(
  id: id, companyId: cid, ncId: nc, authorId: uid,
  at: '2026-11-18T12:00:00Z', kind: kind, note: note,
);

Future<void> main() async {
  final saved = <String, String>{};
  final ledger = NcFollowupLedger(
    read: (key) async => saved[key] ?? '',
    write: (key, value) async { saved[key] = value; },
  );
  final first = event('a1', 'empresa-A', 'NC-001', 'tst-1');
  final initial = await ledger.append(first);
  check(initial.length == 1, 'primeiro registro');
  final repeat = await ledger.append(first);
  check(repeat.length == 1, 'reenvio não duplica histórico');

  final reported = event('a2', 'empresa-A', 'NC-001', 'tst-1',
    kind: NcFollowupKind.correctionReported,
    note: 'A empresa informou instalação de proteção');
  final rows = await ledger.append(reported);
  check(rows.length == 2, 'mantém histórico da NC existente');
  check(rows.last.kind == NcFollowupKind.correctionReported,
      'correção é somente informada, não validada');

  final anotherNc = await ledger.list('empresa-A', 'NC-002', 'tst-1');
  final anotherCompany = await ledger.list('empresa-B', 'NC-001', 'tst-1');
  final anotherUser = await ledger.list('empresa-A', 'NC-001', 'tst-2');
  check(anotherNc.isEmpty && anotherCompany.isEmpty && anotherUser.isEmpty,
      'isolar por NC, empresa e usuário');

  var collision = false;
  try {
    await ledger.append(event('a1', 'empresa-A', 'NC-001', 'tst-1',
      note: 'Um texto diferente para o mesmo identificador'));
  } catch (_) { collision = true; }
  check(collision, 'rejeita reutilização de ID com outro conteúdo');

  var invalid = false;
  try {
    await ledger.append(event('a3', 'empresa-A', 'NC-001', 'tst-1',
      note: 'curto'));
  } catch (_) { invalid = true; }
  check(invalid, 'exige descrição factual mínima');

  final key = NcFollowupLedger.key('empresa-A', 'NC-001', 'tst-1');
  final before = saved[key]!;
  saved[key] = '{"version":1,"companyId":"empresa-B","ncId":"NC-001","events":[]}';
  var rejected = false;
  try { await ledger.list('empresa-A', 'NC-001', 'tst-1'); }
  catch (_) { rejected = true; }
  check(rejected, 'não mistura payload de outra empresa');
  saved[key] = before;

  final failingLedger = NcFollowupLedger(
    read: (k) async => saved[k] ?? '',
    write: (k, v) async => throw StateError('sem armazenamento'),
  );
  var failed = false;
  try {
    await failingLedger.append(event('a3','empresa-A','NC-001','tst-1'));
  } catch (_) { failed = true; }
  check(failed && (await ledger.list('empresa-A','NC-001','tst-1')).length == 2,
    'erro na gravação preserva histórico');
  print('NC_FOLLOWUP_TESTES_7_CENARIOS_OK');
}
