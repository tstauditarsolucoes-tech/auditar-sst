# Checklist de entrega ao Julio César Angelim

## Decisões a confirmar antes de codificar o backend real

1. Hospedagem: VPS/dedicado com Node/Docker ou PHP compartilhada? Provedor, SO e acesso SSH? Domínio e SSL?
2. Banco disponível: PostgreSQL ou MySQL? Onde ficará o backup automatizado e como testar restauração?
3. O sistema web será apenas painel cliente/ADM ou também todas as funções de campo (Ronda, vistorias, fotos, DDS, CIPA, relatórios)?
4. Offline web é obrigatório no primeiro lançamento ou pode ser fase posterior?
5. Qual será a estratégia para interoperar com a Central Online Apps Script sem alterar contratos atuais?
6. Armazenamento privado de mídia: manter Hostinger PHP/Drive como ponte ou migrar para object storage? Política de retenção?
7. Quem autoriza migração dos dados reais, quem testa e quem aprova entrada em produção?

## Ordem de execução para a equipe

- [ ] Abrir AUDITORIA_DO_CODIGO.md e verificar referências na branch congelada.
- [ ] Obter o snapshot compilável **sem segredos** (o aplicativo é montado por scripts).
- [ ] Selecionar stack web com base na infraestrutura, não no instalador Android.
- [ ] Revisar e aprovar API_WEB_PROPOSTA.yaml com técnico/ADM e exemplos reais **anonimizados**.
- [ ] Preparar repositórios/ambientes separados de frontend, backend, banco e storage.
- [ ] Implementar login/autorização por empresa; testar ataques via IDs alterados.
- [ ] Implementar primeiro fluxo de NC + tratativa + foto + validação/rejeição.
- [ ] Implementar agenda e dashboard; validar nomenclatura e prioridades.
- [ ] Migrar demais módulos por etapas, com testes de regressão.
- [ ] Ensaiar migração de banco/anexos com snapshot e rollback.
- [ ] Homologar em dispositivos reais; liberar por fase apenas com autorização.

## Alertas

- A API Web proposta não existe hoje; não direcionar URLs /api/v1 ao servidor de produção sem implementação.
- Não copiar AUDITAR_SYNC_KEY, arquivos de configuração, tokens, credenciais ou dados pessoais para GitHub ou frontend.
- Não mover/deletar fotos/assinaturas/Drive; trabalhar com cópias e comprovar hashes.
- Não misturar Gestão EPI: a integração EpiSync.gs é legada, não uma autorização para portar dados do EPI junto.
- Não modificar auth_service.dart, device_sync_service.dart, SQLite, Apps Script ou fluxos de mídia existentes sem aprovação expressa.
- PR #15 do aplicativo permanece DRAFT, e esta preparação de web não exige merge dele.

**Resultado deste pacote:** diagnóstico, arquitetura, plano e contrato inicial. **Não há sistema web funcional, banco migrado, site publicado ou dados pessoais copiados.**
