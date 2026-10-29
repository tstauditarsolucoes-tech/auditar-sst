# Portal individual CIPA — entrega de desenvolvimento, 28/10/2026

## Estado e limites

Implementação para homologação privada, na branch `migration/preparacao-web-20261027`.
Não é publicação em produção. PR #23 deve continuar draft.
As telas e APIs deste portal usam **somente o banco novo da VPS**.
Não há conexão com os registros CIPA do aplicativo Flutter/Central Online,
nem migração automática, sincronização com Android/Windows ou dados antigos.
Não habilitar no domínio final nem afirmar paridade com o app atual.

## Entregue no código

- Página `/cipa?empresa=<UUID público da empresa>`, responsiva, sem dados demonstrativos no login.
- Identidade individual diferente das contas de técnico/gestão/cliente.
- Senha temporária criada pela gestão, troca obrigatória, sessão de duas horas,
  cookie Secure/HttpOnly/SameSite Strict, senha scrypt, CSRF e limite de tentativas persistente.
- Vínculos explícitos por empresa/mandato/membro. Reaproveitamento de conta em novo mandato.
- Membro consulta ações atribuídas, solicita apoio e envia conclusão para validação.
- A equipe valida, devolve com motivo ou reabre ações; controle de versão evita sobrescrita silenciosa.
- Reuniões e confirmação de leitura: **não equivale a presença nem assinatura**.
- Sugestões de prevenção identificadas, avisos do mandato e histórico.
- Gestão cria/vincula/revoga acesso e redefine senha, encerrando sessões.
- Pedidos de apoio podem receber orientação individual na ação.
- Nenhum registro é excluído ao revogar acesso ou encerrar mandato.
- Canal de denúncias não incluído, conforme orientação do usuário.

## Parte do Júlio (somente depois de CI verde e aceite)

1. Usar ambiente e hostname HTTPS exclusivos de homologação. Seguir
   `GUIA_PRIVADO_JULIO.md` e os guias existentes, sem reutilizar banco/volume de outros sistemas.
2. Fazer backup e ensaiar restauração do banco de homologação antes da nova migration.
3. Com a API parada apenas nesse projeto, aplicar em ordem `db/migrations/014_cipa_member_portal.sql`, `015_cipa_guided_participation.sql` e `016_cipa_private_observation_photos.sql`
   depois de 001–013, com o administrador do banco dedicado. As migrations são transacionais
   e rejeitam reaplicação. Nunca usar seeds `db/tests/*` em uma VPS com dados de pessoas.
4. Reconstruir API e web com os novos fontes. O Dockerfile inclui os novos módulos.
5. Somente para o teste privado, definir `AUDITAR_ENABLE_CIPA_PORTAL=PRIVATE_STAGING_CIPA_ONLY`
   junto do opt-in privado já existente. O padrão é `disabled`.
6. Preservar a topologia existente: Nginx Proxy Manager -> web -> API -> DB;
   não expor API/DB diretamente, não ocupar portas dos outros sistemas e não publicar
   `tst.auditarsolucoes.com.br`. A trava do domínio final continua ativa.
7. Entrar como gestor/ADM da empresa de teste, cadastrar mandato e membros no módulo CIPA,
   abrir a gestão do portal e criar os acessos. Entregar link e senha separadamente ao membro.

Para suspender o piloto: voltar o opt-in a `disabled` e recriar **somente a API desse projeto**.
Não apagar volumes, tabelas ou histórico; não executar `down -v`, `prune` ou comandos globais.
Um rollback de código deve preservar a migration e os dados; não há migration destrutiva de retorno.

## Aceite manual obrigatório

- Gestor cria acesso -> membro entra -> troca senha -> vê somente mandato autorizado.
- Dois membros da mesma empresa não veem ações/sugestões privadas um do outro.
- Outra empresa não acessa o mandato mesmo conhecendo seu UUID.
- Membro informa conclusão -> gestor valida/devolve -> histórico aparece ao membro.
- Reenvio após perda de resposta não duplica eventos nem ações.
- Revogação bloqueia o vínculo e invalida sessões, sem apagar histórico.
- Redefinição exige nova troca de senha e invalida as sessões anteriores.
- Testar Android Chrome, navegador de PC, teclado e telas de 360/412 px.
- Confirmar na prática que nenhum módulo do app atual deixou de funcionar.

## Testes e pontos ainda fora desta entrega

`api/cipaPortal.test.mjs`: valida contratos e falha fechada sem banco.
`api/integration.cipa-portal.ci.test.mjs`: PostgreSQL efêmero com contas sintéticas,
RLS entre empresas e membros, auth real, trocas de senha, CSRF, validação e revogação.
`validate-web-foundation.yml` executa build TypeScript e a integração após os testes CIPA existentes.

Os resultados finais da CI e o aceite visual/real precisam ser conferidos na execução do commit.
Não há envio automático de e-mails, presença assinada, upload de documentos do membro,
importação de legado ou sincronização com Flutter neste portal.
Listas são limitadas explicitamente (200 ações, 100 reuniões, 300 entradas recentes);
os dados mais antigos permanecem no banco. Expandir com paginação antes de escalar o uso.
Sugestões gerais ainda não possuem uma resposta privada independente; a equipe pode
atribuir uma ação para encaminhamento ou publicar aviso sem expor a sugestão.

## Funcionalidades adicionadas após a primeira entrega

- Roteiro mensal da CIPA com progresso gravado por conta, mandato e competência. Cada marcação é um evento imutável; nenhuma presença é presumida.
- Registro identificado de observação com local e descrição; foto opcional de até 2 MB (JPEG, PNG, WebP) no volume **privado de homologação**. A gestão visualiza a evidência autorizada; não se cria NC automaticamente.
- Próxima reunião e arquivo `.ics` opcional com lembrete de véspera, importado voluntariamente no calendário do usuário. **Não há envio automático** de e-mails/push.
- Pauta sugerida e minuta guiada de reunião, sempre revisável. Minuta e confirmação de leitura **não** são ata assinada nem registro de presença.
- Relatório mensal de gestão apurado no banco (ações = situação atual; reuniões/eventos = competência) e opção imprimir/salvar PDF pelo navegador.
- Antes de testar fotos, confirme o volume privado `/var/lib/auditar-staging/evidence`, permissões de diretório e restauração do backup. Fotos são proibidas no Drive da produção durante o piloto.
- O portal **continua sem importação ou sincronização com o aplicativo legado**. Todos os registros no piloto são novos e isolados.
- No aceite, incluir foto >2MB, arquivo com assinatura inválida, acesso do membro B à foto do membro A, acesso de outra empresa, perda de resposta e reenvio, mandato encerrado, revogação e fechamento do navegador.
- A migração 016 acrescenta a tabela `sst.cipa_portal_photo` e não altera a tabela de evidências do sistema atual.
