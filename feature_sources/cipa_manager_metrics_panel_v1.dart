import 'package:flutter/material.dart';

/// Gráficos de consulta gerencial. Respeita escopo confirmado no servidor.
/// Não exibe detalhes, nomes de membros, fotos ou dados de outras empresas.
class CipaManagerMetricsPanel extends StatelessWidget {
  const CipaManagerMetricsPanel({
    super.key,required this.companyId,required this.mandateId,
    required this.serverData,
  });
  final String companyId,mandateId;
  final Map<String,dynamic>? serverData;

  Map<String,int>? _counts() {
    final raw=serverData;
    if(raw==null||raw['ok']!=true)return null;
    final scope=raw['scope'],values=raw['metrics'];
    if(scope is! Map||values is! Map||
      scope['companyId']!=companyId||
      scope['mandateId']!=mandateId)return null;
    const keys=[
      'membersActive','membersParticipating','inspectionsScheduled',
      'inspectionsSubmitted','inspectionsOverdue','meetingsScheduled',
      'meetingsRecorded','correctiveActionsOverdue',
      'observationsPendingReview','observationsReplied',
    ];
    final counts=<String,int>{};
    for(final key in keys){
      final value=values[key];
      if(value is! int||value<0)return null;
      counts[key]=value;
    }
    if(counts['membersParticipating']!>counts['membersActive']!||
       counts['inspectionsSubmitted']!>counts['inspectionsScheduled']!)
      return null;
    return counts;
  }

  Widget _progress(String title,int done,int total) {
    final ratio=total<=0?0.0:done/total;
    return SizedBox(width:300,child:Column(
      crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text(title,style:const TextStyle(fontWeight:FontWeight.w700)),
        const SizedBox(height:4),
        Text('$done de $total',
          style:const TextStyle(fontSize:13)),
        const SizedBox(height:8),
        LinearProgressIndicator(value:ratio,minHeight:10),
        const SizedBox(height:6),
      ],
    ));
  }
  Widget _metric(String title,int count) {
    return SizedBox(
      width:158,
      child:Card(
        child:Padding(
          padding:const EdgeInsets.all(12),
          child:Column(
            crossAxisAlignment:CrossAxisAlignment.start,
            children:[
              Text('$count',style:const TextStyle(
                fontSize:24,fontWeight:FontWeight.w800)),
              const SizedBox(height:4),
              Text(title,style:const TextStyle(fontSize:13)),
            ],
          ),
        ),
      ),
    );
  }

  @override Widget build(BuildContext context) {
    final c=_counts();
    return Card(child:Padding(
      padding:const EdgeInsets.all(14),
      child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text('Indicadores gerenciais da CIPA',
          style:Theme.of(context).textTheme.titleMedium),
        const SizedBox(height:8),
        if(c==null)
          const Text('Indicadores não disponíveis nesta consulta. '
            'Verifique a autorização e a conexão da Central.')
        else ...[
          const Text('Dados deste mandato, confirmados pelo servidor. '
            'A participação considera integrantes com ao menos um relato.',
            style:TextStyle(fontSize:13)),
          const SizedBox(height:12),
          Wrap(spacing:20,runSpacing:12,children:[
            _progress('Participação dos integrantes',
              c['membersParticipating']!,c['membersActive']!),
            _progress('Vistorias programadas com registro',
              c['inspectionsSubmitted']!,c['inspectionsScheduled']!),
          ]),
          Wrap(spacing:4,runSpacing:4,children:[
            _metric('Relatos aguardando orientação',
              c['observationsPendingReview']!),
            _metric('Orientações enviadas',
              c['observationsReplied']!),
            _metric('Reuniões agendadas',c['meetingsScheduled']!),
            _metric('Reuniões registradas',c['meetingsRecorded']!),
            _metric('Vistorias com prazo vencido',c['inspectionsOverdue']!),
            _metric('Ações com prazo vencido',
              c['correctiveActionsOverdue']!),
          ]),
          const SizedBox(height:8),
          const Text('Um relato não comprova correção do risco ou '
            'encerramento de ação. Contagens não substituem a gestão da NR-05.',
            style:TextStyle(fontSize:12)),
        ],
      ]),
    ));
  }
}
