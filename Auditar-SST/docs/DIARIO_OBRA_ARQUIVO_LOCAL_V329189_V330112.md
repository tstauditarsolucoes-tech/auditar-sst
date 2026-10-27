# Diário da obra — proteção contra perda no limite de 80 lançamentos

Pacote em validação: Android v3.29.189+331 / Windows v3.30.112+299.

**Problema comprovado:** o acompanhamento anterior descartava silenciosamente os lançamentos mais antigos ao atingir 80 entradas; a Central V1 também limita o diário a 80.

**Correção preparada:** antes de salvar a 81ª entrada, o app copia os lançamentos excedentes para um histórico local independente, separado por obra e técnico. Só então salva os 80 lançamentos recentes no acompanhamento original. O histórico pode ser consultado pelo botão **Ver registros anteriores**.

- A operação de arquivamento é aguardada; se falhar, o diário atual não é truncado nem sobrescrito.
- Reenvios do mesmo lançamento não criam duplicidade no histórico.
- O formato enviado à Central, a rota `worksite_followup_sync_v1` e os serviços de autenticação e sincronização não mudam.
- Arquivos anteriores ficam **somente neste aparelho**; ainda NÃO são compartilhados pela Central e precisam entrar em um futuro projeto de backup, sujeito a autorização.
- Dados descartados por versões anteriores não são restaurados automaticamente.
- Testes de limite 80/81, repetição, isolamento entre obras e entre técnicos.
- PR #15 continua Draft; não há deploy do GS. Para aprovação de uso, testar com dados de exemplo, backup e duas contas reais de homologação.
