# Central de Vistorias e Devolutivas da CIPA — Homologação (11/11/2026)

## Objetivo
Concluir o primeiro ciclo seguro do relato de observação visual: **membro registra → administração da CIPA recebe → técnico/administrador registra devolutiva → membro consulta o retorno**.

Escopo de código: **projeto existente de gestão Android/Windows e cliente Android individual do membro**, não migração Web/VPS. O trabalho nesta branch é experimental, sem implantação, APK ou acesso real liberado.

## Fluxo implementado
1. O membro usa o roteiro de vistoria simples, enviado pelo canal autorizado de observação (PR #41 e #42).
2. A Central administrativa recebe registros do mandato e distingue vistorias orientadas de relatos livres.
3. A pessoa **autorizada como administradora da Central** pode registrar **Em análise** ou **Orientação enviada**. A segunda exige texto de no mínimo 8 caracteres, máximo 600. Nenhuma opção "Concluído" é disponibilizada nesta primeira fase para impedir falsa sensação de baixa de NC.
4. O servidor grava uma **nova linha imutável** de devolutiva com empresa, mandato, membro, id do relato, estado, mensagem, hora e id de quem revisou. Confere autorização, referência original e escopo dentro da trava de concorrência.
5. O membro consulta somente os próprios registros, com o estado e a orientação mais recentes. Não conhece o identificador do administrador; não pode editar o parecer.
6. A caixa da administração usa filtro por empresa e mandato. A devolutiva não altera o evento original nem cria ou encerra NC automaticamente.

## Restrições e segurança
- O processo exige o backend experimental `CipaMemberReviewsV1.gs` e uma integração explícita à `CipaMemberGatewayV1.gs`. O script real em produção **não foi tocado**. O recurso permanece desligado enquanto `CIPA_MEMBER_V1_ENABLED` não for habilitado após homologação.
- Só conta **ADM validada** pode escrever devolutivas pelo endpoint `cipa_member_admin_review_observation`. TST sem esse papel precisa de uma política servidor própria, que ainda não foi liberada.
- Relatos são identificados pelo id do registro original; empresa/mandato não podem ser escolhidos livremente para expor dados externos.
- Requisições de devolutiva têm identificador idempotente: reenvio exato não duplica histórico; reuso com dados diferentes é bloqueado.
- Comentários não devem conter dados médicos ou identificação desnecessária de terceiros; o formulário adverte isso, mas revisão humana e LGPD continuam necessárias.
- Conclusão técnica ou de ação corretiva exige outro fluxo com evidências e responsáveis.
- Fotos, anexos, gravações, notificações push e rascunhos persistentes **não estão implementados**. Esses recursos requerem armazenamento privado, política de acesso, apagamento e testes. Não compartilhar URLs públicas de imagens.

## O que ainda falta para produção
- [ ] Conferir a instalação do Apps Script real, as fontes de dados, usuários e autorizações em dois estabelecimentos e dois mandatos; executar backup e plano de reversão.
- [ ] Executar testes de backend, Flutter de ADM e API do membro com fixtures; testar falhas de rede, sessões revogadas, concorrência, idempotência.
- [ ] Integrar a Central ao aplicativo Android/Windows real com os scripts de patch e homologar o cliente Android separado.
- [ ] Criar política apropriada para respostas do TST (não só da administração).
- [ ] Testar efetivamente com membros iniciantes e letras ampliadas.
- [ ] Emitir builds **de homologação** e depois release assinado somente após autorização da Auditar.

A política documental/participação segue a NR-05, mas este sistema **não certifica conformidade normativa**.
