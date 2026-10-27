import 'package:flutter/material.dart';
import '../database.dart';
import '../services/auth_service.dart';
import '../services/offline_knowledge_cloud_service.dart';

/// Manual validation of the independent knowledge queue and cloud cache.
class OfflineKnowledgeStatusScreen extends StatefulWidget {
  const OfflineKnowledgeStatusScreen({super.key});
  @override
  State<OfflineKnowledgeStatusScreen> createState()=>_OfflineKnowledgeStatusScreenState();
}
class _OfflineKnowledgeStatusScreenState extends State<OfflineKnowledgeStatusScreen> {
  bool busy=false,hasCentral=false;
  String? error;
  Future<OfflineKnowledgeStatus>? statusFuture;
  @override
  void initState(){
    super.initState();
    _refreshStatus();
  }
  Future<void> _refreshStatus() async {
    try{
      final endpoint=await AppDatabase.instance.getSetting('management_panel_endpoint');
      if(mounted)setState((){
        hasCentral=endpoint.trim().startsWith('https://');
        statusFuture=OfflineKnowledgeCloudService.status();
      });
    }catch(_){
      if(mounted)setState(()=>statusFuture=OfflineKnowledgeCloudService.status());
    }
  }
  Future<void> _syncNow() async {
    if(busy)return;
    setState((){busy=true;error=null;});
    try{
      await OfflineKnowledgeCloudService.sync();
    }catch(_){
      if(mounted)setState(()=>error=
        'Não foi possível atualizar os modelos. Confirme a conexão e a implantação do módulo na Central. A fila local permanece salva.');
    }finally{
      if(mounted){
        setState(()=>busy=false);
        await _refreshStatus();
      }
    }
  }
  @override
  Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Biblioteca técnica online')),
    body:Align(alignment:Alignment.topCenter,
      child:ConstrainedBox(constraints:const BoxConstraints(maxWidth:680),
      child:FutureBuilder<OfflineKnowledgeStatus>(
        future:statusFuture,
        builder:(context,snapshot){
          final v=snapshot.data;
          return ListView(padding:const EdgeInsets.all(16),children:[
            Text('Aprendizado do Auditar',
              style:Theme.of(context).textTheme.titleLarge),
            const SizedBox(height:8),
            const Text('Modelos aprovados são gravados primeiro no aparelho. '
              'O envio para a Central é independente da sincronização das vistorias.'),
            const SizedBox(height:16),
            Card(child:Padding(padding:const EdgeInsets.all(14),
              child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
                Text('Pendentes de envio: '+(v?.pending.toString()??'...')),
                const SizedBox(height:6),
                Text('Modelos recebidos no cache: '+(v?.cached.toString()??'...')),
                const SizedBox(height:6),
                Text('Última atualização confirmada: '+(
                  v?.lastSuccess.isNotEmpty==true?v!.lastSuccess:'Ainda não confirmada')),
              ]))),
            const SizedBox(height:12),
            if(!AuthService.isSignedIn)
              const Text('Entre com uma conta interna da Auditar para compartilhar modelos.'),
            if(!hasCentral)
              const Text('Central não configurada neste aparelho. Aprendizado local preservado.'),
            if(error!=null)
              Text(error!,style:TextStyle(color:Theme.of(context).colorScheme.error)),
            const SizedBox(height:14),
            FilledButton.icon(onPressed:busy||!hasCentral||!AuthService.isSignedIn
                ?null:_syncNow,
              icon:const Icon(Icons.cloud_sync_outlined),
              label:Text(busy?'Atualizando...':'Enviar pendentes e atualizar biblioteca')),
            const SizedBox(height:12),
            const Text('Sem internet ou sem o módulo implantado, os modelos continuam locais. '
              'Não apague os dados do app antes de confirmar um envio bem-sucedido.'),
          ]);
        },
      ))),
  );
}
