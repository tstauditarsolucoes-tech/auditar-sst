# Assinatura permanente — Auditar SST Android

Este projeto usa o workflow `.github/workflows/build-v329106-client-portal.yml`
e o script `tools/configure_release_signing_v329122.py`.

## Uma única configuração segura

1. Guarde duas cópias privadas do backup `Auditar-SST-Chave-Permanente-BACKUP.zip`, fora do repositório.
2. GitHub: Settings > Secrets and variables > Actions > New repository secret.
3. Configure os cinco secrets abaixo com os valores do backup privado:
   - `AUDITAR_ANDROID_KEYSTORE_B64`: conteúdo integral de `Auditar-SST-Keystore-Base64.txt`.
   - `AUDITAR_ANDROID_STORE_PASSWORD`: senha de armazenamento.
   - `AUDITAR_ANDROID_KEY_ALIAS`: alias da chave.
   - `AUDITAR_ANDROID_KEY_PASSWORD`: senha da chave.
   - `AUDITAR_ANDROID_SIGNER_SHA256`: impressão digital SHA-256 do certificado.
4. Preserve `AUDITAR_SYNC_KEY`, que já é usado pelo aplicativo. Não substitua esse valor.
5. Depois de cadastrar os secrets, faça um novo commit no workflow ou solicite
   um commit de disparo na branch `feature/client-panel-permissions-v329106`.
   Esse workflow é acionado por mudanças nos arquivos listados em `on.push.paths`.
   Como ele ainda não existe na branch principal, não dependa de `Run workflow`
   no GitHub para iniciá-lo manualmente.
6. Somente distribua um APK quando a execução terminar com sucesso e
   `SAFE_ANDROID_SIGNER_VERIFIED` aparecer nos logs.

Nunca publique o arquivo JKS, senhas, base64 ou o ZIP no repositório, nos logs
ou em uma issue. Não gere uma chave nova em cada compilação.

## Migração da instalação anterior

A chave permanente nova NÃO consegue atualizar in-place aplicativos assinados com
a chave antiga. Antes da primeira troca, confirme e, se necessário, exporte todos
os dados que deseja manter — inclusive registros, mídia e assinaturas — e verifique
a restauração na Central. Apenas após essa verificação, e com ciência de que dados
somente locais podem ser perdidos, faça a única substituição de instalação.

A partir da primeira instalação assinada com esta chave, todas as versões seguintes
devem reutilizar o mesmo JKS, alias e senhas, manter o mesmo `applicationId` e
incrementar o `versionCode`. Assim elas poderão atualizar por cima normalmente.

## Segurança de compilação

O workflow falha fechado quando algum secret está ausente, quando o certificado
do JKS difere do SHA-256 configurado, quando o APK resultante é assinado por
outro certificado ou quando seu package ID é diferente do Auditar SST. Nenhuma
alteração é necessária no GS, na IA do Checklist ou no protocolo de sincronização.
