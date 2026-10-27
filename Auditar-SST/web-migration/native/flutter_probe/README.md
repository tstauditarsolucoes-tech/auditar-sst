# Sondagem Flutter para o NOVO servidor — SOMENTE leitura, desligada

Este diretório contém um **componente Dart puro** (sem dependências Flutter) que pode ser integrado mais tarde nas compilações de teste do Android e Windows. NÃO está ligado à tela inicial, ao sincronizador, ao login, ao SQLite ou aos builds publicados. Nenhum APK ou EXE novo foi gerado nesta etapa.

## O que a sonda faz
- Desligada por padrão: nenhuma chamada de rede.
- Quando habilitada explicitamente numa versão privada de testes, chama SOMENTE `GET https://HOST-PRIVADO/api/v1/native/handshake` com HTTPS, sem cookies, senhas, tokens, IDs de dispositivo ou informações de clientes.
- Compara serviço, versão e sinalizadores do servidor. Mesmo ao encontrar o backend, devolve `serverFoundButSyncUnavailable` e `canSync == false`.
- Bloqueia HTTP, query string, fragmento, credenciais em URL, URLs do Apps Script, redirecionamentos e respostas incompatíveis.
- **Nunca chama** `device_sync_push`, `device_sync_pull`, login ou qualquer POST; **nunca** marca fila offline como enviada.

## Arquivos
- `native_backend_probe.dart`: cliente GET com `dart:io` e validação estrita.
- `native_backend_probe_test.dart`: testes sintéticos sem rede ou dados reais.

## Como executar APENAS testes Dart locais/CI
```bash
dart run Auditar-SST/web-migration/native/flutter_probe/native_backend_probe_test.dart
```

## Flags para compilação FUTURA e deliberada
O construtor `NativeBackendProbe.fromBuildConfiguration()` conhece duas flags:
```
--dart-define=AUDITAR_SST_NATIVE_PROBE_ENABLED=true
--dart-define=AUDITAR_SST_NATIVE_PROBE_URL=https://HOST-PRIVADO-EXCLUSIVO
```
Essas flags **não fazem nada sozinhas**: ainda seria necessário chamar o cliente explicitamente numa UI de testes, após revisão. Nunca inserir endereço real ou segredos no repositório público. Não usar o domínio ocupado `tst.auditarsolucoes.com.br` sem autorização; não trocar `management_panel_endpoint` ou a configuração do Apps Script.

## O que falta para um aplicativo realmente conectado
1. Implementar autenticação específica para clientes nativos, com sessões/tokens revogáveis e perfis por empresa. Os cookies/CSRF da Web NÃO devem ser reutilizados sem projeto e testes.
2. Implementar contratos versionados de **dados NOVOS** (não importar legado), upload seguro de fotos e assinaturas, histórico e permissões.
3. Criar outbox independente e offline-first com ACK após commit, regras de conflito, idempotência, quotas e telemetria minimizada.
4. Somente então integrar a nova API nas telas e compilações de Android/Windows, testando o ciclo real nos dois dispositivos.
5. Manter o sistema anterior preservado e utilizável. Não eliminar arquivos legados.

**Sondagem conectada não significa aplicativo pronto, e não autoriza migração de dados nem publicação.**


## Atualização: sessão nativa de backend, mas aplicativo AINDA não conectado

O servidor tem o módulo opt-in `nativeAuthService.mjs` com login/consulta/logout para futura utilização por clientes nativos novos, token de 30 minutos e revogação, na migração de esquema 013. Esse código NÃO é importado pelo Flutter atual e **não autoriza** acessar dados de negócio, NC, fotos ou fila offline. Esta sonda continua um GET desativado por padrão; não colocar senha/credencial/token em código Dart ou `--dart-define`. O uso de secure storage e fluxo nativo completo exige nova etapa específica com testes físicos.
