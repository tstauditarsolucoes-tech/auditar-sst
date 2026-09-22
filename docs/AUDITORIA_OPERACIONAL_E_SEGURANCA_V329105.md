# Auditar SST — consolidação e revisão de segurança (22/09/2026)

Escopo: Android v3.29.105 e Windows v3.30.29, derivados das bases funcionais v3.29.104/v3.30.28. Esta é uma revisão estática e de testes sintéticos; **não certifica adequação integral à LGPD nem substitui teste real com clientes**.

## Proteções acrescentadas nesta etapa

- Em todos os pedidos efetuados pelo transporte compartilhado Apps Script, a URL inicial deve ser HTTPS. Um redirecionamento para HTTP, domínio externo, porta diferente de 443 ou URL com credenciais embutidas é recusado antes de qualquer nova transmissão. Google Apps Script pode continuar redirecionando somente entre seus domínios oficiais de serviço.
- O PDF da Ronda tem limite explícito de até 300 páginas, com blocos pagináveis. O teste de 30 e 50 registros com 30/50 arquivos de fotografia e textos extensos exercita versões fotográfica, técnica e modelo personalizado.
- O pipeline examina os PDFs produzidos, conta as imagens e confirma que a estrutura é válida. Artefatos de amostra são preservados no GitHub Actions.
- Os módulos de autenticação, banco local, backend e sincronização estruturada foram mantidos fora do escopo deste patch.

## Riscos e ações de implantação

| Item | Constatação/limitação | Ação antes da expansão comercial |
| --- | --- | --- |
| Chave global no aplicativo | A chave de transporte é incorporada ao binário por `--dart-define`. Qualquer segredo distribuído no cliente deve ser tratado como potencialmente recuperável. | Garantir autenticação e autorização **no servidor** por usuário, dispositivo, tenant e empresa para todas as rotas de sincronização/mídia; girar credenciais segundo procedimento controlado. Não usar a chave embutida como prova única de autorização. |
| Base local | Arquivos SQLite e fotos locais não demonstram criptografia própria em repouso nesta análise. O token de sessão é protegido por armazenamento seguro e o aplicativo pede login ao reiniciar. | Avaliar criptografia/isolamento dos arquivos, bloqueio de sessão, política de aparelho perdido e retenção de evidências antes do uso multiempresa em escala. |
| Fotos/assinaturas | A fila separada pode enviar sem bloquear o sync estruturado. Erros e pendências aparecem na Home, mas a recuperação após perda física de arquivo depende de backup prévio no Drive. | Executar roteiro de falha de rede e recuperação de mídia abaixo; nunca apagar dados locais até conferir cópia remota. |
| Acesso multiempresa | O cliente mantém escopo de empresas, mas a lógica do backend realmente implantado não foi auditada ponta a ponta. | Confirmar em ambiente de homologação que usuário A não consegue ler/gravar empresa B via chamadas diretas, inclusive PDFs, logos e fotos. |
| Relatórios técnicos | A IA apresenta recomendações que necessitam aprovação do técnico. | Registrar original e revisão aprovada; impedir conclusão com dados inferidos não verificados. |

## Roteiro presencial de homologação (requer dois dispositivos reais)

1. Realizar cópia de segurança e identificar duas contas de teste, cada qual com empresa distinta. Não desinstalar nem limpar dados.
2. No Android, desligar internet e criar 50 ocorrências com **50 fotos reais** distribuídas por setores, uma NC longa, uma assinatura e um registro de checklist não concluído. Confirmar contagem local e que nenhum item não vistoriado aparece como conforme.
3. Reativar internet. Acompanhar separadamente cadastros e evidências até ambos ficarem sem pendências; registrar horários e falhas. No Windows, receber os registros e abrir fotos e assinatura.
4. Simular interrupção de rede durante envio; religar e conferir não duplicação (ID) nem perda de evidência. Tentar o botão de envio manual uma vez.
5. Emitir Ronda em modelos fotográfico, técnico e personalizado com os 50 registros e conclusão longa; verificar visualmente primeira, intermediária e última página.
6. Fazer teste de acesso cruzado somente em contas fictícias autorizadas; confirmar bloqueio no servidor das rotas de mídia, download, edição e exportação.
7. Simular ausência **de arquivo local de teste já confirmado no Drive** e usar biblioteca/reparo para restaurar; não deletar uma evidência real sem backup confirmado.
8. Confirmar instalação sobre a versão anterior, dados e assinatura preservados, sem regressão no login e no cadastro de colaboradores.

**Critério de liberação comercial:** todos os testes em dispositivos reais e verificações de escopo do backend concluídos, com registro da revisão; compilação e testes sintéticos sozinhos não constituem homologação final.
