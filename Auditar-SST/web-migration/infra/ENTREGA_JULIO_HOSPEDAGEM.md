# Auditar SST — entrega atualizada ao Júlio (VPS compartilhada, sem importação de dados)
**Atualizado em 28/10/2026 · Branch `migration/preparacao-web-20261027` · PR #23 DRAFT**

## Pedido do Júlio
Migrar a tecnologia para **Web no navegador, sem depender de instalar o aplicativo Flutter** para acessar a interface. Infraestrutura confirmada: VPS compartilhada com Docker, outros sistemas no mesmo servidor, Node.js autorizado, PostgreSQL em contêiner e Nginx Proxy Manager (NPM). **Domínio definitivo previsto:** `tst.auditarsolucoes.com.br`.

**Atenção:** o domínio já está atendendo outro sistema. Ele NÃO deve ser alterado agora. Identificar o serviço existente e suas dependências no NPM/Docker antes de planejar a troca.

## O que a equipe já preparou no repositório
- **Web:** React + TypeScript responsivo (PC e celular), interface autenticada por módulos; NC, vistoria/Ronda, agenda, Plano de Ação, solicitações do cliente, Central ADM, CIPA e treinamentos/DDS em diferentes graus de piloto.
- **Backend:** Node.js 24, sessões/cookie HttpOnly/CSRF para Web, autenticação nativa opcional segregada, RLS no PostgreSQL e controle de acesso por empresa.
- **Banco:** PostgreSQL 17 em contêiner exclusivo, migrações **001–014** e volumes privados próprios de homologação.
- **Portal individual CIPA:** login separado, troca de senha, mandatos autorizados, ações do membro, apoio, reuniões, avisos e validação pela equipe. Desligado por padrão; [guia específico e limites](PORTAL_CIPA_HOMOLOGACAO.md). Não usa os dados CIPA do app atual.
- **Documentos:** relatório de vistoria PDF piloto com recomendações e fotografias ampliadas e minuta educativa sem validade de comprovação de presença.
- **Clientes Android/Windows:** os aplicativos Flutter originais continuam independentes e **não utilizam o novo backend**. Existem uma sonda Dart desligada, autenticação nativa opcional e endpoints de consulta/criação de rascunho **para homologação técnica**; ainda não são sincronização instalada.
- **CI:** testes automatizados para React, API, PostgreSQL multiempresa, Docker, PDF e contratos Dart usando identidades e dados sintéticos. CI aprovada não substitui testes físicos.

## Nova decisão de dados
**NÃO migrar dados antigos.** O banco Web começará vazio e somente receberá cadastros novos quando houver autorização de produção. Não importar histórico, NC, fotos, certificados, assinaturas, Drive, Sheets ou Apps Script. **Não apagar** nada do ambiente anterior: continuar consultável e preservado conforme retenção aplicável. Não haverá sincronização automática entre o app legado e Web enquanto os clientes não forem atualizados.

## Como Júlio pode conferir a VPS SEM instalar nada
Clonar a branch em **pasta nova**, separar 3 segredos apenas de teste conforme o [guia privado](GUIA_PRIVADO_JULIO.md) e definir em seu próprio terminal duas variáveis verificadas, sem colocá-las no Git:
```bash
export AUDITAR_NPM_NETWORK=NOME_REAL_DA_REDE_EXISTENTE_NPM
export AUDITAR_ALLOWED_ORIGIN=https://HOSTNAME_PRIVADO_DE_HOMOLOGACAO
cd Auditar-SST/web-migration/infra
bash scripts/preflight-shared-vps.sh
```
O script só faz leituras e `docker compose config`: verifica conflito de projeto, contêiner, volumes, rede NPM, origem HTTPS e ausência de portas publicadas. **Não sobe contêineres, não altera NPM, DNS, TLS, banco ou serviços existentes.** Se encontrar um projeto com o mesmo nome já instalado, interrompe até inventário. O hostname de homologação deve ser outro, autorizado por quem administra DNS/NPM.

O passo a passo posterior de **homologação privada** com autorização está em [GUIA_PRIVADO_JULIO.md](GUIA_PRIVADO_JULIO.md). A API e o banco NÃO devem publicar portas do host; o proxy encaminha somente ao contêiner Web, nome/alias `auditar-sst-web-hml`, porta interna `8080`.

## O que NÃO é responsabilidade exclusiva do Júlio
Ainda há desenvolvimento para tornar a Web equivalente ao aplicativo SST inteiro: relatórios oficiais Padrão Auditar 3, certificados/assinaturas com comprovação, recursos offline reais, captura de mídia, segurança/recuperação de conta, testes reais de UX e integração da nova API aos aplicativos Android/Windows (caso essas versões continuem em uso). Também é necessário validar todos os controles de segurança, backup/restauração, monitoramento e política LGPD antes de utilizar dados reais.

## Responsabilidades antes da publicação
**Desenvolvimento:** concluir funcionalidades, testes de isolamento, backups e homologação dos três clientes; aprovar artefatos.  
**Júlio (VPS):** inventariar rede e Proxy Host do domínio ocupado, capacidade, contêineres/volumes e dependências; configurar novo projeto Docker privado e separado, segredos, SSL/Access List de teste, backups/monitoramento e validar restauração.  
**Auditar:** testar os fluxos no navegador e aparelhos reais e autorizar explicitamente a futura troca de domínio.

### Regra para o domínio
**`tst.auditarsolucoes.com.br` é o destino pretendido, não um domínio disponível hoje.** Nenhuma alteração de Proxy Host, DNS ou remoção do serviço existente foi executada; a virada exige identificação do que está publicado ali, backup verificável, aceite da Auditar e plano de reversão. Não usar `docker compose down -v`, `docker system prune` nem comandos globais na VPS compartilhada.

Links: [PR #23](https://github.com/tstauditarsolucoes-tech/auditar-sst/pull/23) · [Guia NPM](GUIA_NGINX_PROXY_MANAGER_TST.md) · [Plano de virada](PLANO_DE_VIRADA_DO_DOMINIO_TST.md) · [Início limpo sem migração](../INICIO_LIMPO_SEM_MIGRACAO_20261027.md).

**Estado técnico: Web de homologação e base própria preparadas, mas NÃO homologadas como produto final e ainda NÃO publicadas na VPS.**

