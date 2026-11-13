
import 'cipa_member_identity.dart';

/// Orientação educativa. Nunca confere cargo nem permissão automaticamente.
class CipaRoleGuide {
  const CipaRoleGuide._();
  static const roles=['Presidente','Vice-presidente','Titular','Suplente',
    'Secretário','Membro designado'];

  static String summary(String role) {
    switch(role) {
      case 'Presidente':return 'Convoca os membros, coordena as reuniões '
        'e encaminha as decisões à organização e ao SESMT, se houver. '
        'NR-5, item 5.3.4.';
      case 'Vice-presidente':return 'Substitui o presidente em impedimentos '
        'ou afastamentos temporários. Coordena e divulga as decisões com '
        'o presidente. NR-5, itens 5.3.5 e 5.3.6.';
      case 'Titular':return 'Participa das reuniões, apresenta sugestões '
        'e acompanha as medidas preventivas da CIPA.';
      case 'Suplente':return 'Colabora com as ações preventivas e substitui '
        'titular conforme o mandato e as regras aplicáveis.';
      case 'Secretário':return 'Ajuda a registrar os fatos da reunião. '
        'Os membros designam um secretário PARA CADA reunião, '
        'conforme o item 5.6.5. O nome no cadastro não substitui '
        'essa designação específica.';
      case 'Membro designado':return 'Representante nomeado pela organização '
        'nas hipóteses da NR-5, itens 5.4.13 e 5.4.14. '
        'Não se torna automaticamente presidente de uma CIPA.';
      default:return 'Confirme sua função com o responsável pelo cadastro.';
    }
  }
  static String hint(String role) {
    if(role=='Presidente')return 'A organização escolhe o presidente entre '
      'seus representantes da CIPA (5.4.5).';
    if(role=='Vice-presidente')return 'Representantes eleitos dos empregados '
      'escolhem o vice dentre seus titulares (5.4.5).';
    if(role=='Secretário')return 'A secretaria da reunião é definida '
      'pelos membros a cada encontro (5.6.5).';
    if(role=='Membro designado')return 'Confira se é representante '
      'nomeado da NR-5, e não titular/suplente de uma CIPA constituída.';
    return 'Confira a função e representação com o mandato oficial.';
  }
  static bool consistent(String role,String representation) {
    if(!roles.contains(role)||
       !CipaMemberIdentityLabel.validRepresentations.contains(representation))
      return false;
    if(role=='Presidente')return representation=='Empregador';
    if(role=='Vice-presidente')return representation=='Empregados';
    if(role=='Membro designado')return representation=='Designado';
    return representation!='Designado';
  }
  static List<String> firstSteps(String role) {
    switch(role){
      case 'Presidente':return const [
        'Confira calendário, data, horário e convoque os membros.',
        'Organize a pauta e as pendências com apoio da comissão.',
        'Abra a reunião e coordene a discussão das decisões.',
        'Confirme o secretário designado nesta reunião.',
        'Encaminhe as decisões à organização e ao SESMT, quando houver.'
      ];
      case 'Vice-presidente':return const [
        'Ajude a preparar a pauta e verificar ações anteriores.',
        'Substitua o presidente se estiver temporariamente impedido.',
        'Apoie a divulgação das decisões aos trabalhadores.'
      ];
      case 'Secretário':return const [
        'Confirme a designação de secretário desta reunião.',
        'Registre data, horário, local e presentes que realmente compareceram.',
        'Anote os assuntos e as decisões discutidos de verdade.',
        'Prepare a minuta para conferência e assinatura dos presentes.'
      ];
      case 'Membro designado':return const [
        'Confira sua nomeação e a orientação da organização.',
        'Observe problemas apenas onde possa circular com segurança.',
        'Converse com trabalhadores e acompanhe as medidas de prevenção.'
      ];
      case 'Suplente':return const [
        'Leia as convocações e informe sugestões à comissão.',
        'Colabore nas tarefas e vistorias seguras.',
        'Ao substituir titular, siga a composição formal do mandato.'
      ];
      case 'Titular':return const [
        'Leia a pauta e prepare sugestões dos trabalhadores.',
        'Participe das discussões e dos encaminhamentos da CIPA.',
        'Acompanhe medidas e peça apoio quando precisar.'
      ];
      default:return const ['Solicite conferência de sua função cadastrada.'];
    }
  }
}

/// Modelo educacional local. Não grava ata, presença, assinatura ou documento.
class CipaMinutesPractice {
  const CipaMinutesPractice({required this.date,required this.place,
    required this.agenda,required this.discussion,
    required this.decisions,this.secretary='',this.presentMembers='',
    this.responsibleAndDue='',this.meetingType='Ordinária'});
  final DateTime date;
  final String place,agenda,discussion,decisions,secretary,presentMembers,
    responsibleAndDue,meetingType;
  static String _clean(String value,{int max=600}){
    final clean=value.replaceAll(RegExp(r'[\r\n\t]+'),' ').trim();
    if(clean.length>max)throw ArgumentError('Texto acima do limite.');
    return clean;
  }
  String build(){
    if(!['Ordinária','Extraordinária'].contains(meetingType))
      throw ArgumentError('Tipo da reunião não reconhecido.');
    final local=_clean(place,max:120),pauta=_clean(agenda),
      relato=_clean(discussion),decisao=_clean(decisions),
      secretario=_clean(secretary,max:120),
      presentes=_clean(presentMembers),
      prazos=_clean(responsibleAndDue);
    if(local.length<2||pauta.length<4||relato.length<4||
       decisao.length<4)throw ArgumentError(
      'Preencha local, pauta, discussão e decisões que realmente ocorreram.');
    final dateText=date.day.toString().padLeft(2,'0')+'/'+
      date.month.toString().padLeft(2,'0')+'/'+date.year.toString();
    return [
      'RASCUNHO EDUCATIVO — NÃO É ATA OFICIAL',
      'Reunião '+meetingType+' da CIPA — '+dateText,
      'Local: '+local,
      'Secretário designado para esta reunião: '+
        (secretario.isEmpty?'[CONFERIR DESIGNACAO]':secretario),
      'Pessoas efetivamente presentes: '+
        (presentes.isEmpty?'[CONFERIR LISTA REAL]':presentes),
      'Pauta: '+pauta,
      'Assuntos realmente discutidos: '+relato,
      'Decisões e encaminhamentos: '+decisao,
      'Responsáveis e prazos: '+(prazos.isEmpty?'[COMPLETAR]':prazos),
      '',
      'CONFERÊNCIA: verificar fatos, lista real, assinatura dos presentes, '
      'disponibilização da ata aos membros e divulgação dos encaminhamentos '
      'aos empregados (NR-5, itens 5.6.3 a 5.6.3.2).',
      'Este texto não cria ata oficial, presença, assinatura ou publicação '
      'na Central; revise com os responsáveis.',
    ].join('\n');
  }
}
