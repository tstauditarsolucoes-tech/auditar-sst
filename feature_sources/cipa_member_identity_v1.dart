/// Rótulos dos integrantes da CIPA. Não concede permissões.
class CipaMemberIdentityLabel {
  const CipaMemberIdentityLabel._();

  static const validCipaRoles = <String>{
    'Presidente','Vice-presidente','Titular','Suplente','Secretário',
    'Membro designado',
  };
  static const validRepresentations = <String>{
    'Empregador','Empregados','Designado',
  };

  static String displayName({
    required String name,
    required String cipaRole,
  }) {
    final safeName = name.trim();
    final safeRole = validCipaRoles.contains(cipaRole.trim())
        ? cipaRole.trim()
        : '';
    if (safeName.isEmpty) return '';
    return safeRole.isEmpty ? safeName : '$safeName — $safeRole da CIPA';
  }

  /// Exibe cargo profissional somente quando confirmado no cadastro.
  /// O cargo da empresa é diferente da função na comissão.
  static String subtitle({
    required String representation,
    String jobTitle = '',
  }) {
    final r = representation.trim();
    final j = jobTitle.trim();
    final parts = <String>[
      if (j.isNotEmpty) 'Cargo na empresa: $j',
      if (validRepresentations.contains(r)) 'Representação: $r',
    ];
    return parts.join(' • ');
  }
}

/// O perfil individual precisa vir de uma sessão conferida NO SERVIDOR,
/// vinculada ao cadastro CIPA. Esta classe não faz login nem autorização.
class CipaMemberAccessProfile {
  const CipaMemberAccessProfile({
    required this.userId,
    required this.companyId,
    required this.mandateId,
    required this.memberId,
    required this.workerId,
    required this.fullName,
    required this.cipaRole,
    required this.representation,
    required this.jobTitle,
  });

  final String userId, companyId, mandateId, memberId, workerId;
  final String fullName, cipaRole, representation, jobTitle;

  String get displayName => CipaMemberIdentityLabel.displayName(
    name:fullName,cipaRole:cipaRole,
  );
  String get detailLine => CipaMemberIdentityLabel.subtitle(
    representation:representation,jobTitle:jobTitle,
  );
}

/// Contrato explícito para um futuro endpoint autenticado.
/// Membro e usuário devem pertencer à MESMA empresa, mandato e pessoa.
/// A sessão deve ser validada antes pelo servidor; passar qualquer texto
/// para esse método não equivale a autenticar ninguém.
class CipaMemberProfileContract {
  const CipaMemberProfileContract._();

  static CipaMemberAccessProfile? fromVerifiedMembership({
    required String authenticatedUserId,
    required String grantedCompanyId,
    required String grantedMandateId,
    required String grantedMemberId,
    required String membershipUserId,
    required String membershipCompanyId,
    required String membershipMandateId,
    required String membershipMemberId,
    required String membershipWorkerId,
    required String fullName,
    required String cipaRole,
    required String representation,
    String jobTitle = '',
    required bool userActive,
    required bool mandateActive,
    required bool memberActive,
  }) {
    final ids = <String>[
      authenticatedUserId,grantedCompanyId,grantedMandateId,
      grantedMemberId,membershipUserId,membershipCompanyId,
      membershipMandateId,membershipMemberId,membershipWorkerId,
    ];
    if (ids.any((id)=>id.trim().isEmpty) ||
        !userActive || !mandateActive || !memberActive ||
        authenticatedUserId!=membershipUserId ||
        grantedCompanyId!=membershipCompanyId ||
        grantedMandateId!=membershipMandateId ||
        grantedMemberId!=membershipMemberId ||
        fullName.trim().isEmpty ||
        !CipaMemberIdentityLabel.validCipaRoles.contains(cipaRole.trim()) ||
        !CipaMemberIdentityLabel.validRepresentations.contains(representation.trim())) {
      return null;
    }
    return CipaMemberAccessProfile(
      userId:authenticatedUserId,companyId:grantedCompanyId,
      mandateId:grantedMandateId,memberId:grantedMemberId,
      workerId:membershipWorkerId,fullName:fullName.trim(),
      cipaRole:cipaRole.trim(),representation:representation.trim(),
      jobTitle:jobTitle.trim(),
    );
  }
}
