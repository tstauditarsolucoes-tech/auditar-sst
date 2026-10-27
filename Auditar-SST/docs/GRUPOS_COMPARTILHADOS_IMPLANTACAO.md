# Grupos compartilhados — implantação pendente

O aplicativo mantém os grupos offline e oferece o botão **Compartilhar grupos**.
A sincronização de vistorias/fotos não foi alterada. Grupos, tipo e nome curto
usam um canal separado com a mesma sessão autenticada e permissões por empresa.
Favoritos, empresas recentes e filtros permanecem pessoais por aparelho/usuário.

## Integração para revisão

Não substituir automaticamente os arquivos da Central em produção.
Após autorização de implantação e backup da versão atual:

1. Adicionar um arquivo `CompanyGroupsSync.gs` com o conteúdo do módulo entregue.
2. No `doPost` existente, antes do bloco `device_sync_push`, acrescentar:

```javascript
    if (request.action === 'company_groups_sync_v1') {
      return jsonResponse_(companyGroupsSync_(request));
    }
```

3. Manter o restante dos arquivos, autenticação e rotas existentes.
4. Publicar uma nova versão na implantação existente, após autorização.
5. Na conta Auditar, compartilhar grupos no primeiro aparelho. No segundo,
   usar o mesmo botão para receber os vínculos. Repetir após editar grupos.

A planilha separada `AUDITAR_COMPANY_GROUPS_V1` é criada somente em chamada
com sessão válida. Não há nova tabela/schema no SQLite do aplicativo.
A versão por empresa bloqueia sobrescrita de alterações concorrentes; o
usuário revisa e pode manter pendências ou escolher os vínculos da Central.
Grupos sem empresas vinculadas continuam locais até receberem uma empresa.

## Conferência prática

- Login técnico restrito a uma empresa não recebe dados de outra empresa.
- Conta do portal do cliente não acessa a rota.
- Criar/mover uma empresa no Android; compartilhar e conferir no Windows.
- Editar offline; reabrir e compartilhar após reconectar.
- Alterar em dois aparelhos e conferir a revisão de conflito.
- Renomear/unir grupos; retirar grupo mantendo empresas e registros SST.
- Conferir nome curto, favoritos, recentes e filtros após reabrir.
- No PC, expandir grupos para conferir NCs, ações e treinamentos vencidos.

**A implantação ainda não foi realizada.** Build e testes automatizados não
substituem estas verificações no app e na Central real.
