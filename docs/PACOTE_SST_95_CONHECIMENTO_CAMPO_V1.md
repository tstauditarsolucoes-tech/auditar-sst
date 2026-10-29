# Auditar SST — pacote 9,5: conhecimento online e campo rápido

**Preparado na branch** `feature/client-panel-permissions-v329106`. **Sem merge nem deploy da Central**.

## O que foi acrescentado

1. **Biblioteca técnica compartilhada**: novo arquivo `OfflineKnowledgeCloud.gs` e rota `offline_knowledge_sync_v1` no `Code.gs` preparado durante a montagem. A rota autentica a sessão interna via `authorizeMultiUserToken_`; perfis de clientes não acessam o catálogo. As edições concorrentes usam versão-base, sem sobrescrever silenciosamente.
2. **Aprendizado automático sem internet**: a aplicação de uma sugestão primeiro grava no arquivo local já existente; depois cria uma entrada em fila complementar. Falhas de conexão não atrasam Ronda ou Vistoria. Ao conectar, envia lotes de até 20 modelos e busca catálogo recente de até 80 itens por consulta; o cache por usuário mantém no máximo 120 modelos. O catálogo local antigo (até 500 modelos) não é apagado.
3. **Migração conservadora**: na primeira conexão autenticada, tenta incluir modelos locais antigos de regras técnicas reconhecidas na fila. Não transfere fotos, descrições completas de vistorias, nomes de empresas nem cadastros. Modelos sem regra reconhecida continuam locais até revisão específica.
4. **Campo mais rápido**: botão explícito para retomar a última empresa/obra autorizada. Três comandos visíveis e compactos: Nova ronda, Nova vistoria e Registrar não conformidade. A empresa não muda automaticamente, prevenindo registros na empresa errada.
5. **Sem alteração do núcleo**: não muda `database.dart`, `device_sync_service.dart`, `sync_coordinator.dart`, `auth_service.dart`, HTTP, fotos, Drive ou IA. A Central mantém suas rotas anteriores. Nenhuma nova tabela local.

## Conflitos e proteção

- Somente modelos reutilizáveis com regra técnica identificável são compartilhados.
- O servidor rejeita CPF, CNPJ e e-mail inseridos no conteúdo reutilizável e limita o tamanho dos campos.
- O título compartilhado é o título técnico canônico da regra, não o nome personalizado do setor/empresa.
- A chave do modelo não muda conforme o dispositivo. Cada versão remota é atualizada apenas quando sua revisão é conhecida.
- Se houver conflito, a versão remota não é sobrescrita. A correção local permanece disponível e a fila pendente continua preservada. Uma tela administrativa de resolução de conflitos é etapa posterior.
- O arquivo de fila mantém cópia de segurança local (`.bak`) para recuperação.
- Como o cache contém modelos técnicos, não fotos nem ocorrências, é pequeno. Os registros SST originais não são apagados para liberar espaço.

## Ativação em homologação — exige autorização separada para publicar

1. Na implantação de teste do Apps Script da Central, **acrescentar** `OfflineKnowledgeCloud.gs` ao projeto existente, sem substituir `Code.gs` com uma versão antiga.
2. Acrescentar ao `doPost` a rota, antes de `device_sync_push`:
   ```javascript
   if (request.action === 'offline_knowledge_sync_v1') {
     return jsonResponse_(offlineKnowledgeSyncV1_(request));
   }
   ```
3. Executar `node tools/test_offline_knowledge_cloud_v1.js` e validar manualmente autorização, edição simultânea, login offline, Android/Windows e abertura do aplicativo sem Central.
4. Somente após backup e aprovação explícita, implantar a **Central de homologação**. **Não houve deploy automático nesta implementação.**

> Se a rota não estiver implantada, o aplicativo conserva normalmente o aprendizado local e mantém as correções pendentes. A simples criação do módulo no GitHub **não significa que o compartilhamento online já esteja operacional em produção**.

## Testes de aceitação

- Em 360 px e 412 px, abrir a última empresa explicitamente e registrar Ronda/Vistoria/NC.
- Aplicar sugestão sem internet; fechar e reabrir; conferir aprendizado local.
- Conectar a Central de homologação; confirmar modelo enviado sem fotos nem dados pessoais.
- Abrir outro aparelho autorizado; pesquisar a mesma falha; confirmar modelo remoto.
- Editar o mesmo modelo simultaneamente em dois aparelhos: deve ocorrer conflito, nunca perda silenciosa.
- Testar ausência da rota, autenticação vencida e lote inválido sem impedir registro de campo.
- Conferir `git diff` e hashes dos arquivos protegidos, CI Android e Windows, APK assinado, instalador e portátil.
- Executar teste físico antes de distribuir a novas empresas.

## Próximos incrementos para nota 9,5

Gestão individual de etapas por obra, visão de recorrências e evolução (antes/depois), filtros por responsável/prazo e resumo gerencial por construtora. Estas melhorias exigem testes próprios e não devem ser consideradas prontas apenas porque a biblioteca online foi preparada.
