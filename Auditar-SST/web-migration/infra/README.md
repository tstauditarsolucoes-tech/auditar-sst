# Auditar SST Web — homologação privada

**Atualização 27/10/2026. Nenhuma implantação em produção.**

A estrutura Web React + TypeScript utiliza Node.js/PostgreSQL, com módulos de homologação para NCs, vistorias/Ronda, agenda, Plano de Ação, atendimento ao cliente, Central ADM, CIPA, treinamentos/DDS, imagens privadas e PDFs piloto. Autenticação nativa, consultas e criação de rascunhos via API são **opt-in, desligadas por padrão**; não estão integradas ao APK/EXE.

- O entrypoint Docker **padrão permanece fechado** para dados de negócio.
- A ativação exige o overlay privado, HTTPS de teste separado do domínio final, Access List no Nginx Proxy Manager e dois roles de DB separados. Antes disso, o Júlio deve executar **somente leitura** em `scripts/preflight-shared-vps.sh` para conferir conflitos na VPS compartilhada.
- Nenhuma porta de banco/API/web é publicada no host pelo Compose.
- **Decisão expressa: não haverá migração dos dados antigos.** A nova base começará vazia; manter os arquivos legados preservados. Não há sincronização pronta com o Flutter/Drive/Apps Script.
- O domínio tst.auditarsolucoes.com.br permanece intacto.

## Como entregar ao Júlio

1. [GUIA_PRIVADO_JULIO.md](GUIA_PRIVADO_JULIO.md): roteiro exato para testes com contas fictícias.
2. [../STATUS_REAL_E_ACEITE_20261027.md](../STATUS_REAL_E_ACEITE_20261027.md): matriz de pendências, critérios de aceite e bloqueios.
3. [db/README.md](db/README.md): migrações versionadas 001 a 013.
4. [api/README.md](api/README.md): contratos dos pilotos e limites.
5. [GUIA_NGINX_PROXY_MANAGER_TST.md](GUIA_NGINX_PROXY_MANAGER_TST.md): integração de rede NPM.
6. [ENTREGA_JULIO_HOSPEDAGEM.md](ENTREGA_JULIO_HOSPEDAGEM.md): entrega técnica atualizada à VPS compartilhada e domínio previsto.
7. [scripts/preflight-shared-vps.sh](scripts/preflight-shared-vps.sh): inspeção somente de leitura, sem instalar nada.

A CI testa o React, API isolada, PostgreSQL RLS multitenant, sessões e fluxo HTTP de homologação. **CI bem-sucedida não comprova testes físicos nem autoriza produção.**

Não executar seeds fictícias em VPS, não limpar volumes nem substituir o Proxy Host existente sem autorização escrita.
