import 'package:flutter_test/flutter_test.dart';
import 'package:auditar_sst/screens/evidence_backup_screen.dart';

void main() {
  test('never infer record backup solely from a global sync timestamp', () {
    expect(BackupStatusReader.recordState(
      trackingAvailable:false,dirty:null,hasSuccessfulSync:true),
      BackupRecordState.unverified);
    expect(BackupStatusReader.recordState(
      trackingAvailable:true,dirty:null,hasSuccessfulSync:true),
      BackupRecordState.unverified);
    expect(BackupStatusReader.recordState(
      trackingAvailable:true,dirty:true,hasSuccessfulSync:true),
      BackupRecordState.pending);
    expect(BackupStatusReader.recordState(
      trackingAvailable:true,dirty:false,hasSuccessfulSync:false),
      BackupRecordState.unverified);
    expect(BackupStatusReader.recordState(
      trackingAvailable:true,dirty:false,hasSuccessfulSync:true),
      BackupRecordState.confirmed);
  });

  test('photo backup is confirmed only for current catalog path and Drive ID', () {
    expect(BackupStatusReader.photoState(
      localExists:true,sameCatalogPath:true,hasDriveId:true),
      BackupPhotoState.confirmed);
    expect(BackupStatusReader.photoState(
      localExists:false,sameCatalogPath:true,hasDriveId:true),
      BackupPhotoState.recoverable);
    expect(BackupStatusReader.photoState(
      localExists:true,sameCatalogPath:false,hasDriveId:true),
      BackupPhotoState.pending);
    expect(BackupStatusReader.photoState(
      localExists:false,sameCatalogPath:false,hasDriveId:true),
      BackupPhotoState.unverified);
    expect(BackupStatusReader.photoState(
      localExists:true,sameCatalogPath:true,hasDriveId:false),
      BackupPhotoState.pending);
    expect(BackupStatusReader.photoState(
      localExists:false,sameCatalogPath:false,hasDriveId:false),
      BackupPhotoState.missing);
  });

  test('two photos must both be protected for a fully protected record', () {
    final a=BackupRecordItem(id:'r',category:'Ronda',title:'Exemplo',
      date:DateTime(2026,9,24),state:BackupRecordState.confirmed,
      photos:[
        BackupPhotoStateItem(1,'/one.jpg',BackupPhotoState.confirmed),
        BackupPhotoStateItem(2,'/two.jpg',BackupPhotoState.pending),
      ]);
    expect(a.isProtected,false);
    final b=BackupRecordItem(id:'r2',category:'Ronda',title:'Exemplo',
      date:DateTime(2026,9,24),state:BackupRecordState.confirmed,
      photos:[
        BackupPhotoStateItem(1,'/one.jpg',BackupPhotoState.confirmed),
        BackupPhotoStateItem(2,'/two.jpg',BackupPhotoState.recoverable),
      ]);
    expect(b.isProtected,true);
    final snapshot=BackupCompanySnapshot([a,b],'','');
    expect(snapshot.confirmed,1);
    expect(snapshot.photoCount,4);
    expect(snapshot.backedPhotos,3);
    expect(snapshot.pendingPhotos,1);
  });
}
