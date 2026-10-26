# Homologação rápida — Auditar SST

Use este roteiro depois que Android e Windows concluírem o CI com sucesso.

## Android
1. Instalar a atualização por cima da versão atual, sem desinstalar.
2. Confirmar login online e, depois, abertura offline com credenciais previamente autorizadas.
3. Abrir uma empresa existente e confirmar histórico, fotos e registros já salvos.
4. Criar uma Ronda/Vistoria de teste com foto, descrição curta e sugestão automática.
5. Salvar, fechar e reabrir o registro.
6. Gerar relatório e conferir fotos, NR, risco, recomendação e conclusão.
7. Confirmar que IA continua disponível, mas o fluxo básico funciona sem depender dela.
8. Conferir DDS/Treinamentos, planejamento anual e CIPA.
9. Conferir visão gerencial e indicadores de pendências/capacitação.
10. Com internet ativa, verificar fila de envio e sincronização normal.

## Windows
1. Atualizar pelo instalador sem apagar dados locais.
2. Repetir abertura de empresa, histórico e relatório.
3. Conferir layout em janela normal e maximizada.
4. Testar PDF Completo/Executivo/Padrão Auditar já utilizados pela operação.
5. Conferir DDS/Treinamentos, CIPA e relatórios gerenciais.
6. Conferir instalação e versão portátil.

## Critério de aprovação
A release é considerada homologada somente quando:
- não houver perda de registros/fotos;
- os relatórios abrirem e gerarem PDF normalmente;
- login e modo offline previamente autorizado continuarem funcionando;
- sincronização permanecer normal;
- Android e Windows não apresentarem travamento nos fluxos acima.

Se qualquer item falhar, registrar tela, ação realizada e mensagem exibida antes de atualizar novamente.


## Acesso à Linha do Tempo (atalho de campo)
Na versão com este acabamento, abrir **Iniciar visita**, selecionar a empresa/obra
e tocar em **Linha do tempo da empresa**. O atalho reutiliza a mesma tela
`CompanyTimelineScreen` já existente e respeita a seleção e a autorização da
empresa. O histórico consolidado inclui vistorias, DDS, treinamentos, segurança
e correções.

Este histórico local **não é** a conversa de correção com o cliente. Para ela,
usar **Comunicação e tratativas** no app, ou **Comunicação e linha do tempo** no
Painel do Cliente, condicionado à implantação e à permissão `tratativas`.
