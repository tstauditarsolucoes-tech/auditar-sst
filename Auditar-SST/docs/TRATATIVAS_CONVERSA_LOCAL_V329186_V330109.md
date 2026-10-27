# Comunicação Auditar — mensagens locais por conversa

Implementado no código-fonte preparado para Android 3.29.186 e Windows 3.30.109, sem publicação da Central.

- O técnico abre a conversa geral de uma empresa ou uma tratativa por ocorrência.
- Quando a mensagem é aceita no armazenamento protegido do aparelho, o editor é limpo e a mensagem aparece como pendente na própria conversa.
- O envio utiliza a fila anterior (mesmo identificador de requisição). A mensagem só aparece como confirmada depois da resposta de sucesso da Central.
- Outras mensagens em atraso, de empresas diferentes, não determinam o status da mensagem atual.
- Mensagens rejeitadas permanecem guardadas até decisão explícita na Caixa de entrada.
- Mensagens locais não são mostradas a outras empresas/assuntos ou a uma conta diferente.
- A fila continua independente do banco e da sincronização SST; nenhuma foto ou arquivo é transmitido por este canal.

Aceitação: confirmar armazenamento sem internet, reinício do aplicativo, status por ID, revisão de recusa, envio após reconexão, isolamento entre A/B, mensagens antigas e PDFs preservados.
