# Auditar SST Windows v3.30.121 — Candidate
Acesso pela Administração Auditar -> Atividade dos técnicos. Também foi acrescentado atalho para Caixa de entrada dos clientes.
Candidata de supervisão: ativo recentemente, último contato de sessão, filtros de período e produtividade por eventos sincronizados.
GS aditivo: feature_sources/TechnicianSupervisionCloud_v1.gs — Não foi publicado. A Central precisa autorizar e rotear technician_supervision_v1 para technicianSupervisionV1_, revalidando token e ADM no backend.
Ações offline aparecem somente após sincronização; contagem de registros de sync não é produtividade necessariamente única; histórico limitado aos 9999 eventos de auditoria mais recentes.
Outros recursos recomendados (agenda de serviços, alertas de segurança de backup e relatório gerencial PDF formal) permanecem pendentes de implementação específica.
Sem modificações de sincronização, autenticação, banco, fotos, Android, GS de produção. PR DRAFT, nunca fazer merge automaticamente.
