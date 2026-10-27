# Auditar SST — auditoria de telas, etapa 1 (13/10/2026)

Status: código-fonte preparado na branch Draft, sem publicação de GS ou aplicação sobre dados existentes.

## Ajustes aditivos
- Pesquisa Global limita resultados a empresas ativas autorizadas e filtra trabalhadores, treinamentos, vistorias e registros SST. Registro sem empresa só aparece para ADM.
- A pesquisa revalida acesso ao abrir e encaminha vistorias ao histórico contextualizado pela empresa. Não promete abrir uma vistoria por ID, pois o destino atual não fornece esse contrato.
- Vistorias sem ID de empresa identificável de modo único são omitidas da pesquisa, sem apagar os registros subjacentes.
- Gestão Multempresa lista apenas empresas autorizadas; consulta em grupos de 6, rechecando permissão após carregar e antes de navegar.
- Diagnóstico ADM não exibe versões antigas como se fossem atuais; configuração de endpoint não é chamada conectividade comprovada.

## Escopo e limitações
- Fontes incrementais atualizadas; o próximo build que executar os patches de origem incorporará estas correções. A simples gravação no GitHub não substitui CI/homologação.
- Nenhum serviço de autenticação, sincronização, banco, fotos, mídia, Drive, IA ou GS alterado.
- O backend deve validar o acesso por empresa independentemente da interface. Teste de duas contas e duas obras é obrigatório.
- Não remover módulos só porque apresentam atalhos semelhantes.
