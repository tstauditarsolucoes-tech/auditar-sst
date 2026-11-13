# Minha CIPA — aplicativo individual, opcional e com modo offline

Data: 13/11/2026. Status: **homologação experimental**, PR #61. Mantém a versão Android/Windows do **Auditar SST técnico** intacta. Não modifica o Web/VPS pendente nem publica APK.

## Arquitetura

1. O aplicativo individual **Minha CIPA — Auditar** usa login por e-mail e código de uso único na Central existente. Não recebe login do TST/administrador nem a chave mestre de sincronização do Auditar SST.
2. A Central consulta o módulo CIPA vinculado ao mandato e devolve **somente os dados autorizados** ao membro, conforme as rotas de homologação. O app recusa registros com empresa, mandato ou integrante diferentes.
3. Após login e confirmação online, o membro pode **optar por ativar** uso offline no próprio aparelho, definindo PIN de seis números.
4. O app salva a última consulta pessoal (atividades, reuniões, avisos, vistorias e informações liberadas) em arquivo AES-256-GCM no diretório interno. A chave de arquivo fica no KeyStore via secure storage, separada do arquivo. A prova do PIN usa PBKDF2-HMAC-SHA256 com 120.000 iterações. Não é armazenado token de sessão offline.
5. Sem internet, o integrante informa o mesmo e-mail e PIN; recebe acesso **somente de leitura** à consulta salva por até **24 horas** após a última sincronização online. Após cinco tentativas erradas de PIN, o acesso offline é bloqueado até nova ativação autenticada online.
6. A vistoria guiada pode ser preenchida offline em até três perguntas, com até duas fotos, observação e rascunho criptografado no dispositivo. Não se transmite nenhum dado enquanto offline.
7. Ao entrar online, o botão **Enviar vistorias salvas** lê rascunhos completos do mandato autorizado, revalida a sessão no servidor, usa a mesma identificação por tentativa e só remove o rascunho após confirmação do relato **e das fotos**. Falhas e incompletos permanecem locais para análise e nova tentativa manual.
8. A Central do TST/ADM pode acompanhar o relato, consultar fotos privadas e enviar orientação, sem permitir que o cipeiro conclua um laudo, feche uma ação ou certifique a conformidade.

## Restrições essenciais

- **Offline não equivale a acesso permanentemente autorizado.** Se o membro for desligado, o mandato revogado ou a autorização retirada enquanto o aparelho está sem internet, a mudança não será detectada antes de um contato online. O limite de 24h reduz a janela; não é revogação instantânea.
- O relógio local é usado na expiração. Deve-se testar manipulação do relógio e proteger armazenamento conforme a política da empresa. Esta é uma implementação de homologação.
- Sair da conta **apaga cache e rascunhos daquele vínculo**; se houver pendências, a tela deve advertir antes. Fechar a consulta offline não apaga os arquivos, mas exige PIN no próximo acesso.
- Anexos de fotografias permanecem no armazenamento privado definido para as fotos da CIPA. Uma imagem só entra no servidor após confirmação de autorização e vínculo.
- O upload é **manual**, não uma sincronização em background; notificações push e uso offline de biblioteca técnica completa continuam fora desta etapa.
- A primeira versão permite **um rascunho de vistoria avulsa por integrante** e um rascunho por agendamento. Múltiplas vistorias avulsas simultâneas e exportação para recuperação deverão ser ampliadas antes de um piloto extensivo.
- Pendências associadas a agendamentos removidos/cancelados ou mandatos trocados exigem revisão técnica de retenção e descarte, não migração automática para nova empresa.
- A homologação deve incluir **duas empresas**, troca/revogação de membro, rede totalmente offline, rede intermitente com apenas uma foto entregue, aparelho reiniciado, celular compartilhado, tentativas erradas de PIN, expiração das 24h, LGPD, backups e critérios de retenção.

## Critérios de aceite antes do APK

- CI do backend, Central, API membro, interface membro e montagem app aprovado.
- Rotas de homologação configuradas e revisadas, armazenamento de fotos privado, permissões e backups definidos.
- Testes presenciais com aparelhos Android físicos e comprovação visual dos estados **salvo local**, **pendente**, **enviando** e **confirmado**.
- Aprovação formal do responsável da Auditar para piloto restrito; sem merge ou instalação de produção apenas pelo CI.

O aplicativo segue **opcional**, e o uso da CIPA no Auditar SST principal permanece possível sem instalá-lo.
