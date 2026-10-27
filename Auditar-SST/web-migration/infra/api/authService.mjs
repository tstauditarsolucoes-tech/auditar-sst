/**
 * Autenticacao NOVA para WEB em homologacao isolada.
 * Nao le nem substitui login atual Flutter / Google Apps Script.
 * authPool: conta PostgreSQL dedicada, sem SUPERUSER e sem acesso a NCs.
 */
import { randomBytes, createHash, scrypt, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';
import { ApiError } from './ncService.mjs';

const scryptAsync = promisify(scrypt);
const COOKIE = '__Host-auditar_sst';
const TTL_SECONDS = 8 * 60 * 60;
const TOKEN_RE = /^[A-Za-z0-9_-]{43}$/;
const VERIFIER_RE = /^scrypt\$(131072)\$(8)\$(1)\$([0-9a-f]{32})\$([0-9a-f]{128})$/;
const LOGIN_ERROR = 'Credenciais invalidas ou conta sem acesso';
// Verificador ficticio para consumir KDF mesmo quando email nao existe.
const DUMMY_VERIFIER = 'scrypt$131072$8$1$8ee14d963363a557534aaeee01e41a11$9341afbb464041474db2f3c691b19572efb22a62c5df3b0936a826982c052627bc7b7c3398738a44de51ced864541685a0f186b61f09a68cec5b2589d099d7ec';
const HEX_SHA256 = /^[0-9a-f]{64}$/;

export function sessionCookie(token, secure = true) {
  if (!TOKEN_RE.test(token)) throw new ApiError(500, 'SESSION_ERROR', 'Token de sessao invalido');
  // __Host exige Path=/, Secure e ausencia de Domain.
  if (!secure) throw new ApiError(503, 'HTTPS_REQUIRED', 'Login exige HTTPS');
  return COOKIE + '=' + token +
    '; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=' + TTL_SECONDS;
}
export function clearSessionCookie() {
  return COOKIE + '=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0';
}
export function readSessionCookie(req) {
  const raw = req?.headers?.cookie;
  if (typeof raw !== 'string' || raw.length > 4096) return null;
  for (const part of raw.split(';')) {
    const [name, ...parts] = part.trim().split('=');
    const value = parts.join('=');
    if (name === COOKIE && TOKEN_RE.test(value)) return value;
  }
  return null;
}
function sha256(token) {
  return createHash('sha256').update(token,'utf8').digest('hex');
}
export function csrfForToken(token) {
  if (!TOKEN_RE.test(token)) throw new Error('Token invalido');
  return createHash('sha256').update('auditar-sst-csrf-v1:' + token).digest('base64url');
}
function sameSafe(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  return timingSafeEqual(Buffer.from(a,'utf8'),Buffer.from(b,'utf8'));
}
export function requireOrigin(req, allowedOrigin) {
  if (!allowedOrigin || req?.headers?.origin !== allowedOrigin) {
    throw new ApiError(403,'ORIGIN_DENIED','Origem nao autorizada');
  }
}
export function requireCsrf(req, token) {
  const provided = req?.headers?.['x-csrf-token'];
  if (!token || !sameSafe(provided,csrfForToken(token))) {
    throw new ApiError(403,'CSRF_DENIED','Protecao de formulario invalida');
  }
}

export async function hashPassword(password) {
  if (typeof password !== 'string' || password.length < 12 || password.length > 256) {
    throw new ApiError(400,'WEAK_PASSWORD','Senha deve ter entre 12 e 256 caracteres');
  }
  const salt = randomBytes(16);
  const key = await scryptAsync(password, salt, 64, {
    N:131072,r:8,p:1,maxmem:268435456,
  });
  return 'scrypt$131072$8$1$'+salt.toString('hex')+'$'+key.toString('hex');
}
export async function verifyPassword(password, verifier) {
  if (typeof password !== 'string' || password.length > 256) return false;
  const match = typeof verifier === 'string' ? verifier.match(VERIFIER_RE) : null;
  if (!match) return false;
  const salt = Buffer.from(match[4],'hex');
  const expected = Buffer.from(match[5],'hex');
  const actual = await scryptAsync(password,salt,64,{
    N:131072,r:8,p:1,maxmem:268435456,
  });
  return timingSafeEqual(actual,expected);
}

/** role de autenticacao isolada; nunca superuser ou mesma conta de dados NC. */
async function withAuth(pool, fn) {
  if (!pool || typeof pool.connect !== 'function') {
    throw new ApiError(503,'AUTH_UNAVAILABLE','Autenticacao nao configurada');
  }
  const client=await pool.connect();
  let started=false;
  try {
    await client.query('BEGIN');
    started=true;
    await client.query('SET LOCAL ROLE sst_auth_runtime');
    const value=await fn(client);
    await client.query('COMMIT');
    return value;
  } catch (error) {
    if (started) { try {await client.query('ROLLBACK');} catch {} }
    throw error;
  } finally { client.release(); }
}

export function createAuthService({pool, allowedOrigin, secureCookies = true}={}) {
  if (!allowedOrigin || !allowedOrigin.startsWith('https://') || !secureCookies) {
    throw new Error('Auth requer Origin HTTPS fixo e cookie Secure');
  }
  const getToken = req => readSessionCookie(req);
  return {
    async login(req, {email,password}={}) {
      requireOrigin(req,allowedOrigin);
      if (typeof email !== 'string' || email.length < 5 || email.length > 254 ||
          typeof password !== 'string' || password.length > 256) {
        throw new ApiError(401,'LOGIN_FAILED',LOGIN_ERROR);
      }
      const normalized=email.trim().toLowerCase();
      const found=await withAuth(pool,async db=>(await db.query(
        'SELECT u.id,u.display_name,u.active,a.password_verifier FROM sst.app_user u '+
        'JOIN sst.auth_credential a ON a.user_id=u.id '+
        'WHERE lower(u.email)=$1 LIMIT 1',[normalized],
      )).rows[0] || null);
      // Nunca retornar o hash, senha ou distincao entre inexistente/invalido.
      const acceptedPassword = await verifyPassword(password,found?.password_verifier || DUMMY_VERIFIER);
      if (!found || !found.active || !acceptedPassword) {
        throw new ApiError(401,'LOGIN_FAILED',LOGIN_ERROR);
      }
      const membership=await withAuth(pool,async db=>(await db.query(
        'SELECT m.company_id,m.role FROM sst.user_company_role m '+
        'JOIN sst.company c ON c.id=m.company_id '+
        'WHERE m.user_id=$1 AND m.active AND c.status=\'ativa\' '+
        'ORDER BY m.company_id LIMIT 1',[found.id],
      )).rows[0]||null);
      if (!membership) throw new ApiError(401,'LOGIN_FAILED',LOGIN_ERROR);
      const token=randomBytes(32).toString('base64url');
      const tokenHash=sha256(token);
      if (!HEX_SHA256.test(tokenHash)) throw new Error('Hash invalido');
      await withAuth(pool, db=>db.query(
        'INSERT INTO sst.auth_session(token_hash,user_id,company_id,expires_at) '+
        "VALUES ($1,$2,$3,now()+interval '8 hours')",
        [tokenHash,found.id,membership.company_id],
      ));
      return {cookie:sessionCookie(token),body:{
        ok:true,user:{id:found.id,name:found.display_name},
        companyId:membership.company_id,role:membership.role,
        csrfToken:csrfForToken(token),
      }};
    },
    async resolvePrincipal(req) {
      const token=getToken(req);
      if (!token) return null;
      return withAuth(pool,async db=>{
        const result=await db.query(
          'SELECT s.user_id,s.company_id,m.role,u.display_name '+
          'FROM sst.auth_session s '+
          'JOIN sst.app_user u ON u.id=s.user_id '+
          'JOIN sst.user_company_role m ON m.company_id=s.company_id AND m.user_id=s.user_id '+
          'JOIN sst.company c ON c.id=s.company_id '+
          'WHERE s.token_hash=$1 AND s.revoked_at IS NULL AND s.expires_at>now() '+
          "AND u.active AND m.active AND c.status='ativa' LIMIT 1",
          [sha256(token)],
        );
        const row=result.rows[0];
        return row ? {userId:row.user_id,companyId:row.company_id,role:row.role,name:row.display_name}:null;
      });
    },
    requireMutation(req) {
      requireOrigin(req,allowedOrigin);
      requireCsrf(req,getToken(req));
    },
    async session(req) {
      const p=await this.resolvePrincipal(req);
      if (!p) throw new ApiError(401,'UNAUTHENTICATED','Sessao nao verificada');
      return {ok:true,user:{id:p.userId,name:p.name},companyId:p.companyId,
        role:p.role,csrfToken:csrfForToken(getToken(req))};
    },
    async companies(req) {
      const p=await this.resolvePrincipal(req);
      if (!p) throw new ApiError(401,'UNAUTHENTICATED','Sessao nao verificada');
      const rows=await withAuth(pool,async db=>(await db.query(
        'SELECT m.company_id,c.name,m.role FROM sst.user_company_role m '+
        'JOIN sst.company c ON c.id=m.company_id '+
        "WHERE m.user_id=$1 AND m.active AND c.status='ativa' ORDER BY c.name",
        [p.userId],
      )).rows);
      return {items:rows};
    },
    async switchCompany(req, companyId) {
      this.requireMutation(req);
      const p=await this.resolvePrincipal(req);
      if (!p) throw new ApiError(401,'UNAUTHENTICATED','Sessao nao verificada');
      if (typeof companyId !== 'string' || !/^[0-9a-f-]{36}$/i.test(companyId)) {
        throw new ApiError(400,'INVALID_COMPANY','Empresa invalida');
      }
      const tokenHash=sha256(getToken(req));
      const row=await withAuth(pool,async db=>{
        const membership=await db.query(
          'SELECT m.role FROM sst.user_company_role m JOIN sst.company c ON c.id=m.company_id '+
          "WHERE m.user_id=$1 AND m.company_id=$2 AND m.active AND c.status='ativa'",
          [p.userId,companyId],
        );
        if (!membership.rowCount) throw new ApiError(403,'FORBIDDEN','Sem vinculo com empresa');
        const changed=await db.query(
          'UPDATE sst.auth_session SET company_id=$3 WHERE token_hash=$1 AND user_id=$2 '+
          'AND revoked_at IS NULL AND expires_at>now() RETURNING company_id',
          [tokenHash,p.userId,companyId],
        );
        if (!changed.rowCount) throw new ApiError(401,'UNAUTHENTICATED','Sessao expirada');
        return membership.rows[0];
      });
      return {ok:true,companyId,role:row.role,csrfToken:csrfForToken(getToken(req))};
    },
    async logout(req) {
      this.requireMutation(req);
      const token=getToken(req);
      if (token) await withAuth(pool,db=>db.query(
        'UPDATE sst.auth_session SET revoked_at=now() WHERE token_hash=$1 AND revoked_at IS NULL',
        [sha256(token)],
      ));
      return {cookie:clearSessionCookie(),body:{ok:true}};
    },
  };
}
