# Auditar SST — revisão de navegação, preservação e homologação
**Referência:** 13/10/2026. **Status:** inventário estático executado; testes em aparelhos e integrações reais ainda pendentes.

## Constatações objetivas verificadas
- A linha compilada Android v3.29.187 e Windows v3.30.110 passou em CI anterior no commit `48541e8dd05623fbd556cc8d710e8cecc8b325e2`.
- Inventário do app montado: Android **65 telas**, Windows **68 telas**; em ambas, **0 imports locais ausentes e 0 telas sem cadeia estática detectada**.
- Rótulos de navegação repetidos entre arquivos: **31 Android, 39 Windows**. Trata-se de repetição de texto, **não comprovação de função inútil ou duplicação de dados**.
- A Visita Rápida recebeu alternância entre quatro tarefas mantendo a empresa selecionada; correção adicional do título superior preparada na versão em teste v3.29.188/v3.30.111.
- A Central em produção não foi homologada quanto a `company_group_sync_v1`, `worksite_followup_sync_v1`, `offline_knowledge_sync_v1` e `client_treatment_v2`. Arquivos de GS na branch não provam deploy.
- O diário atual de obras limita a lista a **80 entradas**: `WorksiteFollowup.fromMap` aplica `.take(80)`, `toMap` aplica `.take(80)` e o botão Novo Registro salva `[result,..._record.log].take(80)`. Uma entrada antiga pode sair dessa lista após a 81ª inclusão. É um risco real de perda de histórico **dentro do diário local**, e exige correção com preservação/backup, sem alterações silenciosas.
- README antes desta revisão exibia Android 3.29.158 / Windows 3.30.77 e referências de CI de outubro anterior; agora orienta a consultar `CURRENT_VERSION.md` para não divulgar versões obsoletas.

## Próximos blocos, sem exclusão de funções

| Prioridade | Problema | Critério de aceitação |
|---|---|---|
| P0 | Homologação dos builds novos | Android/Windows instalam sobre versão existente sem perder dados, fotos e usuários; check de assinatura Android e funcionamento Windows |
| P0 | Retenção do diário de obras | Nenhuma entrada desaparece ao alcançar 80; arquivo antigo consultável e recuperável, sem substituir o GS atual; testes 79/80/81 registros e restauração |
| P0 | Isolamento multiempresa | Dados de duas obras da mesma construtora não se misturam; cliente sem autorização não acessa outra empresa na API, mídia ou relatórios |
| P1 | Sobreposição de menus | Mesmos módulos preservados; caminhos mais rápidos na Home e Visita Rápida; testes em 360/412 px e desktop |
| P1 | Indicadores repetidos | Painel executivo e Controle Operacional reconciliam quantidades, filtros e períodos para a mesma empresa |
| P1 | GS/Painel Cliente | Backup da Central atual, ativação de rotas isoladas apenas em homologação autorizada, testes de permissões e retorno offline |
| P1 | NR-18 | Subitens por tipo de andaime, fase e risco sem registrar automaticamente NC nem declarar conformidade |
| P2 | Alertas e mensagens de erro | Diferenciar offline, rota ausente, acesso negado, dados rejeitados e conflito; jamais prometer envio se mensagem só está na fila |

## Regras de classificação de duplicidade
1. **Atalho repetido**: mesma função exposta em duas telas por conveniência. Não remover sem teste de usabilidade.
2. **Interface redundante**: duas visões de dados equivalentes, com rótulos diferentes; preferir acesso contextual sem excluir funcionalidades.
3. **Implementação histórica**: arquivos preservados na branch que não compõem o app montado; não confundir com função inativa.
4. **Função inutilizável**: requer reprodução de falha ou comprovação de impossibilidade de acesso/execução no app compilado.
5. **Dependência da Central**: funcionalidade preparada mas indisponível sem deploy/rota; indicar claramente e manter operação offline.

## Regra de publicação
PR #15 **Draft**. Sem merge, sem deploy GS e sem alteração de `database.dart`, sincronização, `auth_service.dart`, IA, fotos ou Drive. CI verde **não comprova** testes físicos nem autoriza instalação em produção sem backup.
