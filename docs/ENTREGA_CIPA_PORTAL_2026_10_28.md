# Auditar SST — CIPA e portal individual

Registro de entrega de desenvolvimento de 28/10/2026. Não é liberação de produção.

## Portal entregue e validado

Branch: `migration/preparacao-web-20261027`, PR #23 em draft.
Código validado: `9bcd0acf8fd90bddbd7a0db8055e882990ab5906`.

Validação completa aprovada:
https://github.com/tstauditarsolucoes-tech/auditar-sst/actions/runs/40786326195

Inclui build React/TypeScript, API, PostgreSQL efêmero, isolamento por empresa/membro,
autenticação e troca de senha, invalidação de sessões, permissões da equipe,
reenvios e conflitos de versão. A API local passou 49 testes; as regras e o cliente
web passaram 17 testes. Os dados da integração são exclusivamente sintéticos.

O portal permite acesso individual, ações atribuídas, pedidos de apoio, envio de
conclusão para validação, orientação/devolução pela equipe, reuniões e ciência
de convocação, avisos, sugestões identificadas e histórico. A gestão cria,
vincula, revoga acessos e redefine senhas. O membro não valida a própria conclusão.
Ciência de convocação não equivale a presença ou assinatura.

A tela de acesso foi conferida em navegador local. Sem API, mostrou erro e não
simulou autenticação. Isso não substitui o aceite autenticado no ambiente HTTPS
de homologação, em PC e celular.

## Melhorias do aplicativo atual

Branch: `feature/client-panel-permissions-v329106`, PR #15 em draft.
Código candidato mais recente: `0faad3df25d18c650f8c7b3147540cf6c86a1c9a`.

Sete melhorias no código: passagem de mandato sem duplicar ações; pedido de apoio;
resumo mensal PDF; visão simplificada; sugestão de pauta; arquivamento/restauração
e revisão de atas sem copiar assinaturas; vitrine de resultados coletivos.

As regras e os patches Android/Windows passaram na validação anterior
40787186799. A validação da correção mais recente é:
https://github.com/tstauditarsolucoes-tech/auditar-sst/actions/runs/40789760881

A primeira compilação completa parou no patch porque o formatador quebrou campos
em linhas diferentes. O patch passou a aceitar essas variações, com teste de
regressão e conferência no arquivo real que falhou. A execução seguinte aplicou
o patch preservando os outros 170 arquivos do app, mas a análise Flutter apontou
um erro de tipo: registros legados podem ter `companyId` nulo. O domínio foi
corrigido para aceitar e ignorar explicitamente esses registros, sem assumir uma
empresa, com dois testes adicionais. A rotina também ignora telas já desmontadas.
As novas compilações completas abaixo precisam ter seu resultado final conferido
antes de distribuir. Não há APK/EXE deste lote confirmado neste registro:

- Android candidato 3.29.199+341:
  https://github.com/tstauditarsolucoes-tech/auditar-sst/actions/runs/40789754441
- Windows candidato 3.30.127+314:
  https://github.com/tstauditarsolucoes-tech/auditar-sst/actions/runs/40789754587

Não distribuir APK/EXE antigos como se incluíssem este lote. Homologação em aparelhos,
fotos, anexos, assinaturas e sincronização existente continua obrigatória.

## Limite essencial: não está tudo integrado

O portal usa o banco novo. O app atual usa a Central Online. Não há sincronização
entre os dois nesta entrega. Não foi feita importação de registros antigos nem
substituição do sistema atual. A migração completa para servidor próprio e a
integração dos apps ainda são trabalho de desenvolvimento e validação, não apenas
uma configuração de hospedagem a cargo do Júlio.

O canal de denúncias segue excluído. Não houve merge, deploy, mudança de domínio,
remoção de sistema, limpeza de banco ou alteração de dados de usuários.

## Próxima etapa do Júlio

Depois do aceite, preparar exclusivamente homologação privada na VPS compartilhada,
com hostname próprio, HTTPS e acesso restrito no Nginx Proxy Manager. Não usar ainda
`tst.auditarsolucoes.com.br`, que permanece ocupado.

Guia de implantação e aceite:
`Auditar-SST/web-migration/infra/PORTAL_CIPA_HOMOLOGACAO.md`.
Inclui migration 014 após 001–013, cópia de segurança, reconstrução dos containers
do projeto e habilitação explícita do portal. Não apagar volumes nem interferir
nos outros sistemas da VPS.

Somente depois de integração, testes e aceite deverá ser planejada a substituição
do sistema atual. Não há autorização nesta entrega para essa troca em produção.
