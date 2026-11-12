# Auditar SST — Portal CIPA de uso simples e avaliação de aderência à NR-05

Data de referência: 06/11/2026

## Experiência para usuários com pouca familiaridade com celular

O portal de membros continua **independente** da conta de técnicos e
administradores. O acesso somente é exibido após autenticação individual
validada no servidor. Esta mudança implementa a primeira simplificação:

- Abertura com a pergunta **O que você quer fazer hoje?**;
- Três opções grandes de 58 px de altura: **Ver reuniões**,
  **Minhas tarefas** e **Avisar uma situação**;
- Botões com ícone e texto legível, altura generosa e linguagem comum;
- Ação de observação somente se o servidor concedeu a função;
- Instrução curta de que não é preciso conhecer o número da NR;
- Demais seções (avisos, treinamento, documentos, observações e lembretes)
  dentro de **Mais informações**, minimizando a sobrecarga visual;
- Permanecem o texto de segurança, a exigência de sessão válida e
  o aviso de que confirmar ciência não comprova presença/assinatura.

**Não implementado ainda:** leitura por voz, envio de áudio, modo de alto
contraste personalizado, teste assistido com membros reais, notificações
push e login em produção. Não prometer esses recursos antes de homologá-los.

## Aderência prática da gestão à NR-05

Referência oficial: [NR-05 — Comissão Interna de Prevenção de Acidentes e
de Assédio, MTE](https://www.gov.br/trabalho-e-emprego/pt-br/acesso-a-informacao/participacao-social/conselhos-e-orgaos-colegiados/comissao-tripartite-partitaria-permanente/normas-regulamentadora/normas-regulamentadoras-vigentes/NR05atualizada2023.pdf).

| Item | Como o Auditar SST pode apoiar | Limitação / evidência necessária |
|---|---|---|
| 5.3.1 | Observações de riscos, ações, programa preventivo e registro de propostas | Verificação de campo, participação da CIPA e PGR não são automáticos |
| 5.3.1 j | Avisos e pautas podem incluir prevenção ao assédio e violência | Comprovar ações e treinamentos reais; não usar portal aberto como canal sensível |
| 5.4 e Quadro I | Mandatos e membros são cadastráveis | Dimensionamento por estabelecimento e riscos, titularidade e eleição devem ser validados |
| 5.5 | Registros de processo eleitoral | Prazos, voto secreto, quórum, apuração e confiabilidade precisam ser comprovados |
| 5.6 | Agenda de reuniões, pautas, presença, decisões, atas e ações | Atas precisam da assinatura real dos presentes e disponibilização adequada |
| 5.7 | Acompanhamento de treinamentos | Validar carga horária, conteúdos, modalidade, participação e comprovantes |
| 5.9.2 | Organização documental | Prazo mínimo de guarda de cinco anos exige retenção e backup efetivos |
| Anexo I | CIPA em construção | Regras específicas do setor exigem análise separada |

## O que não se pode afirmar

O portal **ainda não está em produção**; possui teste de regras e autorização
com dados fictícios. O sistema **não torna uma CIPA conforme por si só**.
Não há comprovação automática de eleição regular, frequência das reuniões,
documento assinado, presença em treinamento, funcionamento de comissão,
participação da equipe ou retenção de documentos por cinco anos.

A melhoria desta branch é somente **de interface do membro**. Não altera
Code.gs, MultiUser.gs, permissões no servidor, banco, sincronização,
gestão de atas, assinaturas, sistema de eleições ou registros existentes.

Para liberação: validar fluxo de login individual e controles no servidor;
testar em Android/Windows e com membros pouco experientes; verificar
acessibilidade com leitor de tela e uso de fontes ampliadas; homologar
backup de evidências e política de privacidade.

## Refinamento adicional — guia explicativo ao membro (06/11/2026)

A tela individual, ainda bloqueada sem sessão autorizada, ganhou uma seção expansível **Como funciona a minha participação**, dividida em três instruções: reunião/ciência, andamento ou ajuda em tarefa e observação de uma situação. Os textos explicam que ciência não é presença, andamento depende de conferência e observação não abre ou encerra NC. Também foi corrigido o ícone de **Avisar uma situação** para representar registro textual (o formulário não oferece anexar foto).

Adicionado teste de widget para conferir a visibilidade das instruções e a diferença entre ciência e presença. **Teste ainda não reexecutado nesta alteração; instalação, compilação final e acesso individual em produção continuam bloqueados.** Não foram alterados autenticação, compartilhamento, servidor nem o projeto Web.
