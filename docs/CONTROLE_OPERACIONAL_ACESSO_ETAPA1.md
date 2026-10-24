# Controle Operacional — ajuste de acesso e comunicação de rede

- A lista de empresas fica limitada ao escopo AuthService.canAccessCompany.
- Para contas restritas sem empresa selecionada, consultas gerenciais não fazem mais agregações globais. A conta ADM preserva a visão geral.
- Resultado assíncrono é descartado se a conta ou empresa for alterada durante a consulta.
- O botão de prioridade exige seleção de empresa quando não há visão geral autorizada.
- A indicação de 'Online' (teste de resolução de nome) foi corrigida para 'Rede disponível • Central não testada'.
- Não altera AuthService, banco, sincronização, mídia, IA ou GS.
- Requer flutter analyze, testes e CI antes de distribuição.
