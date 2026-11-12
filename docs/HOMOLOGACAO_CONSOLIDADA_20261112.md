# Auditar SST — homologação consolidada (12/11/2026)

## Escopo real e limites

**Esta é uma branch de homologação, não uma atualização distribuída.**
A montagem é feita a partir do Auditar SST Flutter existente, preservando a
fonte Android/Windows e usando patches aditivos que recusam estruturas inesperadas.
A migração Web/VPS do Júlio **não** está neste pacote.

### Módulos no candidato de montagem
- Entrada única de vistorias Android com Checklist, Ronda Expressa e vistoria
  rápida, sem substituir os formulários existentes.
- Visita Inteligente Android; no Windows, atalho adicional por empresa.
  Resumos são calculados **somente** com Rondas Expressas locais e não incluem
  automaticamente checklists, dados de outras instalações ou a Central.
- Indicadores de rondas e observações: deduplicação por ID/ronda e separação
  entre vistoria concluída e NC efetivamente corrigida.
- Biblioteca offline: extensão de modelos por NR, NR-12 Panificação e atalho de
  consulta com atualização dos indicadores ao retornar. A sincronização de
  materiais recebidos da Central requer homologação própria.
- Central de Relatórios SST: seis entradas, rascunhos locais, PDF revisável;
  fotos maiores, erro explícito para foto/assinatura selecionada mas inacessível.
- CIPA na tela de gestão técnica: triagem, ajuda guiada, assistente para
  **sugestão de pauta** e nome/cargo de membro. A pauta é anterior à reunião,
  não gera ata com decisões, presenças ou assinaturas fictícias.

### Componentes ainda isolados
- **Portal individual de membros da CIPA**: código e CI integrados no
  repositório, porém sem instalação no aplicativo técnico e sem habilitação de
  seu backend. O parâmetro `CIPA_MEMBER_V1_ENABLED` permanece desativado em
  produção. A implantação exige autenticação individual, autorização por
  empresa/mandato/membro e revisão do Apps Script real.
- Fotos da CIPA com armazenamento privado e rascunhos offline persistentes
  são pendentes; nunca compartilhar links públicos de evidências sem avaliação.
- Nenhum código do integrador altera `Code.gs`, `MultiUser.gs`, banco,
  autenticação, sincronização, mídia ou envio de PDFs.

## Critérios para permitir testes com pessoas e dados reais

Apenas se **todos** os controles abaixo forem atendidos:

- [ ] Pipelines Android e Windows concluídos com sucesso no mesmo commit,
  sem ignore de falha e com hash dos artefatos.
- [ ] Certificado de assinatura Android de homologação conhecido e validado.
- [ ] Backup independente dos dados e fotos do aparelho/PC existente,
  com plano de restauração testado.
- [ ] Testar preferencialmente em aparelho/usuário de homologação isolado.
- [ ] Login autorizado e revogação de acesso por cliente testados.
- [ ] Troca de empresa, mandato e técnico não revela dados de outro cliente.
- [ ] Testes de vistorias Ronda/Checklist, envio, reabertura e sincronização
  com registros fictícios e a Central autorizada.
- [ ] Relatórios Padrão Auditar / técnico e fotos antes/depois comparados.
- [ ] PDFs de inspeção com uma e duas fotos, fotos rotacionadas, assinaturas e
  documentos anteriores preservados. Falha de mídia deve ser explícita.
- [ ] Modelos embarcados offline e modelos recebidos online testados
  separadamente; cache, permissão, data/hora de atualização e falhas de rede.
- [ ] CIPA (gestão técnica) aceita somente participantes e atas reais, e o
  assistente de pautas não inventa presença/decisões.
- [ ] Uso offline, volta de tela, fechamento/reabertura, fila de envio,
  sincronização lenta e retries sem registros duplicados.
- [ ] Android 360/412px, letras ampliadas e Windows em janelas diferentes.
- [ ] Sem regressão nos fluxos já usados pelas empresas.
- [ ] Responsável autoriza a distribuição após conferir o relatório de
  homologação e a versão/identidade do pacote.

## Bloqueadores conhecidos

1. **Não declarar corrigidos** os problemas reportados de sincronização
   automática da biblioteca ou recarregamento das telas apenas porque os
   widgets e scripts isolados passaram: necessitam logs e aparelho real.
2. A contagem completa de todas as modalidades de vistoria ainda exige
   conciliação com as fontes e sincronização da Home.
3. Não fazer merge nem implantação de arquivos Apps Script, Centro ADM,
   Firebase, Web/VPS ou regras de acesso do cliente sem autorização.
4. O instalador de homologação pode compartilhar armazenamento por usuário
   com instalações anteriores; **não instalar sobre estação de produção**
   sem migração/backup comprovados. Nome de arquivo não isola base local.

## Implantação
O integrador `tools/integrate_sst_homologation_v1.py` executa patches
aditivos em cópia temporária da aplicação e verifica hashes de arquivos
protegidos a cada etapa. Se algum patch ou teste falhar, o CI **deve abortar
antes do build e da publicação do artefato**. As duas plataformas possuem
pipelines próprios; aprovação em uma não valida a outra.

**Responsabilidade técnica:** as sugestões de NR e o resumo de riscos não
são laudo, prova de conformidade, decisão sobre continuidade do trabalho,
constatação automática de recorrência ou encerramento de NC. Cabe ao TST
verificar e formalizar cada situação.
