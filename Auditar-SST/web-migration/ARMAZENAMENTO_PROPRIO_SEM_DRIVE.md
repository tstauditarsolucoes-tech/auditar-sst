# Decisão de armazenamento — Auditar SST 100% servidor próprio
Data: 27/10/2026 — opção 1 escolhida por Luan/Auditar Soluções.

## Decisão

**O armazenamento principal do novo Auditar SST será integralmente próprio, no ambiente controlado pela Auditar.** A arquitetura final não dependerá do Google Drive nem do Google Apps Script para armazenar ou consultar registros, fotos, assinaturas e PDFs.

- Dados estruturados: PostgreSQL com volume privado e migrações versionadas.
- Arquivos grandes: armazenamento de objetos privado no próprio servidor/VPS (por exemplo, serviço S3-compatível autogerenciado, a ser escolhido pelo Júlio após confirmar capacidade e operações). **Não usar pastas públicas do Nginx** para evidências.
- Backend Node.js controla autorização por usuário, empresa e perfil; cliente não acessa volumes nem banco diretamente.
- Android, Windows e Web usam APIs autenticadas do mesmo servidor; o offline dos instalados será preservado com fila local confiável.

**Backups criptografados fora da VPS são indispensáveis**, mesmo mantendo o armazenamento operacional 100% próprio. Isso é cópia de segurança e não uma dependência do Drive em produção.

## Estado do código hoje

A branch `migration/preparacao-web-20261027` tem frontend React parcial, Node.js com **somente endpoint de saúde**, PostgreSQL de teste vazio e estrutura Docker isolada. **Ainda NÃO foi instalado/configurado serviço de arquivos, tabelas SST nem integração real.** Esta decisão documenta o alvo; não ativa upload, não move arquivos, não conecta o Drive nem altera os apps Android/Windows.

## Caminho lógico de um arquivo

1. Técnico registra NC/vistoria e seleciona foto ou assinatura no aplicativo (offline ou online).
2. Aplicativo armazena localmente até receber confirmação definitiva do servidor quando houver conectividade.
3. API verifica sessão, permissões, empresa, tipo/tamanho e integridade do conteúdo.
4. API armazena o arquivo no serviço privado do servidor e registra referência no PostgreSQL.
5. Outros clientes autorizados visualizam via API que verifica empresa/usuário. Acesso público direto ao volume é proibido.
6. Auditoria registra autoria, data, entidade, operações e eventuais substituições sem eliminar histórico.

### Modelo mínimo de metadados (conceitual)

| Campo | Finalidade |
| --- | --- |
| `id` imutável | Identificação do arquivo |
| `company_id` | Isolamento multiempresa |
| `owner_type/owner_id` | Vistoria, NC, assinatura, relatório etc. |
| `object_key` | Referência privada no armazenamento de objetos |
| `sha256` | Verificação da integridade do original |
| `mime_type`, `size_bytes` | Validação e limites |
| `created_by`, `created_at` | Auditoria |
| `legacy_source_id` (restrito) | Correspondência temporária com Drive/Hostinger |
| `retention_state` | Política de guarda e exclusão controlada |

Nunca confiar somente no `company_id` recebido do aplicativo; o servidor precisa aplicar a vinculação autorizada na sessão. A mídia sensível não deve conter CNPJ/nomes/segredos previsíveis na chave pública.

## Migração das fotografias e assinaturas do Drive

**Preservar tudo no Google Drive original até concluir a conferência e a aprovação da Auditar.**

1. Inventário autorizado das planilhas/registros e referências a arquivos Drive/Hostinger, sem expor dados pessoais no GitHub público.
2. Backup do legado, congelamento de versão e manifesto privado com IDs antigos, empresas, tipo de arquivo, tamanho e hash.
3. Copiar arquivos originais para o novo armazenamento em homologação; manter IDs de correlação. Não recomprimir originais.
4. Conferir contagem, vinculação a vistorias/NCs, hashes SHA-256 e abertura real de uma amostra representativa de PDF/fotos/assinaturas.
5. Exercitar restauração e rejeição de acesso cruzado entre empresas.
6. Preparar sincronização dos aplicativos instalados e plano para arquivos gerados durante a janela de transição.
7. Depois de todas as três versões homologadas, efetuar virada controlada e manter o Drive antigo em retenção somente leitura conforme política aprovada.
8. Nunca apagar automaticamente originais ou desvincular fotos ao trocar o backend. Exclusão futura só com autorização específica e plano de recuperação.

## Pré-requisitos que o Júlio deve medir NA VPS antes de dimensionar

- Espaço em disco livre real, filesystem e risco de atingir capacidade dos demais sistemas compartilhados.
- Volume atual de fotos, assinaturas e PDFs e crescimento mensal esperado; limites de upload e necessidade de miniaturas.
- Capacidade de CPU/RAM/IO e rede; separar e nomear volumes de app, PostgreSQL e objetos.
- Política de armazenamento e retenção, criptografia em repouso e transporte TLS.
- Local independente para backups criptografados, credenciais fora do código e teste periódico de restauração.
- RPO/RTO aceitos pela Auditar, alarmes para espaço, erros de upload, falhas de backup e latência.
- Autorização do administrador antes de criar serviços/volumes adicionais na VPS compartilhada.

**Bloqueio:** não publicar fotos/assinaturas reais ou desligar Drive/Apps Script até essas condições serem verificadas e o backend próprio estar implementado e testado.
