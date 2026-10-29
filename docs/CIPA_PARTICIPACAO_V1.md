# CIPA — participação e continuidade no app atual

Data: 28/10/2026. Candidatos Android 3.29.199+341 e Windows 3.30.127+314.
Escopo: aplicativo Flutter atual. Não faz parte da migração web. Não contém canal de denúncias.

## Entregas de código

1. Passagem de mandato: seleção explícita de ações abertas de mandatos anteriores; registra uma referência, sem duplicar nem remover a ação. Origem, responsável, prazo, NC e anexos ficam preservados.
2. Pedido de apoio: compra, manutenção, autorização ou orientação; registro breve obrigatório e indicação destacada. Marcar apoio atendido não encerra a ação. Não há envio automático de mensagem/e-mail.
3. Resumo mensal PDF: reuniões realizadas no mês, conclusões datadas registradas pelo módulo e prioridades/pedidos de apoio atuais. Não inventa datas de conclusão de registros antigos ou de NCs com atualização automática. Não apresenta pendências atuais como fotografia histórica de um mês anterior.
4. Visão simplificada: atalhos, próxima reunião, ações e filtro por responsável. É uma organização visual da conta já autenticada, não um portal de membro nem uma barreira de acesso.
5. Pauta sugerida: seleção de ações pendentes, preservando o texto existente e evitando repetir linhas.
6. Proteção do histórico: arquivar/restaurar com motivo, sem exclusão física; não oculta ações abertas, mandato ativo, reuniões realizadas nem atas finalizadas/assinadas. Revisões de ata criam novo rascunho com versão crescente e motivo, sem copiar assinaturas. PDF identifica versão e situação.
7. Melhorias coletivas: vitrine de ações resolvidas e consulta das evidências, sem pontuação ou ranking de pessoas.

O calendário diferencia reunião agendada, realizada, cancelada e necessidade de conferência. Ele não certifica conformidade legal.

## Extensão prática para uso na versão ATUAL Android e Windows — 29/10/2026

- O módulo **Participação** inclui roteiro mensal com quatro itens marcáveis: observação segura do ambiente, acompanhamento de pendências, conferência de reunião e registro de melhoria.
- Cada marcação ou desmarcação registra novo evento `monthly_check` no envelope de `CIPA_DOCUMENTO` já existente, associado à empresa, mandato, competência `YYYY-MM` e identificador conhecido da atividade. Não há alteração em tabela, sincronização ou Apps Script.
- A lista de **situações observadas** permite informar local e descrição simples; o registro é `observation`, sem classificação automática como NC e sem canal de denúncias. Foto opcional pode ser selecionada **na sequência da gravação** ou depois pelo menu de anexos. Usa o fluxo de mídia existente `cipa_document`, sem alterar Drive ou Apps Script.
- **Guia de reuniões** com orientações antes, durante e depois. A opção **Preparar reunião guiada** reúne título, tipo, data, local e pauta editável; permite escolher pendências e agenda via `CipaManagementService.saveMeeting` com lista de presentes **vazia**, nunca presumida. Reaproveita os lembretes da agenda existente. Não cria assinatura, presença nem ata automaticamente.
- A visão simplificada apresenta **Por onde começar?**, atalhos, orientações em linguagem comum e um roteiro de cinco passos para novos integrantes. A ação **Informar andamento** salva um evento `progress_reported` sem modificar status da ação, sem aprovar conclusão e sem encerrar NC. O técnico continua responsável pelas validações.
- Estes recursos são visíveis na conta já autenticada e os marcadores mensais representam acompanhamento **compartilhado da equipe**, não prova de atividade individual, autoria do membro ou cumprimento legal da NR-05.
- **Web e VPS do Júlio permanecem fora do escopo e parados.** Esta entrega é somente do aplicativo atual.
- Antes da liberação, homologar em Android e Windows com empresa e mandatos de teste: itens de meses diferentes, marcar/desmarcar, observação com foto e recuperação da foto em outro aparelho com o fluxo existente, offline, sincronização e encerramento de mandato.
- Até essa homologação, o resultado é **candidato de desenvolvimento**; não substituir a versão instalada em produção.

## Persistência e proteção

- A implementação utiliza `CipaManagementService.saveRecord` e o envelope existente `CIPA_DOCUMENTO`, com marcador `auditar.cipa.participation.v1` para eventos administrativos. Não cria tabela nem tipo novo de transporte.
- Os eventos não são mostrados como documentos comuns e não são contados como documentos obrigatórios. Eventos de arquivamento/restauração e passagem são aditivos: não substituem os registros originais.
- A atualização de ação trazida preserva seu `mandateId` original. O evento de passagem registra IDs e fotografia dos campos relevantes no momento da passagem.
- Reuniões, membros, eleições, anexos e serviços de IA não são reimplementados.
- O patch é aplicado no final da montagem e verifica SHA-256 de todos os arquivos não-CIPA em `lib` e Apps Script. Banco, modelos, autenticação, HTTP, sincronização, Drive e mídia permanecem intocados.
- O registro operacional não identifica, por si só, quem realizou a alteração nem substitui uma trilha de auditoria de segurança. Acesso individual autenticado de membros permanece fora deste lote: exige revisão específica de autorização e permissões.

## Validação antes de liberar

- Executar o teste puro Dart e o teste do patch para os dois layouts, inclusive depois de `dart format`.
- Executar análise Flutter dos aplicativos realmente montados e compilar com a chave permanente existente; não trocar certificado, identificador ou remover dados do dispositivo.
- Homologar em empresa de teste: criar ação, pedir apoio, atender apoio, concluir; gerar resumo; trazer a ação aberta de um mandato antigo, editar e verificar que a origem e a evidência não mudaram.
- Arquivar/restaurar um registro permitido e verificar que nenhuma foto/assinatura sumiu. Confirmar que pendências abertas não oferecem arquivamento.
- Revisar e finalizar ata; comparar arquivos e anexos das duas versões. A revisão nova não deve herdar assinaturas da anterior.
- Testar 360/412 px, fonte ampliada e janela Windows estreita/larga. Conferir todas as 11 abas e a navegação lateral.
- Testar ida/volta dos novos eventos pelos mecanismos existentes em uma empresa de teste, entre Android e Windows, inclusive offline. Não publicar nova versão de Apps Script para este lote sem evidência de necessidade e autorização.
- Evitar uso simultâneo de clientes antigos e novos durante a homologação: versões antigas não conhecem o marcador administrativo e podem listar esses eventos entre documentos. Numeração de revisões e ordenação de eventos são locais; conflitos entre aparelhos precisam de homologação, não se presume garantia transacional distribuída.

Compilar e passar testes automatizados não substitui a homologação nos aparelhos. Não executar importação, limpeza, migração de dados nem publicação web como parte deste lote.

## Pendente para um portal **individual** dos integrantes

O modo simplificado entregue no aplicativo atual **não** possui login ou autorização independente por membro da CIPA. O filtro por nome e a possibilidade de informar andamento são apenas recursos da conta do técnico/gestor que já está conectada; não restringem dados aos membros. Não distribuir credenciais de técnico/ADM aos integrantes. Para liberar acesso individual no sistema atual, é necessário estudar autorização por empresa/mandato, credenciais, revogação, trilha de autoria e o contrato do backend atual **antes** de alterar autenticação/sincronização ou publicar GS, com homologação e reversão. A migração web e a VPS do Júlio seguem fora do escopo.

## Testes do incremento 29/10/2026

- [x] Código de interface atualizado com foto após observação, reunião guiada e informe de andamento não técnico.
- [x] Regras e testes focados de participação incluem isolamento da anotação por empresa e ação.
- [ ] Compilações Android/Windows do commit mais recente comprovadas.
- [ ] Homologar no aparelho: salvar observação com/sem foto; sincronizar foto em outro aparelho com a Central Online atual; agendar reunião guiada e conferir lembretes; informar andamento e conferir que status não mudou; retorno offline/online.
- [ ] Verificar abertura, fonte ampliada, 360/412 px e navegação desktop; obter aceite do responsável antes de substituir instaladores usados em produção.
