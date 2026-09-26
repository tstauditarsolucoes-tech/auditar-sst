import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:path/path.dart' as p;
import 'package:auditar_sst/services/express_round_draft_storage.dart';

void main() {
  late Directory temp;

  setUp(() async {
    temp = await Directory.systemTemp.createTemp('auditar_draft_');
  });

  tearDown(() async {
    if (await temp.exists()) await temp.delete(recursive: true);
  });

  test('round draft is isolated per company and round', () async {
    await ExpressRoundDraftStorage.save(
      'companyA', 'round1', {'entryId': 'one', 'description': 'Foto no forno'},
      root: temp,
    );
    expect(
      (await ExpressRoundDraftStorage.load('companyA', 'round1', root: temp))
          ?['description'],
      'Foto no forno',
    );
    expect(await ExpressRoundDraftStorage.load('companyB', 'round1', root: temp),
        isNull);
    expect(await ExpressRoundDraftStorage.load('companyA', 'round2', root: temp),
        isNull);
  });

  test('saves newer snapshot without losing the entry identity', () async {
    await ExpressRoundDraftStorage.save(
      'companyA', 'round1', {'entryId': 'same-id', 'description': 'Primeira nota'},
      root: temp,
    );
    await ExpressRoundDraftStorage.save(
      'companyA', 'round1', {
        'entryId': 'same-id',
        'description': 'Nota revisada',
        'categories': ['EPI'],
      },
      root: temp,
    );
    final restored =
        await ExpressRoundDraftStorage.load('companyA', 'round1', root: temp);
    expect(restored?['entryId'], 'same-id');
    expect(restored?['description'], 'Nota revisada');
    expect(restored?['categories'], ['EPI']);
  });

  test('corrupt primary can recover a previous valid snapshot', () async {
    final primary = File(p.join(
        temp.path, 'auditar_round_drafts', 'companyA', 'round1.json'));
    await ExpressRoundDraftStorage.save(
      'companyA', 'round1', {'entryId': 'safe', 'description': 'Saved note'},
      root: temp,
    );
    await primary.copy(primary.path + '.bak');
    await primary.writeAsString('incomplete JSON', flush: true);
    final recovered =
        await ExpressRoundDraftStorage.load('companyA', 'round1', root: temp);
    expect(recovered?['entryId'], 'safe');
  });

  test('clear deletes primary and recovery snapshots', () async {
    await ExpressRoundDraftStorage.save(
      'companyA', 'round1', {'entryId': 'old'}, root: temp,
    );
    await ExpressRoundDraftStorage.clear('companyA', 'round1', root: temp);
    expect(await ExpressRoundDraftStorage.load('companyA', 'round1', root: temp),
        isNull);
  });

  test('draft cannot be read under a different declared company', () async {
    await ExpressRoundDraftStorage.save(
      'companyA', 'round1', {'entryId': 'separate'}, root: temp,
    );
    final a = File(p.join(
        temp.path, 'auditar_round_drafts', 'companyA', 'round1.json'));
    final b = File(p.join(
        temp.path, 'auditar_round_drafts', 'companyB', 'round1.json'));
    await b.parent.create(recursive: true);
    await a.copy(b.path);
    expect(await ExpressRoundDraftStorage.load('companyB', 'round1', root: temp),
        isNull);
  });
}
