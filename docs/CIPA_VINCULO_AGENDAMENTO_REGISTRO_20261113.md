# Minha CIPA — vínculo da programação com o registro (13/11/2026)

**Estado: desenvolvimento/homologação, sem publicação, merge ou acesso de integrantes reais.**
Esta entrega incremental parte da PR #47 e preserva o aplicativo técnico Auditar SST.
Não altera a versão Web/VPS em preparação.

## Fluxo proposto

1. A Central administrativa agenda uma vistoria para **empresa, mandato e integrante** autorizados.
2. O integrante abre **Iniciar esta vistoria**. O **tema** vem preenchido; o **local** deve ser informado por ele, não deduzido do nome do tema. Responde três perguntas visuais, confere e envia.
3. O app informa o `scheduleId` ao servidor usando o mesmo endpoint pessoal de observação. O servidor valida sessão ativa, vínculo com empresa/mandato/membro e existência de agendamento ativo, antes e dentro do lock.
4. Na primeira gravação aceita, a observação mantém o ID do agendamento em `target_id`. Retentativa com o mesmo `requestId` e conteúdo idêntico é idempotente; conteúdo divergente retorna `ID_REUSED`. Um segundo registro para o mesmo agendamento retorna `ALREADY_SUBMITTED`.
5. O portal do membro e a consulta administrativa exibem `Registro enviado` e o ID do relato vinculado. **Isso não significa vistoria validada, ação corrigida, NC encerrada, relatório aprovado ou presença em reunião.** A orientação técnica da PR #47 permanece em fluxo separado.
6. O agendamento cancelado deixa de aparecer na lista ativa, sem apagar relatos históricos.

## Segurança e limites

- Nenhum token, segredo, foto, endereço de empresa ou dado real está armazenado neste repositório.
- Os testes simulam duas empresas/mandatos; o servidor nunca aceita `scheduleId` de outro vínculo.
- A lista de relatórios recentes do membro é limitada a 100 eventos. Antes do uso com volume alto, paginar consultas e consolidar o índice de vínculos para evitar uma vistoria antiga aparecer como `Programada` após muitos eventos.
- O app ainda não tem fotos, notificações push, narração das perguntas, rascunho persistente criptografado nem sincronização offline. Nenhuma dessas capacidades deve ser anunciada como disponível.
- Os arquivos são fontes experimentais. Eles **não estão integrados** no backend real do Apps Script nem no APK/EXE de produção.

## Homologação indispensável antes da implantação

- Aprovação dos cinco conjuntos de testes automatizados, inclusive vinculação, idempotência e isolamento entre empresas.
- Backup, revisão do roteador do Apps Script e implantação **somente em ambiente de homologação**, conferindo permissões da Central.
- Teste manual com duas empresas, mandatos e integrantes diferentes; sessão vencida/revogada; tentativa de reutilizar `requestId`; rede intermitente; cancelamento durante envio.
- Testes em aparelho físico Android, letras ampliadas e navegação por integrante com pouca prática.
- Confirmação de que um relato não encerra ação corretiva e só o TST/perfil autorizado pode validar providências.

## Próximas entregas

1. **Fotos privadas**: até duas imagens por observação, captura direta, acesso por empresa/mandato e revisão técnica, sem URL pública.
2. **Rascunho offline protegido**: armazenamento criptografado, chave do dispositivo, fila durável, `requestId` persistido e limpeza na revogação da sessão.
3. **Avisos simples**: agenda e novas orientações dentro do app; push somente depois de checar consentimento, credenciais e isolamento por empresa.
4. **Modo fácil**: fonte, leitura de perguntas e tutorial no primeiro acesso, com opção de reabrir.
5. **Painel gerencial**: indicadores autorizados de participação, tarefas, reuniões, vistorias vinculadas e ações vencidas, sem divulgar dados pessoais desnecessários.
