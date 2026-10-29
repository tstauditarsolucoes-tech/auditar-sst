# Auditar SST — implantação NOVA sem migração de dados antigos (27/10/2026)

## Decisão de escopo
**Não migrar** para a nova versão Web registros de Google Sheets, Apps Script, Drive, assinaturas, fotografias, relatórios ou histórico dos aplicativos atuais. O novo PostgreSQL começa vazio e recebe somente cadastros novos, criados após a homologação e autorização de uso real.

**Não apagar** ou substituir o sistema atual. A opção de não migrar não é autorização para excluir nem liberar acesso público ao legado. O sistema anterior deve permanecer preservado e consultável pela Auditar, conforme suas obrigações documentais e de retenção.

## O que Júlio pode testar
Somente um ambiente privado de homologação separado, com contas e dados **fictícios**:
1. Subir serviços Docker exclusivos e HTTPS de testes, com lista de acesso NPM.
2. Criar PostgreSQL **novo e vazio**; executar migrações 001 a 012 na ordem, seguindo o guia privado.
3. Criar usuário fictício de ADM e empresas fictícias, sem reutilizar senhas atuais.
4. Testar NCs, vistorias, plano de ação, agenda, portal, painel ADM, treinamentos/DDS, CIPA, fotos fictícias e PDFs candidatos.
5. Testar permissões entre empresas, logout, tentativas de login, relatório e restauração de banco + volume privado.
6. Registrar aceite por dispositivo e navegador antes de qualquer acesso real.

## O que AINDA depende de desenvolvimento — não atribuir a Júlio
- Equivalência integral do app Flutter: funções de campo, toda biblioteca técnica, treinamentos/assinaturas, PDF Padrão Auditar 3 definitivo e demais funções específicas.
- Integração Android APK e Windows EXE à API própria; autenticação móvel, filas offline, conflitos e atualização local precisam de implementação/testes separados.
- Segurança de produção: revisão de permissões, backup com restauração real, monitoramento, recuperação de contas, logs, cotas/retencão e conformidade LGPD.
- Validação física de fotos, PDFs e interfaces PC/celular, incluindo assinaturas. Uma lista de participantes digitada não é comprovante de presença.
- Plano de ativação com rollback: não substituir o proxy do domínio atual sem autorização expressa.

## Critério para futuro início zerado
Se a Auditar decidir iniciar o NOVO sistema com dados novos, criar as empresas e usuários NOVOS nele, revisar os perfis, treinar a equipe e validar o primeiro ciclo completo de vistoria/NC/foto/PDF por empresa. **Essa decisão não liga automaticamente os aplicativos Android/Windows ao novo backend.** Enquanto estiverem no legado, não haverá sincronização entre esses aplicativos e a Web nova.

## Interdições permanentes
Não fazer importação retroativa; não apagar dados/volumes antigos; não apontar o domínio atual à homologação; não reutilizar credenciais do Apps Script; não publicar bancos ou mídias; não mesclar PR #23 ou #15 sem testes e aprovação.

## Referências
- Branch: `migration/preparacao-web-20261027`
- PR #23: https://github.com/tstauditarsolucoes-tech/auditar-sst/pull/23
- Guia: `infra/GUIA_PRIVADO_JULIO.md`

**A CI comprova testes automatizados de homologação, não autorização de produção.**
