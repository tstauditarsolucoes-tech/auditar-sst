import 'cipa_member_identity_v1.dart';

void check(bool valid,String message) {
  if (!valid) throw StateError(message);
}
void main() {
  check(CipaMemberIdentityLabel.displayName(name:'Maria Silva',
      cipaRole:'Vice-presidente')=='Maria Silva — Vice-presidente da CIPA',
      'Função da CIPA deve aparecer junto ao nome.');
  check(CipaMemberIdentityLabel.displayName(name:'José Lima',
      cipaRole:'Titular')=='José Lima — Titular da CIPA','Titular visível.');
  check(CipaMemberIdentityLabel.displayName(name:'Ana',
      cipaRole:'Membro designado')=='Ana — Membro designado da CIPA',
      'Designado visível.');
  check(CipaMemberIdentityLabel.displayName(name:'Ana',
      cipaRole:'Superadministrador')=='Ana',
      'Não exibir função da CIPA arbitrária.');
  check(CipaMemberIdentityLabel.subtitle(
      representation:'Empregados',jobTitle:'Auxiliar de Produção')==
      'Cargo na empresa: Auxiliar de Produção • Representação: Empregados',
      'Separar cargo profissional e representação da CIPA.');
  check(CipaMemberIdentityLabel.subtitle(
      representation:'Empregador')=='Representação: Empregador',
      'Não inventar cargo profissional.');
  CipaMemberAccessProfile? profile({
    String userId='user-A',String companyId='empresa-A',
    String mandateId='mandato-2026',String memberId='member-A',
    String membershipUserId='user-A',
    String membershipCompanyId='empresa-A',
    String membershipMandateId='mandato-2026',
    String membershipMemberId='member-A',
    bool userActive=true,bool mandateActive=true,bool memberActive=true,
  })=>CipaMemberProfileContract.fromVerifiedMembership(
    authenticatedUserId:userId,grantedCompanyId:companyId,
    grantedMandateId:mandateId,grantedMemberId:memberId,
    membershipUserId:membershipUserId,
    membershipCompanyId:membershipCompanyId,
    membershipMandateId:membershipMandateId,
    membershipMemberId:membershipMemberId,
    membershipWorkerId:'worker-A',fullName:'Maria Silva',
    cipaRole:'Presidente',representation:'Empregador',
    jobTitle:'Encarregada',userActive:userActive,
    mandateActive:mandateActive,memberActive:memberActive,
  );
  check(profile()!=null,'Perfil autenticado e compatível aceito.');
  check(profile()!.displayName=='Maria Silva — Presidente da CIPA',
      'Cabeçalho individual deve exibir função.');
  check(profile()!.detailLine.contains('Encarregada'),
      'Cabeçalho mostra cargo profissional quando informado.');
  check(profile(membershipCompanyId:'empresa-B')==null,
      'Rejeitar dados de outra empresa.');
  check(profile(membershipMandateId:'mandato-2025')==null,
      'Rejeitar mandato diferente.');
  check(profile(membershipMemberId:'member-B')==null,
      'Rejeitar cadastro de outro integrante.');
  check(profile(membershipUserId:'user-B')==null,
      'Rejeitar usuário que não pertence ao cadastro.');
  check(profile(userActive:false)==null,'Revogação de conta.');
  check(profile(mandateActive:false)==null,'Mandato encerrado.');
  check(profile(memberActive:false)==null,'Membro substituído.');
  check(profile(memberId:'')==null,'Exigir vínculo imutável.');
  print('CIPA_MEMBER_ROLE_NAME_AND_PROFILE_CONTRACT_OK');
}
