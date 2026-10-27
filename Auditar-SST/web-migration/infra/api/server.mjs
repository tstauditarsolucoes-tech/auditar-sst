import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { ApiError, createNcService } from './ncService.mjs';

/**
 * Somente homologacao: o HTTP exige resolvePrincipal autenticado injetado pelo
 * FUTURO modulo de sessao. Sem injetor nao existe login nem acesso a NC.
 * JAMAIS confiar em x-company-id, x-role ou outros headers do navegador.
 */
export function createApp({ pool, resolvePrincipal } = {}) {
  const service = createNcService(pool);
  return createServer(async (req, res) => {
    const pathname = new URL(req.url || '/', 'http://localhost').pathname;
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Content-Type-Options', 'nosniff');
    res.setHeader('Referrer-Policy', 'no-referrer');
    function send(status, data) {
      res.writeHead(status);
      res.end(JSON.stringify(data));
    }

    try {
      if (req.method === 'GET' && pathname === '/api/v1/health') {
        send(200, {
          ok: true,
          service: 'auditar-sst-web',
          environment: 'homologacao-isolada',
          productionDataConnected: false,
        });
        return;
      }

      const ncCollection = pathname === '/api/v1/nonconformities';
      const ncPath = pathname.match(/^\/api\/v1\/nonconformities\/([a-f0-9-]{36})\/(events|correction|decision)$/i);
      if ((ncCollection || ncPath) &&
          (req.method === 'GET' || req.method === 'POST')) {
        // Nenhuma sessao real existe nesta fase; falha fechada.
        const principal = typeof resolvePrincipal === 'function'
          ? await resolvePrincipal(req)
          : null;
        if (!principal) {
          send(401, {ok:false,code:'UNAUTHENTICATED'});
          return;
        }
        if (ncCollection && req.method === 'GET') {
          send(200, {items:await service.list(principal)});
          return;
        }
        if (ncPath && ncPath[2] === 'events' && req.method === 'GET') {
          send(200, {items:await service.events(principal,ncPath[1])});
          return;
        }
        if (req.method === 'POST') {
          const contentType = req.headers['content-type'] || '';
          if (!/^application\/json(?:;|$)/i.test(contentType)) {
            send(415, {ok:false,code:'JSON_REQUIRED'});
            return;
          }
          const chunks = [];
          let length = 0;
          for await (const chunk of req) {
            length += chunk.length;
            if (length > 8192) throw new ApiError(413,'TOO_LARGE','JSON muito grande');
            chunks.push(chunk);
          }
          let body;
          try { body = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
          catch { throw new ApiError(400,'INVALID_JSON','JSON invalido'); }
          if (!body || typeof body !== 'object' || Array.isArray(body)) {
            throw new ApiError(400,'INVALID_JSON','Objeto JSON esperado');
          }
          if (ncCollection) {
            send(201, {item:await service.create(principal,body)});
            return;
          }
          if (ncPath?.[2] === 'correction') {
            send(200, {item:await service.reportCorrection(principal,ncPath[1],body)});
            return;
          }
          if (ncPath?.[2] === 'decision') {
            send(200, {item:await service.decideCorrection(principal,ncPath[1],body)});
            return;
          }
        }
      }
      send(404, {ok:false,code:'NOT_IMPLEMENTED'});
    } catch (error) {
      if (error instanceof ApiError) {
        send(error.status,{ok:false,code:error.code,message:error.message});
      } else {
        // Oculta conexao, SQL e outros detalhes internos.
        send(500,{ok:false,code:'INTERNAL_ERROR'});
      }
    }
  });
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const port = Number(process.env.PORT || 3000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('PORT invalida');
  }
  // Sem auth injetada: a versao instalada so disponibiliza o health.
  createApp().listen(port, '0.0.0.0');
}
