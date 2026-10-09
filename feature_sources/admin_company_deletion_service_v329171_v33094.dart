import '../database.dart';
import 'auth_service.dart';

/// Exclusão destrutiva de empresa reservada exclusivamente à conta ADM.
///
/// A autorização é conferida aqui novamente, além da proteção visual da tela.
/// O motor de sincronização não é alterado; as exclusões locais continuam
/// usando os tombstones já existentes do DeviceSyncService.
class AdminCompanyDeletionService {
  const AdminCompanyDeletionService._();

  static bool get isAllowed => AuthService.isAdmin;

  static Future<int> deletePermanently(String companyId) async {
    if (!AuthService.isAdmin) {
      throw StateError(
        'A exclusão definitiva de empresa é exclusiva da conta administradora.',
      );
    }

    final id = companyId.trim();
    if (id.isEmpty) {
      throw ArgumentError.value(companyId, 'companyId', 'Empresa inválida.');
    }

    return AppDatabase.instance.deleteCompanyPermanentlyAdmin(id);
  }
}
