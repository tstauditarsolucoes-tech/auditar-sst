# Nginx Proxy Manager — tst.auditarsolucoes.com.br

**Configuração candidata para o Julio, NÃO aplicada na VPS.**

Infraestrutura informada em 27/10/2026:
- VPS compartilhada com vários sistemas;
- Docker e Node.js permitidos;
- proxy reverso: Nginx Proxy Manager (NPM);
- domínio informado: **tst.auditarsolucoes.com.br**.

Não foi possível confirmar o conteúdo atual do domínio a partir desta auditoria. **Antes de qualquer alteração, Julio deve verificar se já existe um Proxy Host para esse endereço ou se outro serviço o utiliza. Nunca sobrescrever a rota existente sem backup e autorização.**

## 1. Como conectar os contêineres sem ocupar portas do host

A base atual em compose.staging.yml não publica portas do host e mantém API/PostgreSQL numa rede interna. O override compose.npm.example.yml adiciona **somente o contêiner web** à rede Docker externa já utilizada pelo Nginx Proxy Manager.

- API Node: apenas rede backend interna, porta 3000 não publicada.
- PostgreSQL: apenas rede backend interna, porta 5432 não publicada.
- Web Nginx: porta interna 8080, com alias DNS Docker **auditar-sst-web-hml** visível ao NPM depois de anexado.
- Proxy NPM: mantém suas portas 80/443 existentes e encaminha para o contêiner web quando autorizado.

O nome verdadeiro da rede externa **não foi informado**. Julio deve consultar o Docker da VPS (por exemplo a rede ligada ao contêiner NPM), sem enviar credenciais ao repositório. A variável de ambiente AUDITAR_NPM_NETWORK será definida **localmente na VPS**, nunca fixada nos arquivos públicos.

## 2. Validação da composição (sem tocar no NPM)

No diretório infra/ e após criar o arquivo de senha de teste para o Postgres, o programador poderá validar:

- export AUDITAR_NPM_NETWORK=nome_real_da_rede_do_npm
- docker compose -p auditar-sst-web-hml -f compose.staging.yml -f compose.npm.example.yml config --quiet

**Apenas o comando config acima analisa a configuração. Ele não cria contêiner, não mexe na rede NPM, não altera DNS e não publica site.**

Depois da revisão do administrador e com staging autorizado, poderá subir o projeto separado usando as mesmas opções -p/-f e up --build -d. Não executar sobre outros projetos nem reutilizar seus volumes.

## 3. Configuração proposta do Proxy Host (somente após autorização)

Conferir primeiro que o domínio está livre ou que a transição do serviço existente foi aprovada.

| Campo Nginx Proxy Manager | Valor candidato |
| --- | --- |
| Domain Names | tst.auditarsolucoes.com.br |
| Scheme | http (NPM faz a terminação TLS/HTTPS) |
| Forward Hostname / IP | auditar-sst-web-hml |
| Forward Port | 8080 |
| SSL | certificado válido para tst.auditarsolucoes.com.br |
| Force SSL | ativar depois de confirmar o certificado |
| Websocket Support | somente se a interface futura usar WebSocket |
| Access control | restringir homologação a equipe autorizada; revisar impacto em login final |

Atenção: **não apontar o domínio real para a página de teste como se fosse sistema final**. A interface atual só mostra o estado da API e NÃO possui login nem dados. Prefira um subdomínio exclusivo de homologação (nome definido com o dono do DNS) enquanto o endereço principal estiver em uso.

## 4. Checklist de segurança antes de expor qualquer rota

- [ ] Backup/exportação das configurações atuais do NPM e inventário de Proxy Hosts.
- [ ] Confirmar dono e uso atual de tst.auditarsolucoes.com.br, DNS, certificado e política de mudança.
- [ ] Identificar a rede Docker externa correta, nome sem conflito e permissão do administrador.
- [ ] Confirmar que db e api **não** foram anexados à rede do NPM e não publicam portas.
- [ ] Certificado TLS válido, redirecionamento HTTPS e logs com retenção controlada.
- [ ] Backend com autenticação, controle por empresa, proteção CSRF, rate limiting e revisão de segurança **antes** de expor dados.
- [ ] Homologação com usuários de teste, sem dados pessoais verdadeiros.
- [ ] Plano de reversão da rota e teste de retorno do serviço anterior.
- [ ] Autorização expressa da Auditar antes da virada para o domínio definitivo.

**Não executar deploy automático, alterar NPM, criar certificado, redirecionar DNS, carregar dados reais ou iniciar migração de banco com este arquivo.**
