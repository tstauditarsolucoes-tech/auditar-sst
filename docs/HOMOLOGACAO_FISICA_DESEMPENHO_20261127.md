# Homologação física — Android 3.29.205 / Windows 3.30.129

Referências: #88, #87, #90 e execução 45979846793. O retorno positivo de sincronização da 3.29.204 não comprova todas as rotas; preserve essa referência. 3.29.205 tem CI aprovado, mas não aceite físico. Windows é debug, sem credenciais, não é distribuição comercial.

## Protocolo
- Usar dispositivo/PC de teste, conta e empresa fictícias, ambiente de homologação autorizado. Antes de executar, verificar backup e possibilidade de retorno à versão operacional. Não desinstalar nem limpar dados.
- Para Android, comparar 3.29.204 e 3.29.205 no mesmo aparelho e condições, somente após confirmar que o candidato está isolado e autorizado; nunca substituir automaticamente. Não publicar o APK conectado, chaves ou arquivos de configuração.
- Com ADB autorizado e apenas um aparelho conectado, abra o candidato e rode `python tools/android_perf_snapshot_v1.py PACKAGE_EXATO` antes e após cada roteiro. O utilitário é somente leitura, imprime métricas agregadas (PSS, frames, jank e percentis quando disponíveis) e não coleta logcat, credenciais ou dados do cliente. `python tools/android_perf_snapshot_v1.py --self-test` valida o parser sem aparelho.
- Meça separadamente três aberturas a frio, tempo até a tela ficar utilizável e três repetições de cada navegação, com cronômetro. Não force encerramento com trabalho não salvo. Anote mediana, condições, versão, travamentos e overflow. Os contadores gfxinfo são cumulativos; comparar deltas somente quando o processo e contadores não reiniciarem; percentis são cumulativos. Flutter pode não expor todos os frames via gfxinfo; ausência de métricas não significa desempenho bom.
- Repetir o roteiro no Windows, medindo abertura, tempo de navegação e memória pelo Gerenciador de Tarefas (não registrar nomes de clientes ou dados pessoais).
- Roteiro: login offline/online; empresa e Ronda com foto fictícia; PDF; lista de pendências; CIPA com/sem mandato; investigação de acidentes e revisão humana da IA; APR/AR/PT/PET com minutas; rubrica e invalidação após edição; rascunho offline e restauração; sincronização bidirecional com duplicidade e reenvio, exclusivamente no ambiente autorizado. Não enviar fotos reais à IA.
- Critério de bloqueio: travamento, perda de rascunho, configuração manual inesperada, overflow, divergência entre contas, duplicação, regressão de desempenho relevante sem investigação ou falha de rollback. Registrar medidas e evidências sanitizadas; não presumir causa de lentidão nem aprovar sem teste.
- Rubricas são ciência; PT/PET não autorizam trabalho. Não liberar produção nem mudar GS/SQLite/servidor com este protocolo.

| Versão | Dispositivo/OS | Roteiro | Tempo mediano | PSS/jank | Resultado | Evidência sanitizada |
|---|---|---|---|---|---|---|
| 3.29.204 | | | | | Pendente | |
| 3.29.205 | | | | | Pendente | |
| 3.30.129 | | | | | Pendente | |

Manter #88 aberto até aceite físico documentado. Este protocolo não executa o teste nem comprova correção da lentidão.
