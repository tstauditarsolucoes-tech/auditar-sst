# Plano de virada do domínio tst.auditarsolucoes.com.br

**Situação confirmada pelo proprietário em 27/10/2026:** o domínio JÁ ATENDE outro serviço e será substituído futuramente pelo Auditar SST Web. Isto não é autorização para mudar a rota neste momento. Nenhuma ação foi feita na VPS, no Nginx Proxy Manager ou no DNS.

## 1. Regra de segurança

Preparar novo sistema em paralelo, testar em ambiente restrito, preservar configuração e dados do serviço atual, obter autorização expressa e só então trocar o destino do Proxy Host no Nginx Proxy Manager. Nunca apagar contêineres, volumes, certificados ou registros do serviço antigo durante a virada.

## 2. Inventário indispensável do serviço ATUAL

Julio deverá identificar e registrar **fora do Git público**:
- Nome do sistema atualmente publicado em tst.auditarsolucoes.com.br e se é parte da Central Online que os aplicativos Android/Windows ainda usam.
- Proxy Host atual no NPM: origem/hostname interno, porta, cabeçalhos especiais, WebSockets, caminhos personalizados, Access List e certificado TLS.
- Rede Docker e nome do projeto/contêiner que serve o domínio.
- Onde ficam banco, volumes, fotos, assinaturas, relatórios, logs e backups do serviço antigo.
- Quais aplicativos, clientes, técnicos ou integrações dependem da URL atual; contratos Apps Script e endpoints de mídia não devem ser redirecionados por suposição.
- Como restaurar a configuração anterior do NPM e religar o serviço atual sem perda de dados.

**Não enviar senhas, tokens, backups ou dados pessoais ao repositório.** Publicar só instruções sanitizadas.

## 3. Montagem paralela (sem corte)

1. Manter o Proxy Host de tst.auditarsolucoes.com.br intacto.
2. Criar o Auditar SST Web como projeto Docker próprio (por exemplo, auditar-sst-web-hml), com banco/volume próprios e sem host ports.
3. Integrar apenas o contêiner web à rede externa do NPM, conforme compose.npm.example.yml. Não conectar API/banco diretamente ao proxy público.
4. Validar o backend e o frontend por acesso restrito; usar subdomínio exclusivo de homologação apenas se o gestor do DNS/NPM aprovar. **Não presumir que esse subdomínio exista.**
5. Migrar primeiro com dados fictícios; ensaiar migração de cópia anonimizada e restauração dos anexos.
6. Verificar login, empresas, permissões, NC, agenda, chat/tratativas, foto, PDF, relatórios e layout PC/celular.
7. Obter aceite de usuário/gestão e congelar contrato de migração dos aplicativos antigos.

O código atual em infra/ é **somente uma sonda de saúde**; não implementa login ou funcionalidades. Não deve substituir o serviço real.

## 4. Pré-virada — pontos de controle (go/no-go)

- [ ] Sistema web completo e homologado nos dispositivos reais, com SSL, monitoramento, backups e controles por empresa.
- [ ] Central Online e apps Android/Windows testados com o novo backend, sem alteração de sync sem autorização.
- [ ] Inventário de empresas, NCs, vistorias, fotos, assinaturas, PDFs, treinamentos e históricos com contagens e checksums.
- [ ] Exportação final/backup verificado do ambiente antigo, com teste de restauração.
- [ ] Estratégia para novos registros durante a janela (pausa de escrita ou reconciliação auditada), com responsáveis definidos.
- [ ] Plano de reversão exercitado e tempo máximo de interrupção/retorno acordados.
- [ ] Configuração antiga do Proxy Host salva em local privado (destino, portas, TLS e políticas).
- [ ] Aviso aos usuários sobre a janela e aceite expresso do proprietário.

Se qualquer item crítico falhar, **NÃO VIRAR O DOMÍNIO**.

## 5. Virada assistida (somente com autorização)

1. Confirmar backups e integridade imediatamente antes do corte.
2. Aplicar último delta aprovado e, se necessário, bloquear novas escritas no serviço antigo de modo controlado.
3. No Nginx Proxy Manager, editar o Proxy Host existente de tst.auditarsolucoes.com.br apenas para apontar ao serviço web novo validado (hostname do contêiner web e porta interna 8080). Preservar certificado, política de HTTPS e configuração de segurança.
4. Validar HTTPS, login, isolamento multiempresa, foto, emissão de PDF, erros 4xx/5xx e operações essenciais pelo domínio real.
5. Monitorar e registrar horário, versão, aprovadores e incidências. Manter contêiner/volumes antigos **parados ou em contingência, mas recuperáveis**, conforme plano acordado.

Alteração de DNS pode não ser necessária se o domínio já aponta para o mesmo NPM; confirmar a topologia real antes de decidir.

## 6. Reversão segura

- Restaurar o destino original e as políticas do Proxy Host a partir da cópia validada.
- Garantir que a versão antiga ainda existe com seus volumes e banco íntegros; não usar comandos que apagam volumes.
- Se houve escritas no novo sistema, **não alternar cegamente para o antigo**: registrar essas transações e definir reconciliação para evitar perda/duplicidade.
- Revalidar login, serviços antigos, APIs, fotos e PDFs após retorno.
- Comunicar conclusão/reversão e guardar trilha de auditoria.

## 7. Pendências específicas para confirmar com Julio

1. **Qual serviço está atualmente por trás de tst.auditarsolucoes.com.br?** É o painel atual do Auditar SST, outro projeto ou uma página temporária?
2. O serviço antigo armazena algum dado de cliente próprio ou apenas encaminha para a Central Online?
3. Há possibilidade de criar um subdomínio de homologação privado enquanto a versão nova é desenvolvida?
4. Quem autoriza e executa a troca do Proxy Host e os backups da VPS?

**Estado do projeto:** preparação/CI somente. PR #23 continua DRAFT. Nenhum contêiner instalado no servidor, nenhuma rota do NPM modificada e nenhum dado de produção migrado.
