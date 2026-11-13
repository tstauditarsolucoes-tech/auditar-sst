# Minha CIPA — várias vistorias offline e pendências

Data: 13/11/2026. Escopo: PR #62 sobre PR #61. Aplicativo opcional do integrante, sem alterar a versão instalada do Auditar SST técnico ou o Web/VPS.

## Novas funcionalidades
- Cada nova vistoria avulsa ganha identificação exclusiva e arquivo AES-256-GCM próprio, isolado por usuário, empresa, mandato e membro. Uma nova vistoria não substitui a anterior.
- Uma vistoria programada mantém um rascunho por agendamento.
- Tela **Ver rascunhos no celular** com local, estado incompleto/pronto e avisos quando não pode ser enviado. O integrante pode continuar a mesma vistoria com respostas, fotos e identificação originais.
- Rascunhos avulsos da versão anterior continuam recuperáveis.
- Agendamentos removidos ou sem autorização atual ficam bloqueados e preservados; não são reenquadrados como outro agendamento.
- Sincronização manual, só após login online e confirmação da Central, sem eliminar arquivos em falha ou timeout.
- Arquivos incompatíveis, corrompidos ou expirados recebem aviso e não são apagados silenciosamente.

## Passos simples para o integrante
1. Entre online, autorize o uso offline opcional e defina o PIN.
2. No campo, sem internet, abra os dados salvos com e-mail e PIN.
3. Toque em Fazer vistoria, responda as perguntas, tire até duas fotos e use Guardar e sair.
4. Faça outra vistoria em outro local: ela será guardada separadamente.
5. Em Ver rascunhos no celular, continue os registros incompletos.
6. Com internet, entre novamente no acesso individual e use Enviar vistorias salvas.
7. Consulte a confirmação e a orientação da Central; falhas ficam pendentes para nova tentativa.

## Cuidados e limites
- A consulta offline tem validade de 24 horas; o rascunho pode ser recuperável por até sete dias segundo as regras atuais de leitura local.
- Não existe revogação remota instantânea de um aparelho sem internet. O vínculo precisa ser revalidado online.
- A lista está limitada operacionalmente a até cem arquivos locais; acima disso, pedir suporte em vez de apagar automaticamente.
- Não coletar identificação desnecessária de pessoas nem dados de saúde. Não se aproximar de perigos para tirar fotos.
- Uso offline não envia automaticamente, não aprova conformidade, não assina ata, não registra presença e não encerra ações.
- Sair da conta pode apagar os rascunhos daquele vínculo, mediante confirmação quando há pendências. Fechar apenas o modo offline bloqueia a consulta sem apagar.
- Não há publicação de APK ou implantação do backend nesta etapa.

## Homologação obrigatória
- Duas vistorias avulsas offline permanecem independentes e recuperáveis.
- Reabrir um registro mantém o mesmo identificador, fotos e respostas.
- Agendamento removido não é enviado; o registro permanece protegido.
- Queda de conexão durante o upload não produz duplicidade; novo envio usa identificação original.
- Vínculos de duas empresas permanecem segregados.
- PIN incorreto, expiração do cache e revogação online fecham os dados conforme as regras definidas.
- Testes físicos em Android, revisão LGPD, configuração do servidor real e autorização antes de liberar um piloto.

Status: implementação experimental em PR de rascunho, sem deploy, merge ou APK de produção.
