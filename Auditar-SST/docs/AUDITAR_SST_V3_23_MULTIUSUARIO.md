# Auditar SST v3.23 — Multiusuário

## Objetivo

Transformar o Auditar SST em um sistema com acesso individual por pessoa, mantendo a mesma conta utilizável no Android e no Windows e preservando o funcionamento offline-first.

## Modelo de acesso

- **Administrador:** acessa todas as empresas, cria e edita usuários e define permissões.
- **Técnico SST:** pode receber acesso a todas as empresas ou somente às empresas selecionadas pelo administrador.
- Vários técnicos podem trabalhar na mesma empresa.
- Um mesmo usuário pode manter sessão no celular e no computador.

## Dados locais

Cada usuário usa um banco SQLite próprio no aparelho/computador (`auditar_sst_<user_id>.db`). Isso evita que uma pessoa que entre no mesmo dispositivo veja o banco local de outra conta.

No primeiro acesso da conta administradora, o banco legado `auditar_sst.db` é migrado/copiado para o banco individual para preservar os dados já existentes.

## Sessão

A sessão local guarda token, identificação do usuário e dispositivo, nunca a senha. Depois do primeiro login, o app pode continuar sendo usado offline. A sincronização volta automaticamente quando houver conexão.

## Central Online / Apps Script

O arquivo `painel_web_google_apps_script/MultiUser.gs` adiciona:

- usuários;
- sessões por dispositivo;
- perfil administrador/técnico;
- permissões por empresa;
- auditoria de eventos de usuário;
- sincronização filtrada por empresa;
- identificação do usuário que enviou o registro.

O `Code.gs` é alterado pelo `tools/patch_multiuser.py` para aceitar `authToken` nos clientes v3.23.

## Compatibilidade com v3.22

A v3.23 mantém temporariamente a `AUDITAR_SYNC_KEY` para que instalações 3.22 existentes não parem de funcionar durante a migração. Clientes v3.23 enviam o token da sessão e o servidor aplica as permissões individuais.

Essa compatibilidade é temporária: depois que todos os dispositivos forem migrados, a evolução recomendada é desativar o acesso legado baseado apenas na chave compartilhada.

## Segurança

- senhas não são armazenadas em texto simples;
- cada senha recebe salt individual e hash SHA-256 no Apps Script;
- sessões podem ser revogadas;
- sessões expiram após 180 dias;
- técnico não recebe registros de empresas não autorizadas na sincronização multiusuário;
- administrador não pode remover o próprio perfil administrativo/desativar a própria conta pela tela normal.

## Implantação

O APK/Windows da v3.23 só terá login multiusuário funcional após a **Central Online ser atualizada e reimplantada** no Google Apps Script com o `Code.gs` montado pela v3.23 e o novo `MultiUser.gs`.

Antes disso, a tela de login informará que a Central Online precisa ser atualizada.

## Validação

A branch `feature/multiuser-v3.23.0` possui pipelines Android e Windows próprios. A versão não deve substituir a 3.22 até os dois builds passarem e a Central Online ser publicada/testada.
