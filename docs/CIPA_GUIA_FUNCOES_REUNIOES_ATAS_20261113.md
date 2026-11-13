# Minha CIPA — Aprender reuniões, iniciar ata e funções do membro

**Data:** 13/11/2026. **Escopo:** PR #65 em sequência às PRs #61–#64. Módulo opcional do integrante (Android), integração de cadastro em homologação. Nenhuma alteração no Auditar SST instalado, no servidor Web/VPS ou na Central de produção.

## Fluxo fácil do integrante

1. Acesse **Minha CIPA** com a conta individual autorizada.
2. Toque em **Entender minha função** para ver atribuições do cargo vinculado ao mandato. O membro não seleciona permissões nem muda a própria função; somente o cadastro oficial confirma presidente, vice, titular, suplente, secretário ou representante nomeado.
3. Toque em **Aprender reunião e ata** para abrir um roteiro com cinco etapas, botões **Próxima etapa** e **Voltar**:
   - preparação de calendário, data, convocação e pauta;
   - abertura da reunião pelo presidente/vice quando cabível, com sugestão de fala;
   - discussão de riscos, ações e decisões efetivas;
   - escolha do secretário de **cada reunião**, registro dos presentes reais e início da minuta;
   - conferência, assinatura pelos presentes e disponibilização das decisões.
4. Na última etapa, **Montar rascunho da ata** oferece um formulário local. O usuário informa tipo, data, local, pauta, assuntos efetivos e decisões; secretário, presentes e prazos podem ser adicionados. A prévia sempre começa com **RASCUNHO EDUCATIVO — NÃO É ATA OFICIAL**.
5. **Copiar** copia a minuta para conferência pela equipe. O aplicativo não cria ata na Central, não gera presença e não assina documentos. Fechar a janela não cria arquivo ou envio automático.

## Cadastro da função

- Na gestão de membros da CIPA já existe o campo **Função na CIPA**, com as opções Presidente, Vice-presidente, Titular, Suplente, Secretário e Membro designado.
- Um patch de homologação torna essa seleção explicativa: exibe a atribuição e o cuidado aplicável da NR-5; diferencia cargo profissional, função e representação; e impede combinações obviamente incompatíveis na tentativa de salvar, como Presidente dos empregados ou Vice-presidente da organização.
- Na tela administrativa de **Cadastrar acesso individual**, o administrador seleciona e confirma a função **já registrada**. Se a escolha for diferente do cadastro oficial do membro, o botão de autorizar fica bloqueado e o responsável é orientado a alterar primeiro o cadastro formal da CIPA.
- O papel exibido na conta é calculado somente a partir do perfil autorizado pelo servidor. Não é permitido conceder cargo ou acesso extra com base em uma escolha local.
- Importante: **Secretário não é cargo automático permanente exigido pela NR-5 atual**. Para cada reunião ordinária ou extraordinária os membros designam quem escreverá a ata, independentemente do rótulo histórico de função do cadastro.

## Base normativa consultada
- NR-5 (5.3.4): Presidente convoca e coordena reuniões; encaminha decisões.
- NR-5 (5.3.5–5.3.6): Vice substitui quando necessário; coordenação e divulgação compartilhadas.
- NR-5 (5.4.5): Presidente dentre representantes da organização e vice escolhido pelos titulares eleitos dos empregados.
- NR-5 (5.6.1–5.6.1.1): reuniões ordinárias normalmente mensais, com exceção facultativa bimestral para certas ME/EPP de graus 1 e 2.
- NR-5 (5.6.3–5.6.3.2): atas assinadas pelos presentes, disponíveis aos integrantes e encaminhamentos divulgados aos trabalhadores.
- NR-5 (5.6.5): secretário designado pelos membros para **cada** reunião.

Fontes: Ministério do Trabalho e Emprego (NR-5) e transcrição da NR-5 atualizada publicada em https://cipa.fsa.br/nr-05 .

## Limitações para homologação

- O exercício não é editor integrado à ata oficial, não gera assinaturas, não grava registro oficial na Central e não certifica presença, mandato ou cumprimento da NR-5.
- Em caso de dúvidas quanto à composição do mandato ou representação, validar formalmente com RH, gestão CIPA e SST.
- As mudanças do cadastro real foram preparadas como patch isolado para uso **apenas em ambiente de homologação**: tools/patch_cipa_role_onboarding_v1.py. Não aplicar na instalação corrente sem planejamento e testes.
- Necessários testes em Android físico, validação em dois mandatos/empresas, revisão da redação jurídica e teste do fluxo completo de atas no sistema administrativo original.

**Status:** PR draft, CI automatizado validado; sem merge, deployment, publicação ou distribuição de APK.
