import 'package:flutter/material.dart';
import 'screens/cipa_member_portal_screen.dart';
import 'services/cipa_member_identity.dart';
import 'services/cipa_member_portal_policy.dart';

/// Somente DEMONSTRAÇÃO SEM REDE, COM DADOS INVENTADOS.
/// É compilada pelo entrypoint lib/demo_main.dart, jamais pelo lib/main.dart.
/// Sem login, token, API, sincronização, foto real ou envio de qualquer dado.
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MinhaCipaDemoApp());
}

CipaMemberView cipaDemoView() {
  const p = CipaMemberAccessProfile(
    userId: 'usuario-demo',
    companyId: 'empresa-ficticia',
    mandateId: 'mandato-ficticio',
    memberId: 'membro-ficticio',
    workerId: 'trabalhador-ficticio',
    fullName: 'Maria Exemplo',
    cipaRole: 'Titular',
    representation: 'Empregados',
    jobTitle: 'Auxiliar de Produção',
  );
  const empresa = 'empresa-ficticia';
  const mandato = 'mandato-ficticio';
  const membro = 'membro-ficticio';
  return CipaMemberPortalRules.build(
    verifiedProfile: p,
    companyLabel: 'Empresa Fictícia — DEMONSTRAÇÃO',
    mandateLabel: 'Mandato de exemplo 2026–2027',
    records: [
      CipaMemberItem(
        id: 'reuniao-demo', companyId: empresa, mandateId: mandato,
        type: CipaMemberItemType.meeting, title: 'Reunião ordinária de exemplo',
        description: 'Conferir pauta e apresentar as pendências identificadas.',
        status: 'Agendada', visibleToAllMembers: true,
        date: DateTime(2026, 12, 1),
      ),
      CipaMemberItem(
        id: 'acao-demo', companyId: empresa, mandateId: mandato,
        type: CipaMemberItemType.action,
        title: 'Acompanhar proteção da esteira',
        description: 'A equipe técnica ainda vai conferir a adequação.',
        assignedMemberId: membro, status: 'Em andamento',
        dueDate: DateTime(2026, 12, 5),
      ),
      const CipaMemberItem(
        id: 'aviso-demo', companyId: empresa, mandateId: mandato,
        type: CipaMemberItemType.notice, title: 'Orientação de segurança',
        description: 'Observe os riscos e comunique situações inseguras.',
        visibleToAllMembers: true,
      ),
      const CipaMemberItem(
        id: 'treinamento-demo', companyId: empresa, mandateId: mandato,
        type: CipaMemberItemType.training, title: 'Capacitação da CIPA',
        description: 'Exemplo de registro de capacitação na tela pessoal.',
        assignedMemberId: membro, status: 'Programado',
      ),
      const CipaMemberItem(
        id: 'observacao-demo', companyId: empresa, mandateId: mandato,
        type: CipaMemberItemType.observation, title: 'Piso molhado no corredor',
        description: 'Ocorrência fictícia enviada para avaliação técnica.',
        assignedMemberId: membro, status: 'Em análise',
      ),
      CipaMemberItem(
        id: 'vistoria-demo', companyId: empresa, mandateId: mandato,
        type: CipaMemberItemType.scheduledInspection,
        title: 'Vistoria orientada no setor Produção',
        description: 'Conferir EPIs e proteção de máquinas.',
        assignedMemberId: membro, status: 'Agendada',
        dueDate: DateTime(2026, 12, 2),
      ),
      const CipaMemberItem(
        id: 'lembrete-demo', companyId: empresa, mandateId: mandato,
        type: CipaMemberItemType.reminder,
        title: 'Verificar ações ainda pendentes',
        visibleToAllMembers: true,
      ),
    ],
  );
}

class MinhaCipaDemoApp extends StatelessWidget {
  const MinhaCipaDemoApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    title: 'Minha CIPA — Demonstração',
    theme: ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF17477D)),
    ),
    home: const MinhaCipaDemoStart(),
  );
}

class MinhaCipaDemoStart extends StatelessWidget {
  const MinhaCipaDemoStart({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Minha CIPA — DEMO')),
    body: SafeArea(child: Padding(
      padding: const EdgeInsets.all(20),
      child: Column(mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.stretch,children: [
        const Icon(Icons.health_and_safety_outlined,size:76),
        const SizedBox(height:16),
        Text('Conheça o Minha CIPA',textAlign:TextAlign.center,
          style:Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height:12),
        const Text(
          'Versão de demonstração, apenas para conhecer as telas. '
          'Empresa, membro, datas e ocorrências são inteiramente fictícios. '
          'Não há login, consulta à Central ou envio de informações.',
          textAlign: TextAlign.center,
        ),
        const SizedBox(height:20),
        FilledButton.icon(
          icon:const Icon(Icons.visibility_outlined),
          label:const Text('Explorar telas da CIPA'),
          onPressed:()=>Navigator.of(context).push(
            MaterialPageRoute<void>(builder:(_)=>Banner(
              location: BannerLocation.topEnd,
              message: 'DEMO',
              color: Colors.deepOrange,
              child: CipaMemberPortalScreen(
                companyName:'Empresa Fictícia — DEMO',
                mandateLabel:'2026–2027 (exemplo)',
                view:cipaDemoView(),
                sessionVerified:true,
              ),
            )),
          ),
        ),
        const SizedBox(height:12),
        const Text(
          'Ações de envio, encerramento e aprovação não estão habilitadas. '
          'Este APK não substitui o aplicativo oficial.',
          textAlign:TextAlign.center,style:TextStyle(fontSize:13)),
      ]),
    )),
  );
}
