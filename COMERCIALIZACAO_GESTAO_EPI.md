# Gestão EPI — versão comercial

## Estrutura

A versão comercial é multiempresa (multi-tenant): cada cliente comprador possui um `tenant` próprio, com licença, usuários, dispositivos e arquivo de dados separado no Google Drive.

### Painel Mestre
Acesso exclusivo do proprietário do produto. Permite:
- cadastrar clientes;
- definir código de acesso;
- criar administrador inicial;
- escolher plano;
- definir validade da licença;
- limitar usuários e dispositivos;
- ativar, suspender e renovar licenças;
- bloquear/liberar dispositivos;
- migrar a base antiga para um cliente.

### Cliente
O cliente entra no Campo e na Gestão com:
1. código da empresa;
2. usuário;
3. senha.

Perfis disponíveis:
- `admin`: gestão completa da conta do cliente;
- `campo`: registro de entregas;
- `consulta`: somente leitura.

## Isolamento dos dados

No Drive da conta proprietária será criada a estrutura:

`Gestao EPI Comercial / Clientes / CODIGO - EMPRESA /`

Cada pasta possui:
- `dados.json`: empresas, trabalhadores, EPIs, entregas e estoque;
- `usuarios.json`: usuários daquele cliente.

Um token de cliente contém o `tenantId`; o servidor seleciona a pasta pelo token autenticado, e não por um identificador enviado livremente pelo aplicativo.

## Licenças

Status:
- `trial`: teste;
- `active`: ativa;
- `suspended`: suspensa;
- `expired`: calculada automaticamente quando a validade termina.

O servidor valida a licença em cada login e sincronização.

## Segurança

- A chave central antiga não é mais incluída nos APKs/EXEs comerciais.
- Senhas são armazenadas com salt e hash iterativo; a senha em texto não é salva.
- Sessões são assinadas e expiram.
- Usuários e dispositivos bloqueados deixam de sincronizar.
- A versão Campo permite acesso offline somente por período limitado após uma autenticação online válida.

## Migração segura

A base antiga continua intacta no local anterior. No Painel Mestre:
1. crie primeiro o cliente que receberá a base antiga;
2. abra `Gerenciar`;
3. use `Migrar dados atuais`;
4. confira os totais antes de abandonar a versão antiga.

A versão comercial Android utiliza um identificador de aplicativo novo e pode coexistir com o aplicativo antigo durante a transição.

## Implantação do backend

O arquivo `auditar-epi/backend/Code.gs` precisa substituir o conteúdo do `Código.gs` no projeto Apps Script `Auditar EPI - Central Online` e a implantação Web App deve receber uma nova versão.

O arquivo `auditar-epi/backend/EpiSync.gs` deve ser mantido, pois contém as funções de normalização, estoque e leitura da base antiga usada na migração.
