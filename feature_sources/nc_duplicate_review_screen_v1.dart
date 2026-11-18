import 'package:flutter/material.dart';

import '../database.dart';
import '../models.dart';
import '../services/auth_service.dart';
import '../services/nc_duplicate_advisor.dart';
import 'express_round_screen.dart';
import 'nc_followup_screen.dart';

/// Pré-conferência guiada e opcional ANTES de uma nova Ronda Expressa.
/// Só compara NCs locais da empresa autorizada. Não edita registros oficiais.
class NcDuplicateReviewScreen extends StatefulWidget {
  const NcDuplicateReviewScreen({super.key, required this.company});
  final Company company;
  @override State<NcDuplicateReviewScreen> createState() =>
      _NcDuplicateReviewState();
}

class _NcDuplicateReviewState extends State<NcDuplicateReviewScreen> {
  late Future<List<Map<String, dynamic>>> _future;
  String _sector='', _description='';
  bool _searched=false;
  List<NcSimilarityCandidate> _matches=const [];

  @override void initState() {
    super.initState();
    _future=_load();
  }

  bool get _allowed => AuthService.canAccessCompany(widget.company.id);

  Future<List<Map<String, dynamic>>> _load() async {
    if(!_allowed)throw StateError('Acesso à empresa não autorizado');
    final rows=await AppDatabase.instance.getNonConformityRows(
      includeClosed:false).timeout(const Duration(seconds:12));
    final result=<Map<String,dynamic>>[];
    for(final raw in rows){
      final row=Map<String,dynamic>.from(raw);
      if(NcDuplicateAdvisor.first(
        row,['company_id','companyId','empresa_id'])==widget.company.id){
        result.add(row);
      }
    }
    return result;
  }

  void _reload(){
    setState((){
      _future=_load();
      _searched=false;
      _matches=const [];
    });
  }

  void _find(List<Map<String,dynamic>> rows) {
    if(!_allowed)return;
    setState((){
      _searched=true;
      _matches=NcDuplicateAdvisor.suggest(
        companyId:widget.company.id,
        description:_description,
        sector:_sector,
        existingOpenNcs:rows,
      );
    });
  }

  Future<void> _openExisting(NcSimilarityCandidate hit) async {
    if(!_allowed || hit.companyId!=widget.company.id)return;
    await Navigator.of(context).push(MaterialPageRoute<void>(
      builder:(_)=>NcFollowupDetailScreen(
        company:widget.company,nc:Map<String,dynamic>.from(hit.row)),
    ));
    if(mounted)_reload();
  }

  Future<void> _startNew() async {
    if(!_allowed)return;
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>
      AlertDialog(
        title:const Text('Registrar outra situação?'),
        content:const Text('Confira se o problema já está cadastrado. '
          'Uma nova Ronda registra uma nova visita; se for a mesma NC, '
          'prefira acrescentar um acompanhamento ao histórico existente.'),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(ctx,false),
            child:const Text('Voltar')),
          FilledButton(onPressed:()=>Navigator.pop(ctx,true),
            child:const Text('Iniciar nova Ronda')),
        ],
      ),
    );
    if(ok==true&&mounted&&_allowed){
      await Navigator.of(context).push(MaterialPageRoute<void>(
        builder:(_)=>ExpressRoundScreen(company:widget.company)));
      if(mounted)_reload();
    }
  }

  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Evitar NC duplicada'),
      actions:[IconButton(
        tooltip:'Atualizar registros locais',
        icon:const Icon(Icons.refresh),
        onPressed:_reload,
      )]),
    body:SafeArea(child:FutureBuilder<List<Map<String,dynamic>>>(
      future:_future,
      builder:(context,snapshot){
        if(!snapshot.hasData&&!snapshot.hasError){
          return const Center(child:CircularProgressIndicator());
        }
        if(snapshot.hasError){
          return ListView(padding:const EdgeInsets.all(22),children:[
            const Text('Não foi possível consultar as NCs locais. '
              'Nenhum registro foi alterado. Não presuma que não existem '
              'pendências nesta empresa.'),
            const SizedBox(height:12),
            FilledButton(onPressed:_reload,child:const Text('Tentar novamente')),
          ]);
        }
        final rows=snapshot.data!;
        return SingleChildScrollView(
          padding:const EdgeInsets.all(16),
          child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
          Text(widget.company.name,
            style:Theme.of(context).textTheme.titleLarge),
          const SizedBox(height:9),
          const Text('Antes de criar outra ocorrência, descreva o problema. '
            'O aplicativo vai sugerir NCs abertas semelhantes, '
            'mas a decisão de vincular é sempre do técnico.'),
          const SizedBox(height:14),
          TextFormField(
            minLines:2,maxLines:4,maxLength:300,
            decoration:const InputDecoration(
              labelText:'Problema encontrado',
              hintText:'Ex.: esteira transportadora sem proteção',
              border:OutlineInputBorder()),
            onChanged:(v)=>setState((){
              _description=v;
              _searched=false;
              _matches=const [];
            }),
          ),
          const SizedBox(height:7),
          TextFormField(
            maxLength:80,
            decoration:const InputDecoration(
              labelText:'Setor (recomendado)',
              hintText:'Ex.: Produção',
              border:OutlineInputBorder()),
            onChanged:(v)=>setState((){
              _sector=v;
              _searched=false;
              _matches=const [];
            }),
          ),
          FilledButton.icon(
            onPressed:_allowed&&_description.trim().length>=8?
              ()=>_find(rows):null,
            icon:const Icon(Icons.manage_search),
            label:const Text('Conferir NCs semelhantes')),
          const SizedBox(height:14),
          if(_searched) ...[
            Text(_matches.isEmpty?
              'Nenhuma correspondência identificada nesta consulta local.':
              'Possíveis pendências já cadastradas',
              style:Theme.of(context).textTheme.titleMedium),
            const SizedBox(height:7),
            if(_matches.isEmpty)const Text(
              'Isso NÃO confirma que o problema seja novo. '
              'Consulte o histórico completo antes de criar outra NC.'),
            for(final hit in _matches) Card(child:Padding(
              padding:const EdgeInsets.all(14),
              child:Column(crossAxisAlignment:CrossAxisAlignment.start,
                children:[
                  const Text('Possível correspondência — confira em campo',
                    style:TextStyle(fontSize:13,fontWeight:FontWeight.w700)),
                  const SizedBox(height:5),
                  Text(hit.description,
                    style:const TextStyle(fontSize:16,
                      fontWeight:FontWeight.w700)),
                  const SizedBox(height:7),
                  Text('NC: '+hit.id+
                    (hit.sector.isEmpty?'':' • '+hit.sector)),
                  const SizedBox(height:8),
                  FilledButton.icon(
                    onPressed:_allowed?()=>_openExisting(hit):null,
                    icon:const Icon(Icons.history_outlined),
                    label:const Text('Acompanhar esta NC')),
                ],
              ),
            )),
          ],
          const SizedBox(height:16),
          OutlinedButton.icon(
            onPressed:_allowed?_startNew:null,
            icon:const Icon(Icons.add_circle_outline),
            label:const Text('Não é a mesma situação • Nova Ronda')),
          const SizedBox(height:12),
          const Text('Consulta baseada somente nas NCs abertas salvas '
            'neste aparelho. Não consulta a Central nem verifica '
            'automaticamente a correção. Nenhum registro é '
            'mesclado ou encerrado.',
            style:TextStyle(fontSize:13)),
        ]));
      },
    )),
  );
}
