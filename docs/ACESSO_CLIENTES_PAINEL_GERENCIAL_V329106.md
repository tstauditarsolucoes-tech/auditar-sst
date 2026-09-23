# Auditar SST — acesso restrito de clientes no Painel Gerencial (v3.29.106 / planejamento técnico)

Data da revisão: 22/09/2026. Branch-base: `test-security-consolidation-v329105`.
**Estado:** inspeção do código versionado e especificação de mudança; ainda não implementado, publicado nem homologado. A versão efetivamente implantada no Apps Script pode diferir dos arquivos do repositório.

## Escopo e limites

Manter o Auditar SST exclusivo da Auditar, reutilizar o Painel Gerencial e a Central existentes. Preservar integralmente Android, Windows, login dos técnicos, SQLite, sincronização estruturada, fila de fotos/assinaturas, IA, CIPA, treinamentos, relatórios e dados históricos. Não criar sistema comercial para terceiros nem instalar novo portal/servidor.

## Inventário confirmado no repositório

1. `management_panel_screen.dart` é a interface interna; os patches `patch_internal_management_training_v32969_v3307.py` e `patch_management_panel_refine_v32990_v33017.py` acrescentam informações gerenciais, treinamentos, fotos, assinaturas, indicadores e identidade visual por empresa.
2. O painel HTML existente é publicado pela própria Central: `Code.gs` guarda snapshots na aba `PainelDados` e expõe `doGet?empresa=<token>`. Uma pessoa com esse link pode consultar o snapshot ativo; esse link não é uma conta individual.
3. `MultiUser.gs` possui usuários/sessões e vinculação por `companyIds`, mas o parser de perfil e o cadastro reconhecem apenas `admin` e `tecnico`. Não existe papel `cliente` verificável nesse arquivo.
4. No código versionado de `MultiUser.gs`, `userCanAccessCompany_` aceita identificador de empresa vazio, e a seleção de sincronização inclui registros sem identificador. Essas compatibilidades legadas **não** constituem proteção suficiente para abrir as rotas de sincronização a usuários externos.
5. A auditoria `docs/AUDITORIA_OPERACIONAL_E_SEGURANCA_V329105.md` documenta testes sintéticos, mas não homologa isolamento multiempresa nem a Central publicada.

## Modelo de permissão proposto (negação por padrão)

- `admin_auditar`: configura acesso e permissões; permanece interno.
- `tecnico_auditar`: mantém operações atuais, com empresas autorizadas.
- `cliente_visualizador`: uso **somente no Painel Gerencial web**, nunca na sincronização completa ou ferramentas internas.
- Concessão explícita por ID imutável de empresa, não por nome, CNPJ apresentado na tela ou parâmetro fornecido pelo navegador.
- Permissões separadas, por empresa: `ver_indicadores`, `ver_relatorios_publicados`, `ver_nao_conformidades`, `ver_acoes_corretivas`; `enviar_evidencia_correcao` desligada inicialmente.
- Só mostrar registros publicados/liberados pela Auditar. Não expor CPF, dados médicos, credenciais, logs internos, chaves, anotações privadas nem registros de outras empresas.
- Validação no servidor em **cada** leitura, download, anexo e edição. Não confiar em filtros da interface ou em `companyId` fornecido pelo cliente.
- Registrar concessão/revogação de acesso, abertura de relatório, download e envio de evidência.

## Implantação incremental segura

**Fase A — comparação da Central real (bloqueante):** obter `Code.gs`, `MultiUser.gs` e demais módulos efetivamente publicados, com backup e versão de implantação. Comparar com os artefatos da branch. Identificar endpoints efetivos de mídia e relatório. Nenhuma substituição integral de GS por snapshot antigo.

**Fase B — controle de acesso:** evoluir cadastro existente para papel externo somente-leitura, limitado a empresas atribuídas. Sessão específica para painel ou credencial que não permita uso de endpoints operacionais. Garantir que autenticação e autorização no servidor neguem rotas de sincronização, IA administrativa, usuários, CIPA, Drive e mídia não publicada para o perfil externo. Conta desativada ou empresa removida perde acesso imediatamente.

**Fase C — Painel Gerencial:** conservar o visual e os dados do painel atual. Exibir indicadores, lista de NCs, status/prazo/responsável de ações e relatórios explicitamente publicados. Cada detalhe ou PDF só é entregue após conferência servidor-side de empresa e publicação. Downloads não podem usar URLs públicas permanentes sem autorização.

**Fase D — evidência de correção (opcional):** permitir foto/observação por NC autorizada, guardar como `evidencia_pendente_validacao`, indicar autor/data, manter histórico e enviar à análise do técnico. Nunca marcar uma NC como resolvida pela simples submissão do cliente.

**Fase E — migração do link legado:** antes da entrega a clientes, desabilitar o acesso anônimo baseado somente em `?empresa=<token>` para as empresas migradas. Links antigos devem direcionar ao login ou ser revogados. Não publicar novo login deixando a rota antiga como alternativa sem autenticação.

**Fase F — validação e publicação:** montar artefatos reprodutíveis e comparar hashes do núcleo de autenticação operacional, banco, transportes e sincronização. Publicar a Central com rollback, testar primeiro com empresas fictícias e somente depois autorizar empresa real.

## Matriz mínima de testes

| Cenário | Resultado esperado |
| --- | --- |
| Cliente A lista empresas | Apenas empresa A |
| Cliente A tenta abrir empresa B alterando a URL/ID/JSON | Negação no servidor, inclusive dados, PDFs, imagens e anexos |
| Cliente A chama diretamente as rotas de push/pull e administração | Negação sem dados e sem alteração |
| Cliente A tenta relatório ainda não publicado | Negação |
| Administrador revoga A durante sessão aberta | Próxima chamada é negada |
| Cliente A envia evidência autorizada | Cria pendência rastreável, sem resolver NC automaticamente |
| Cliente B tenta alterar evidência de A | Negação |
| Link legado de empresa migrada | Não fornece dados sem login |
| Técnico existente no Android e Windows | Nenhuma regressão em login, IA, dados, mídia, sincronização e relatórios |
| Rede instável / muitos registros | Sem perda nem duplicação de evidências; pendências identificáveis |

## Critério de aceite

Acesso de cliente só será considerado pronto após integração com **o GS real publicado**, testes de isolamento por duas empresas, logs de permissão e validação prática Android/Windows. Esta documentação não altera execução, dados, credenciais nem implantação.
