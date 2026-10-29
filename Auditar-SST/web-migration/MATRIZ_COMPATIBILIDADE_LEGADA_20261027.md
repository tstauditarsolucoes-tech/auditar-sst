# Matriz real de compatibilidade Flutter/Apps Script → Node/PostgreSQL

Data de corte da analise: 27/10/2026. **Nao e liberacao de migracao real.**

O repositorio mantem a sincronizacao historica em `source_overrides/Auditar_SST_v1_5_dashboard/lib/services/device_sync_service.dart`, cujas mudancas **nao foram feitas**. O aplicativo atual envia `device_sync_push` e recebe `device_sync_pull` no Apps Script com versao/cursor, lote de mudancas, exclusoes logicas e confirmacao da fila local. **A API Node NOVA ainda nao implementa esse protocolo.** Trocar a URL diretamente pode gerar perdas, sobrescritas ou duplicacoes.

## Inventario das 16 tabelas sincronizadas pelo aplicativo

| Tabela SQLite do app | Estrutura piloto no PostgreSQL novo | Estado da equivalencia |
| --- | --- | --- |
| `companies` | `sst.company` | Somente parcial, faltam IDs, campos/perfis e vinculos |
| `worksites` | nenhuma | Pendente |
| `sectors` | nenhuma | Pendente |
| `workers` | nenhuma | Pendente |
| `training_controls` | nenhuma | Pendente |
| `training_requirements` | nenhuma | Pendente |
| `checklist_templates` | nenhuma | Pendente |
| `checklist_items` | nenhuma | Pendente |
| `cipa_elections` | nenhuma | Pendente |
| `cipa_candidates` | nenhuma | Pendente |
| `cipa_voters` | nenhuma | Pendente |
| `inspections` | `sst.inspection` | Parcial, exige mapeamento de IDs/campos e revisoes |
| `answers` | nenhuma | Pendente |
| `non_conformities` | `sst.non_conformity` | Parcial, exige mapeamento de NC/eventos/status |
| `action_plans` | nenhuma | Pendente |
| `sst_records` | nenhuma | Pendente |

O projeto piloto tem outras tabelas novas (agenda, tratativas, usuarios/roles, tickets, evidencia) que **nao significam** automaticamente uma importacao equivalente de dados antigos.

## Protecoes explicitas ja existentes no app

- `device_sync_changes`: fila persistente, versoes locais, `dirty`, `deleted`; so marcar como enviado apos confirmacao definitiva de persistencia na nova API.
- `device_sync_server_version`: cursor do servidor atual; **nao reutilizar como cursor PostgreSQL**. Requer namespaces independentes e reconciliacao de versoes.
- `sync_coordinator.dart`: faz sincronizacao automatica recorrente; nenhuma troca silenciosa de transporte ou frequencia.
- Caminhos locais `companies.logo_path`, `workers.aso_path`, `training_controls.certificate_path`, `inspections.technician_signature_path`, `inspections.responsible_signature_path` sao tratados separadamente do payload estruturado; **nao apagá-los nem assumir que foram migrados**.
- O login legado, token local, `management_panel_sync_key` e Apps Script nao devem ser reutilizados como sessao ou chave da nova API.

## Contrato seguro para diagnostico novo — SEM registros reais

Com conta ADM **do ambiente privado novo**, os endpoints da API piloto sao:

- `GET /api/v1/migration/compatibility` — informa que escrita/importacao estao bloqueadas.
- `POST /api/v1/migration/compatibility/check` — aceita **apenas** manifesto de CONTAGENS, limitado a 8 KiB e 16 tabelas. Requer cookie, Origin e token CSRF da nova sessao Web; sem autenticacao retorna 401.

Exemplo FICTICIO de corpo:

```json
{
  "marker": "SST_LEGACY_METADATA_ONLY",
  "source": "legacy-device-sync-v1",
  "platform": "android",
  "tables": [
    {"name": "companies", "count": 3, "pendingDeletes": 0},
    {"name": "inspections", "count": 12, "pendingDeletes": 1}
  ]
}
```

A resposta retorna `BLOCKED_FOR_REAL_SYNC`, `safeToSwitchEndpoint:false`, `writesPerformed:0` e `localQueueAcknowledged:0`. A API rejeita linhas, nomes, fotos, contatos, emails, tokens, IDs de registros e campos inesperados. **Nao copiar dados de clientes para exemplos nem para o repositorio publico.** O endpoint nao consulta nem escreve base legada, e nao importa linhas na base nova.

## O que falta implementar ANTES de conectar Android/Windows

1. Fazer backup verificado do SQLite de cada dispositivo, Apps Script, Sheets, Drive e metadados com inventario por empresa/periodo e cadeia de custodia.
2. Congelar e documentar contrato de 16 tabelas (schema/colunas, IDs, FK, datas, estados e exclusoes), com fixtures sintéticas e comparacao automatizada.
3. Criar o esquema complementar e importador em **transacao e com simulacao/rollback** para dados reais, sem overwrite indiscriminado; migrar tenant/roles e referencias.
4. Implementar protocolo versionado novo com `clientMutationId` estavel, outbox offline independente, ACK idempotente somente apos commit, tombstones e politica de conflito auditavel. Conflitos devem ficar visiveis para conciliacao, sem `replace` cego.
5. Mapear e validar **cada** foto/assinatura/documento por checksums e referencias aos registros; comprovacao de restore completo do PostgreSQL + volume privado.
6. Adaptar Android e Windows por feature flag **desativada por padrao**, mantendo UI e dados locais; conectar apenas ao host HTTPS privado de homologacao e usar conta/sessao próprias. Testar desconexao, religacao, filas longas, duas edicoes no mesmo item e mudanca de empresa.
7. Comparar resultados em paralelo e so depois de aceite formal pensar em desligar Apps Script/Drive e alterar proxy do dominio.

**Decisao atual: nao conectar aplicativos existentes ao backend novo.** Este trabalho entrega mapeamento e testes de diagnostico seguro; a integracao real depende de desenvolvimento e homologacao que ainda nao aconteceram.


## Atualização de 27/10/2026 — Sonda nativa independente (somente leitura)

Foi criado `native/flutter_probe/native_backend_probe.dart`, **sem vínculo com o sincronizador Flutter legado**. O recurso de teste exige flag explícita desligada por padrão, URL HTTPS privada, faz somente GET em `/api/v1/native/handshake` e devolve sempre `canSync=false`. Nenhuma tabela será importada (decisão atual de iniciar Web NOVA vazia), nenhum cursor legado será reaproveitado. Futuro desenvolvimento deve focar novos registros, novas contas e fila nova, sem reaproveitar dados antigos ou apontar a configuração existente para Node. Ver [native/flutter_probe/README.md](native/flutter_probe/README.md).
