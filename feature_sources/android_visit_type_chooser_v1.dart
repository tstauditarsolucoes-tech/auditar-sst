import 'package:flutter/material.dart';
import '../models.dart';
import 'new_inspection_screen.dart';
import 'express_round_screen.dart';
import 'quick_visit_screen.dart';
import 'field_quick_screen.dart';
import 'smart_visit_briefing_screen.dart';

/// Apenas um ponto de entrada. Os três formulários originais não são alterados.
class AuditarVisitTypeChooserScreen extends StatelessWidget {
  const AuditarVisitTypeChooserScreen({super.key,this.initialCompany});
  final Company? initialCompany;

  Future<void> _launch(BuildContext context,Widget page) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder:(_)=>page));
    // Volta ao painel de origem após sair do formulário, permitindo
    // que a tela inicial recalcule seus indicadores.
    if(context.mounted) Navigator.of(context).pop();
  }

  Widget _option(BuildContext context,{required IconData icon,
    required String title,required String subtitle,
    required VoidCallback onTap}) => Card(
    margin:const EdgeInsets.only(bottom:12),
    child:ListTile(
      contentPadding:const EdgeInsets.symmetric(horizontal:16,vertical:14),
      leading:Icon(icon,size:32,color:Theme.of(context).colorScheme.primary),
      title:Text(title,style:const TextStyle(fontWeight:FontWeight.w800)),
      subtitle:Text(subtitle),
      trailing:const Icon(Icons.chevron_right_rounded),
      onTap:onTap,
    ),
  );

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar:AppBar(title:const Text('Iniciar vistoria')),
    body:SafeArea(child:ListView(
      padding:const EdgeInsets.all(16),
      children:[
        const Text('Escolha o tipo de vistoria',
          style:TextStyle(fontSize:22,fontWeight:FontWeight.w800)),
        const SizedBox(height:8),
        const Text('Os registros, relatórios e formulários atuais serão mantidos.'),
        const SizedBox(height:18),
        if(initialCompany!=null) _option(context,
          icon:Icons.route_outlined,
          title:'Preparar Visita Inteligente',
          subtitle:'Conferir registros anteriores desta empresa antes '
            'de começar. Somente dados salvos neste aparelho.',
          onTap:()=>Navigator.of(context).push(
            MaterialPageRoute(builder:(_)=>
              SmartVisitBriefingScreen(company:initialCompany!)))),
        const SizedBox(height:8),
        _option(context,
          icon:Icons.fact_check_outlined,
          title:'Checklist completo',
          subtitle:'Vistoria com um ou vários checklists.',
          onTap:()=>_launch(context,
            NewInspectionScreen(initialCompany:initialCompany,
              fieldMode:initialCompany!=null))),
        _option(context,
          icon:Icons.add_a_photo_outlined,
          title:'Ronda Expressa',
          subtitle:'Fotos, descrição e análise técnica em campo.',
          onTap:()=>_launch(context,
            initialCompany==null
              ? const QuickVisitScreen(onlyRound:true)
              : ExpressRoundScreen(company:initialCompany!))),
        _option(context,
          icon:Icons.bolt_outlined,
          title:'Vistoria rápida / avulsa',
          subtitle:'Mantém o modo rápido existente.',
          onTap:()=>_launch(context,const FieldQuickScreen())),
      ],
    )),
  );
}
