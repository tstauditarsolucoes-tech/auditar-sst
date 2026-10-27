# Guia de entrega ao programador — Auditar SST em servidor próprio
**Preparado em 27/10/2026 · Repositório público: `tstauditarsolucoes-tech/auditar-sst` · Branch de organização: `organize/sst-em-pasta-20261027`**

## 1. O que está sendo entregue
A pasta `Auditar-SST/` reúne as fontes SST de Android/Windows, bases Flutter legadas, patches incrementais, scripts de montagem/testes, módulo administrativo, Painel do Cliente e integrações. A última linha de código identificada corresponde aos builds Android **v3.29.198** e Windows **v3.30.126** (26/10/2026). São versões desktop/mobile: **não equivalem a um sistema web já implantável**.

Esta organização moveu os arquivos SST da raiz para `Auditar-SST/` na branch candidata. A pasta e seus módulos estão no Git; **dados de empresas, usuários, fotos, assinaturas, histórico e segredos operacionais não fazem parte do repositório**. Não buscar nem armazenar esses dados no diretório público do site.

## 2. Mapa para começar
| Local relativo a `Auditar-SST/` | Função |
| --- | --- |
| `source_overrides/Auditar_SST_v1_5_dashboard/` | Base Flutter e código de referência |
| `Auditar_SST_v1.5_dashboard_completo*.zip` | Bases legadas exigidas por scripts de montagem |
| `source_v3290_final/` | Fonte de apoio da linha SST |
| `tools/` | Scripts determinísticos de montagem, correções e regressão |
| `feature_sources/` | Agenda, vistorias, NCs, biblioteca técnica, central administrativa, permissões e fontes Apps Script |
| `build_sources/` | Fontes incrementais do Painel do Cliente e dos módulos |
| `auditar-sst-master/`, `auditar-sst-master-windows/` | Componentes administrativos SST |
| `hostinger-media-api/` | API PHP para evidências, mídia e recuperação |
| `entrega_gs_2026-10-14/` | Fontes legadas de integração com Central Online |
| `docs/` | Documentação, testes e critérios de homologação |
| `ci/workflows/` | Cópias dos workflows principais para consulta |

**Os workflows executáveis do GitHub continuam obrigatoriamente na raiz `/.github/workflows/`.** Eles copiam temporariamente os arquivos de `Auditar-SST/` para o diretório de trabalho do runner, porque a montagem legada usa caminhos relativos à raiz. Esse procedimento ocorre só no ambiente de CI, não no servidor em produção.

## 3. Separar o projeto web do aplicativo instalado
O código Flutter foi desenvolvido e homologado principalmente para Android/Windows. Antes de executar `flutter build web`, inventariar o uso de armazenamento SQLite, `sqflite_common_ffi`, câmera, biometria, assinaturas, arquivos, impressão, compartilhamento e sincronização. Implementar as alternativas para navegador quando necessário e acrescentar testes web. Não assumir que os executáveis Android/Windows podem ser enviados diretamente ao hospedador para funcionarem como site.

O `ClientPortal.html` do Painel do Cliente utiliza fluxos ligados à Central Online/Google Apps Script. Hospedá-lo como HTML estático, isoladamente, não transforma chamadas `google.script.run` em API web. Para servidor próprio, construir ou adaptar um backend autenticado que exponha contratos equivalentes, com validação das permissões **no servidor** e isolamento por empresa.

A pasta `hostinger-media-api/` contém um ponto de partida PHP. Ler seu README antes da instalação. Configurações com chaves, armazenamento e credenciais devem ficar fora do Git, preferencialmente fora do diretório público do servidor. Configurar HTTPS, permissões mínimas, limites de upload, acesso autenticado à mídia, backups e logs.

## 4. Arquitetura de implantação proposta (sujeita a validação)
1. **Frontend web responsivo** com rotas para técnico, cliente e administrador, sem chaves embutidas no JavaScript do navegador.
2. **API própria** com autenticação, autorização por função e por empresa, trilha de auditoria, filas de eventos e endpoints das NCs/Agenda/PDF.
3. **Banco transacional** com migrações versionadas e backups testados; nunca copiar diretamente o banco local do usuário para o webroot.
4. **Armazenamento privado de fotos e assinaturas** com URLs autenticadas ou temporárias, retenção e restauração verificadas.
5. **Conector de compatibilidade com a Central existente** até validar a substituição segura das rotas Apps Script e da sincronização offline.

Essa arquitetura é um roteiro, **não uma mudança implantada** neste commit. A escolha de stack web, hospedador, banco, domínio e migração de dados exige inventário do ambiente real e autorização.

## 5. Regras que não podem ser quebradas
- Preservar todas as empresas, relatórios, vistorias, NCs, evidências antes/depois, assinaturas e históricos.
- Primeiro login online e modo offline existentes continuam funcionando nos apps instalados.
- Não mudar os IDs das empresas, contratos de sincronização, autenticação, mídia/Drive, IA, Apps Script ou esquema de banco sem testes de compatibilidade, backups e aprovação.
- Não compartilhar `AUDITAR_SYNC_KEY`, keystore de assinatura Android, senhas, tokens, `config.php` real ou chaves de API em commits, arquivos do site ou conversas.
- Este repositório é **público**: verificar conteúdo e histórico antes de incluir configurações sensíveis.
- Nenhum deploy de produção, merge do PR #15 ou publicação pública de APK é autorizado por esta reorganização.

## 6. Checklist de aceite para a futura versão web
- [ ] Frontend web funciona em PC e celular, inclusive com letras legíveis e navegação clara.
- [ ] Cliente só visualiza sua empresa; técnico e ADM obedecem permissões.
- [ ] NC aberta → cliente registra correção com foto → técnico valida ou rejeita com motivo; histórico preservado.
- [ ] Agenda e painel carregam dados salvos e atualizam mudanças sem apagar estado.
- [ ] PDFs mantêm fotos, logos, assinaturas, paginação e compartilhamento seguro.
- [ ] Upload e download de evidências funcionam em HTTPS, sem exposição pública de arquivos.
- [ ] Migração simulada em cópia do banco, backup e restauração comprovados.
- [ ] Testes de regressão Android/Windows após qualquer alteração de API compartilhada.
- [ ] Homologação em dispositivos reais e autorização expressa antes de disponibilizar aos clientes.

## 7. Próximas decisões com a Auditar
Solicitar ao responsável os detalhes do servidor/domínio, tecnologias preferidas, banco atual, contratos da Central Online e procedimento de backup **por canal seguro**. Preparar ambiente de homologação separado da produção. A migração para web deve ser realizada por fases e com plano de reversão.
