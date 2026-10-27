import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { ApiError, createNcService } from './ncService.mjs';

/**
 * Auth NOVA opcional, injetada internamente na homologacao.
 * Sem authService e sem resolvePrincipal, nao ha nenhuma rota de negocios livre.
 * NUNCA montar resolvePrincipal a partir de headers x-company-id/x-role.
 */
export function createApp({pool, authService, resolvePrincipal} = {}) {
  if (authService && resolvePrincipal) {
    throw new Error('Nao misturar autenticador real com resolver de teste');
  }
  const ncService=createNcService(pool);
  return createServer(async (req,res)=>{
    const pathname=new URL(req.url || '/', 'http://localhost').pathname;
    res.setHeader('Content-Type','application/json; charset=utf-8');
    res.setHeader('Cache-Control','no-store');
    res.setHeader('X-Content-Type-Options','nosniff');
    res.setHeader('Referrer-Policy','no-referrer');
    function send(status,data) {
      res.writeHead(status);
      res.end(JSON.stringify(data));
    }
    async function readJson() {
      const type=req.headers['content-type']||'';
      if (!/^application\/json(?:;|$)/i.test(type)) {
        throw new ApiError(415,'JSON_REQUIRED','JSON obrigatorio');
      }
      const chunks=[];
      let length=0;
      for await (const chunk of req) {
        length+=chunk.length;
        if (length>8192) throw new ApiError(413,'TOO_LARGE','JSON muito grande');
        chunks.push(chunk);
      }
      let body;
      try {body=JSON.parse(Buffer.concat(chunks).toString('utf8'));}
      catch {throw new ApiError(400,'INVALID_JSON','JSON invalido');}
      if (!body || typeof body!=='object' || Array.isArray(body)) {
        throw new ApiError(400,'INVALID_JSON','Objeto JSON esperado');
      }
      return body;
    }

    try {
      if (pathname==='/api/v1/health' && req.method==='GET') {
        send(200,{ok:true,service:'auditar-sst-web',environment:'homologacao-isolada',
          productionDataConnected:false});
        return;
      }

      const authPath=pathname.startsWith('/api/v1/auth/');
      if (authPath && ['GET','POST'].includes(req.method)) {
        if (!authService) {
          send(401,{ok:false,code:'UNAUTHENTICATED'});
          return;
        }
        if (pathname==='/api/v1/auth/login' && req.method==='POST') {
          const result=await authService.login(req,await readJson());
          res.setHeader('Set-Cookie',result.cookie);
          send(200,result.body);
          return;
        }
        if (pathname==='/api/v1/auth/session' && req.method==='GET') {
          send(200,await authService.session(req));
          return;
        }
        if (pathname==='/api/v1/auth/companies' && req.method==='GET') {
          send(200,await authService.companies(req));
          return;
        }
        if (pathname==='/api/v1/auth/company' && req.method==='POST') {
          const body=await readJson();
          send(200,await authService.switchCompany(req,body.companyId));
          return;
        }
        if (pathname==='/api/v1/auth/logout' && req.method==='POST') {
          const result=await authService.logout(req);
          res.setHeader('Set-Cookie',result.cookie);
          send(200,result.body);
          return;
        }
      }

      const ncCollection=pathname==='/api/v1/nonconformities';
      const ncPath=pathname.match(/^\/api\/v1\/nonconformities\/([a-f0-9-]{36})\/(events|correction|decision)$/i);
      if ((ncCollection||ncPath) && ['GET','POST'].includes(req.method)) {
        const resolver=authService
          ? authService.resolvePrincipal.bind(authService)
          : resolvePrincipal;
        const principal=typeof resolver==='function' ? await resolver(req) : null;
        if (!principal) {
          send(401,{ok:false,code:'UNAUTHENTICATED'});
          return;
        }
        // Com cookies de sessao, toda escrita exige Origin correto e CSRF.
        // O resolver injetado para testes legados NAO existe no container real.
        if (req.method==='POST' && authService) authService.requireMutation(req);

        if (ncCollection && req.method==='GET') {
          send(200,{items:await ncService.list(principal)});
          return;
        }
        if (ncPath && ncPath[2]==='events' && req.method==='GET') {
          send(200,{items:await ncService.events(principal,ncPath[1])});
          return;
        }
        if (req.method==='POST') {
          const body=await readJson();
          if (ncCollection) {
            send(201,{item:await ncService.create(principal,body)});
            return;
          }
          if (ncPath?.[2]==='correction') {
            send(200,{item:await ncService.reportCorrection(principal,ncPath[1],body)});
            return;
          }
          if (ncPath?.[2]==='decision') {
            send(200,{item:await ncService.decideCorrection(principal,ncPath[1],body)});
            return;
          }
        }
      }
      send(404,{ok:false,code:'NOT_IMPLEMENTED'});
    } catch (error) {
      if (error instanceof ApiError) {
        send(error.status,{ok:false,code:error.code,message:error.message});
      } else {
        send(500,{ok:false,code:'INTERNAL_ERROR'});
      }
    }
  });
}

if (process.argv[1] && resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const port=Number(process.env.PORT||3000);
  if (!Number.isInteger(port)||port<1||port>65535) throw new Error('PORT invalida');
  // ENTRYPOINT ainda SEM autenticacao/banco em Docker: fail-closed.
  // A ativacao exige duas contas DB restritas, HTTPS e revisao de seguranca.
  createApp().listen(port,'0.0.0.0');
}
