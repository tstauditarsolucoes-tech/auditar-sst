/**
 * Vertical de NCs do NOVO backend SST. Sem alterar Apps Script ou apps Flutter.
 * Recebe SOMENTE principal ja validado pelo futuro modulo de autenticação.
 * O browser nao pode fornecer companyId/role como fonte de autoridade.
 */
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ROLES = new Set(['adm','gestor','tecnico','cliente']);

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export function assertPrincipal(value) {
  if (!value || !UUID.test(value.companyId || '') ||
      !UUID.test(value.userId || '') || !ROLES.has(value.role)) {
    throw new ApiError(401, 'UNAUTHENTICATED', 'Sessao nao verificada');
  }
  return value;
}
function requireRole(principal, roles) {
  if (!roles.includes(principal.role)) throw new ApiError(403, 'FORBIDDEN', 'Perfil sem permissao');
}
function ncId(id) {
  if (!UUID.test(id || '')) throw new ApiError(400, 'INVALID_ID', 'Identificador invalido');
  return id;
}
function textValue(v, max, field, allowEmpty = false) {
  if (typeof v !== 'string') throw new ApiError(400, 'INVALID_INPUT', field + ' deve ser texto');
  const val = v.replace(/\s+/g, ' ').trim();
  if (val.length > max || (!allowEmpty && !val)) {
    throw new ApiError(400, 'INVALID_INPUT', field + ' invalido');
  }
  return val;
}
function riskNumber(v, field) {
  if (!Number.isInteger(v) || v < 1 || v > 5) throw new ApiError(400, 'INVALID_INPUT', field + ' deve ser 1 a 5');
  return v;
}

/**
 * Todas as consultas usam o MESMO cliente/BEGIN, role restrito e tenant local.
 * Pool autenticado da API nao pode ser superuser em producao.
 */
export async function withTenant(pool, verifiedPrincipal, callback) {
  const principal = assertPrincipal(verifiedPrincipal);
  if (!pool || typeof pool.connect !== 'function') {
    throw new ApiError(503, 'DATABASE_UNAVAILABLE', 'Banco nao configurado');
  }
  const client = await pool.connect();
  let began = false;
  try {
    await client.query('BEGIN');
    began = true;
    await client.query('SET LOCAL ROLE sst_app_runtime');
    await client.query('SELECT set_config(\'app.company_id\', $1, true)', [principal.companyId]);
    const result = await callback(client, principal);
    await client.query('COMMIT');
    return result;
  } catch (error) {
    if (began) {
      try { await client.query('ROLLBACK'); } catch { /* preserva erro original */ }
    }
    throw error;
  } finally {
    client.release();
  }
}

export function createNcService(pool) {
  return {
    list(principal) {
      return withTenant(pool, principal, async (db, p) => {
        const result = await db.query(
          'SELECT id, short_title, description, probability, severity, recurring, status, created_at, updated_at ' +
          'FROM sst.non_conformity WHERE company_id=$1 ORDER BY updated_at DESC, id DESC LIMIT 200',
          [p.companyId],
        );
        return result.rows;
      });
    },
    create(principal, payload = {}) {
      return withTenant(pool, principal, async (db, p) => {
        requireRole(p, ['adm','gestor','tecnico']);
        const description = textValue(payload.description, 4000, 'descricao');
        const shortTitle = textValue(payload.shortTitle ?? '', 140, 'nome da NC', true);
        const probability = riskNumber(payload.probability, 'probabilidade');
        const severity = riskNumber(payload.severity, 'severidade');
        if (typeof payload.recurring !== 'undefined' && typeof payload.recurring !== 'boolean') {
          throw new ApiError(400, 'INVALID_INPUT', 'recorrencia invalida');
        }
        const result = await db.query(
          'INSERT INTO sst.non_conformity (company_id,short_title,description,probability,severity,recurring,created_by) ' +
          'VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id,short_title,description,status,created_at',
          [p.companyId,shortTitle,description,probability,severity,payload.recurring ?? false,p.userId],
        );
        await db.query(
          'INSERT INTO sst.nc_treatment_event (company_id,non_conformity_id,kind,message,created_by) ' +
          'VALUES ($1,$2,\'identificada\',\'\',$3)',
          [p.companyId,result.rows[0].id,p.userId],
        );
        return result.rows[0];
      });
    },
    events(principal, id) {
      return withTenant(pool, principal, async (db, p) => {
        ncId(id);
        const nc = await db.query('SELECT id FROM sst.non_conformity WHERE company_id=$1 AND id=$2', [p.companyId,id]);
        if (!nc.rowCount) throw new ApiError(404, 'NOT_FOUND', 'NC indisponivel');
        const result = await db.query(
          'SELECT id,kind,message,created_by,created_at FROM sst.nc_treatment_event ' +
          'WHERE company_id=$1 AND non_conformity_id=$2 ORDER BY created_at,id', [p.companyId,id],
        );
        return result.rows;
      });
    },
    reportCorrection(principal, id, payload = {}) {
      return withTenant(pool, principal, async (db, p) => {
        ncId(id);
        requireRole(p, ['cliente','tecnico','gestor','adm']);
        const message = textValue(payload.message ?? '', 1200, 'observacao', true);
        const state = await db.query(
          'SELECT status FROM sst.non_conformity WHERE company_id=$1 AND id=$2 FOR UPDATE', [p.companyId,id],
        );
        if (!state.rowCount) throw new ApiError(404, 'NOT_FOUND', 'NC indisponivel');
        if (!['aberta','rejeitada'].includes(state.rows[0].status)) {
          throw new ApiError(409, 'INVALID_STATE', 'NC nao aceita nova correcao agora');
        }
        await db.query(
          'INSERT INTO sst.nc_treatment_event (company_id,non_conformity_id,kind,message,created_by) ' +
          'VALUES ($1,$2,\'correcao_informada\',$3,$4)', [p.companyId,id,message,p.userId],
        );
        await db.query(
          'UPDATE sst.non_conformity SET status=\'correcao_informada\',updated_at=now() ' +
          'WHERE company_id=$1 AND id=$2', [p.companyId,id],
        );
        return {id,status:'correcao_informada'};
      });
    },
    decideCorrection(principal, id, payload = {}) {
      return withTenant(pool, principal, async (db, p) => {
        ncId(id);
        requireRole(p, ['tecnico','gestor','adm']);
        if (typeof payload.accepted !== 'boolean') {
          throw new ApiError(400, 'INVALID_INPUT', 'decisao obrigatoria');
        }
        const message = textValue(payload.reason ?? '', 1200, 'motivo', payload.accepted);
        const state = await db.query(
          'SELECT status FROM sst.non_conformity WHERE company_id=$1 AND id=$2 FOR UPDATE', [p.companyId,id],
        );
        if (!state.rowCount) throw new ApiError(404, 'NOT_FOUND', 'NC indisponivel');
        if (state.rows[0].status !== 'correcao_informada') {
          throw new ApiError(409, 'INVALID_STATE', 'Nao ha correcao aguardando validacao');
        }
        const next = payload.accepted ? 'validada' : 'rejeitada';
        await db.query(
          'INSERT INTO sst.nc_treatment_event (company_id,non_conformity_id,kind,message,created_by) ' +
          'VALUES ($1,$2,$3,$4,$5)', [p.companyId,id,next,message,p.userId],
        );
        await db.query(
          'UPDATE sst.non_conformity SET status=$3,updated_at=now() WHERE company_id=$1 AND id=$2',
          [p.companyId,id,next],
        );
        return {id,status:next};
      });
    },
  };
}
