import '../services/auth_service.dart';

/// Client accounts never gain operational access to the Auditar app.
/// Administrative capabilities require the authenticated Auditar admin.
enum AuditarAdminCapability {
  manageUsers,
  manageClientAccounts,
  manageCompanyAccess,
  manageTemplates,
  reviewAuditTrail,
  manageManagementPanel,
  manageAdministrativeSettings,
}

class AuditarAdminAccess {
  const AuditarAdminAccess._();

  static bool isAdmin(AuditarUser? user) =>
      user != null && user.active && user.role.toLowerCase() == 'admin';

  static bool can(
    AuditarUser? user,
    AuditarAdminCapability capability,
  ) =>
      isAdmin(user);

  static bool canOperate(AuditarUser? user) =>
      user != null &&
      user.active &&
      (user.role.toLowerCase() == 'admin' ||
          user.role.toLowerCase() == 'tecnico');

  static bool canAccessCompany(AuditarUser? user, String companyId) {
    if (!canOperate(user)) return false;
    if (isAdmin(user)) return true;
    return companyId.isNotEmpty &&
        (user!.allCompanies || user.companyIds.contains(companyId));
  }
}
