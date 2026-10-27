# Auditar SST Web — homologação privada

**Atualização 27/10/2026. Nenhuma implantação em produção.**

A estrutura anterior era um protótipo estático; agora há uma aba **opcional** com login de teste e APIs Node/PostgreSQL para NCs, vistorias/Ronda, agenda, Plano de Ação, suporte cliente, Central ADM, imagens fictícias em volume Docker privado e PDF resumido de vistoria concluída.

- O entrypoint Docker **padrão permanece fechado** para dados de negócio.
- A ativação exige o overlay privado, HTTPS de teste separado do domínio final, Access List no Nginx Proxy Manager e dois roles de DB separados.
- Nenhuma porta de banco/API/web é publicada no host pelo Compose.
- Não há migração de dados reais nem sincronização com Flutter/Drive/Apps Script.
- O domínio tst.auditarsolucoes.com.br permanece intacto.

## Como entregar ao Júlio

1. [GUIA_PRIVADO_JULIO.md](GUIA_PRIVADO_JULIO.md): roteiro exato para testes com contas fictícias.
2. [../STATUS_REAL_E_ACEITE_20261027.md](../STATUS_REAL_E_ACEITE_20261027.md): matriz de pendências, critérios de aceite e bloqueios.
3. [db/README.md](db/README.md): migrações versionadas 001 a 007.
4. [api/README.md](api/README.md): contratos dos pilotos e limites.
5. [GUIA_NGINX_PROXY_MANAGER_TST.md](GUIA_NGINX_PROXY_MANAGER_TST.md): integração de rede NPM.

A CI testa o React, API isolada, PostgreSQL RLS multitenant, sessões e fluxo HTTP de homologação. **CI bem-sucedida não comprova testes físicos nem autoriza produção.**

Não executar seeds fictícias em VPS, não limpar volumes nem substituir o Proxy Host existente sem autorização escrita.
