import 'package:flutter/material.dart';
import '../database.dart';
import '../models.dart';
import '../services/visit_intelligence.dart';
import 'express_round_screen.dart';
import 'new_inspection_screen.dart';

/// Preparação de visita: consulta somente registros locais já salvos.
/// Não inicia sincronização, não muda NC e não substitui histórico completo.
class SmartVisitBriefingScreen extends StatefulWidget {
  const SmartVisitBriefingScreen({super.key,required this.company});
  final Company company;

  @override State<SmartVisitBriefingScreen> createState()=>
    _SmartVisitBriefingScreenState();
}

class _SmartVisitBriefingScreenState extends State<SmartVisitBriefingScreen> {
  late Future<VisitBriefing> _future;
  @override void initState(){super.initState();_refresh();}

  void _refresh() {
    _future=_load();
  }

  Future<VisitBriefing> _load() async {
    final records=await AppDatabase.instance.getSstRecords(
      type:'OBSERVACAO_SEGURANCA',
    ).timeout(const Duration(seconds:12));
    return VisitIntelligence.fromLocalRondas(
      companyId:widget.company.id,
      records:records.map((record)=><String,Object?>{
        'id':record.id,
        'companyId':record.companyId,
        'status':record.status,
        'payload':record.payload,
      }),
    );
  }

  void _reload()=>setState(_refresh);

  Future<void> _open(Widget screen) async {
    await Navigator.of(context).push(MaterialPageRoute(builder:(_)=>screen));
    if(mounted)_reload();
  }

  Widget _count(String label,int value) => Expanded(
    child:Card(child:Padding(
      padding:const EdgeInsets.symmetric(vertical:14,horizontal:8),
      child:Column(children:[
        Text(value.toString(),style:const TextStyle(
          fontWeight:FontWeight.w800,fontSize:26)),
        const SizedBox(height:5),
        Text(label,textAlign:TextAlign.center,
          style:const TextStyle(fontSize:12)),
      ]),
    )),
  );

  @override Widget build(BuildContext context) => Scaffold(
    appBar:AppBar(
      title:const Text('Visita Inteligente'),
      actions:[IconButton(
        tooltip:'Atualizar dados locais',
        icon:const Icon(Icons.refresh_outlined),
        onPressed:_reload,
      )],
    ),
    body:SafeArea(child:FutureBuilder<VisitBriefing>(
      future:_future,
      builder:(context,snapshot){
        if(snapshot.connectionState!=ConnectionState.done){
          return const Center(child:CircularProgressIndicator());
        }
        if(snapshot.hasError||!snapshot.hasData){
          return ListView(padding:const EdgeInsets.all(18),children:[
            const Icon(Icons.error_outline,size:44),
            const SizedBox(height:12),
            const Text('Não foi possível consultar os registros locais. '
              'Nenhum indicador será apresentado como atualizado. '
              'As vistorias já salvas não foram alteradas.',
              textAlign:TextAlign.center),
            const SizedBox(height:12),
            FilledButton.icon(
              onPressed:_reload,icon:const Icon(Icons.refresh),
              label:const Text('Tentar novamente')),
          ]);
        }
        final data=snapshot.data!;
        return ListView(padding:const EdgeInsets.all(16),children:[
          Text(widget.company.name,style:Theme.of(context)
            .textTheme.titleLarge),
          const SizedBox(height:7),
          const Text('Preparação com base nas Rondas Expressas salvas '
            'neste aparelho. Não inclui automaticamente checklists, '
            'arquivos na nuvem nem ações de outros módulos.',
            style:TextStyle(fontSize:12)),
          const SizedBox(height:16),
          Row(children:[
            _count('Rondas locais',data.savedRounds),
            _count('Observações abertas',data.openObservations),
            _count('Possíveis repetições',data.recurrenceCandidates),
          ]),
          const SizedBox(height:12),
          Text('O que conferir nesta visita?',
            style:Theme.of(context).textTheme.titleMedium),
          const SizedBox(height:8),
          if(data.items.isEmpty)
            const Card(child:Padding(
              padding:EdgeInsets.all(16),
              child:Text('Nenhuma observação aberta identificada nas '
                'Rondas Expressas disponíveis. Isso NÃO significa '
                'que a empresa esteja sem riscos.'),
            )),
          for(final item in data.items)
            Card(child:ListTile(
              leading:Icon(item.recurrenceCandidate?
                Icons.repeat_outlined:Icons.warning_amber_outlined),
              title:Text(item.sector),
              subtitle:Text(item.description),
              isThreeLine:item.description.length>70,
              trailing:item.recurrenceCandidate?
                const Tooltip(
                  message:'Possível repetição; confirme em campo.',
                  child:Icon(Icons.info_outline)):null,
            )),
          if(data.openObservations>data.items.length)
            Text('Exibindo até 5 observações de '
              'um total de registros abertos. Consulte o histórico '
              'para verificar todas.',
              style:const TextStyle(fontSize:12)),
          const SizedBox(height:12),
          const Text('Os possíveis casos recorrentes são sugestões '
            'baseadas em descrições semelhantes de rondas distintas. '
            'O TST deve verificar antes de classificar uma recorrência.',
            style:TextStyle(fontSize:12)),
          const SizedBox(height:16),
          FilledButton.icon(
            onPressed:()=>_open(ExpressRoundScreen(company:widget.company)),
            icon:const Icon(Icons.add_a_photo_outlined),
            label:const Text('Fazer nova ronda'),
          ),
          const SizedBox(height:10),
          OutlinedButton.icon(
            onPressed:()=>_open(NewInspectionScreen(
              initialCompany:widget.company,fieldMode:true)),
            icon:const Icon(Icons.fact_check_outlined),
            label:const Text('Fazer checklist completo'),
          ),
          const SizedBox(height:16),
          const Text('Diagnóstico local: consulta concluída neste aparelho. '
            'Este indicador não confirma envio à Central ou '
            'sincronização com outros dispositivos.',
            style:TextStyle(fontSize:12)),
        ]);
      },
    )),
  );
}
