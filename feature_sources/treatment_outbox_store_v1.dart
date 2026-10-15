import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'treatment_outbox.dart';

const _storage = FlutterSecureStorage();
final treatmentOutbox = TreatmentOutbox(
  read: (key) => _storage.read(key:key),
  write: (key,value) => _storage.write(key:key,value:value),
);
