import { createServer } from 'node:http';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { ApiError, createNcService } from './ncService.mjs';
import { createInspectionService } from './inspectionService.mjs';
import { createTaskService } from './taskService.mjs';
import { createActionPlanService } from './actionPlanService.mjs';
import { createTrainingService } from './trainingService.mjs';
import { createCipaService } from './cipaService.mjs';
import { createCipaPortalService } from './cipaPortalService.mjs';
import { createCipaPortalMediaService } from './cipaPortalMediaService.mjs';
import { createPortalService } from './portalService.mjs';
import { createEvidenceService } from './evidenceService.mjs';
import { createReportService } from './reportService.mjs';
import { createTrainingReportService } from './trainingReportService.mjs';
import {legacyCompatibilityCapabilities,inspectLegacyManifest} from './legacyCompatibility.mjs';
import {nativeDraftPayload} from './nativeDraftContract.mjs';

/**
 * Auth NOVA opcional, injetada internamente na homologacao.
 * Sem authService e sem resolvePrincipal, nao ha nenhuma rota de negocios livre.
 * NUNCA montar resolvePrincipal a partir de headers x-company-id/x-role.
 */
export function createApp({pool, authService, cipaPortalAuth, nativeAuthService, nativeDraftsEnabled=false, resolvePrincipal, evidenceDir} = {}) {
  if(nativeDraftsEnabled && !nativeAuthService)throw new Error('Rascunho nativo exige sessao nativa verificada');
  if (authService && resolvePrincipal) {
    throw new Error('Nao misturar autenticador real com resolver de teste');
  }
  const ncService=createNcService(pool);
  const inspectionService=createInspectionService(pool);
  const taskService=createTaskService(pool);
  const actionPlanService=createActionPlanService(pool);
  const trainingService=createTrainingService(pool);
  const cipaService=createCipaService(pool);
  const cipaPortal=createCipaPortalService(pool);
  const cipaMedia=createCipaPortalMediaService(pool,evidenceDir);
  const portalService=createPortalService(pool);
  const evidenceService=createEvidenceService(pool,evidenceDir);
  const reportService=createReportService(pool,evidenceDir);
  const trainingReportService=createTrainingReportService(pool);
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
    async function readJson(maxBytes=8192) {
      const type=req.headers['content-type']||'';
      if (!/^application\/json(?:;|$)/i.test(type)) {
        throw new ApiError(415,'JSON_REQUIRED','JSON obrigatorio');
      }
      const chunks=[];
      let length=0;
      for await (const chunk of req) {
        length+=chunk.length;
        if (length>maxBytes) throw new ApiError(413,'TOO_LARGE','JSON muito grande');
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
      // Dedicated credentials: a CIPA member is NEVER a staff/client principal.
      if(pathname.startsWith('/api/v1/cipa-portal/')){
        if(!cipaPortalAuth){send(404,{ok:false,code:'CIPA_PORTAL_DISABLED'});return;}
        const route=pathname.slice('/api/v1/cipa-portal/'.length);
        if(route==='auth/session'&&req.method==='GET'){send(200,await cipaPortalAuth.session(req));return;}
        if(['auth/login','auth/logout','auth/password'].includes(route)&&req.method==='POST'){
          const result=route==='auth/login'?await cipaPortalAuth.login(req,await readJson(1600)):
            route==='auth/password'?await cipaPortalAuth.password(req,await readJson(1600)):await cipaPortalAuth.logout(req);
          res.setHeader('Set-Cookie',result.cookie);send(200,result.body);return;
        }
        const p=await cipaPortalAuth.principal(req);
        if(!p)throw new ApiError(401,'UNAUTHENTICATED','Sessao individual expirada');
        const mediaUpload=route.match(/^mandates\/([0-9a-f-]{36})\/observations$/i);
        const mediaDownload=route.match(/^observations\/([0-9a-f-]{36})\/photo$/i);
        if(mediaDownload&&req.method==='GET'){
          const photo=await cipaMedia.download(p,mediaDownload[1]);
          res.setHeader('Content-Type',photo.mimeType);res.setHeader('Content-Disposition','inline');
          res.writeHead(200);res.end(photo.data);return;
        }
        if(mediaUpload&&req.method==='POST'){
          cipaPortalAuth.mutation(req);
          send(201,await cipaMedia.upload(p,mediaUpload[1],await readJson(3*1024*1024)));return;
        }
        if(route==='mandates'&&req.method==='GET'){send(200,{items:await cipaPortal.mandates(p)});return;}
        const detail=route.match(/^mandates\/([0-9a-f-]{36})$/i);
        if(detail&&req.method==='GET'){send(200,await cipaPortal.get(p,detail[1]));return;}
        const post=route.match(/^mandates\/([0-9a-f-]{36})\/entries$/i);
        const status=route.match(/^actions\/([0-9a-f-]{36})\/status$/i);
        if(req.method==='POST'&&(post||status)){
          cipaPortalAuth.mutation(req);const body=await readJson(12000);
          send(200,{item:post?await cipaPortal.post(p,post[1],body):await cipaPortal.status(p,status[1],body)});return;
        }
        send(404,{ok:false,code:'NOT_FOUND'});return;
      }
      if(pathname.startsWith('/api/v1/cipa-portal-admin/')){
        if(!cipaPortalAuth){send(404,{ok:false,code:'CIPA_PORTAL_DISABLED'});return;}
        const p=authService?await authService.resolvePrincipal(req):resolvePrincipal?await resolvePrincipal(req):null;
        if(!p)throw new ApiError(401,'UNAUTHENTICATED','Sessao da equipe necessaria');
        const route=pathname.slice('/api/v1/cipa-portal-admin/'.length);
        const mediaDownload=route.match(/^observations\/([0-9a-f-]{36})\/photo$/i);
        if(mediaDownload&&req.method==='GET'){
          const photo=await cipaMedia.download(p,mediaDownload[1],true);
          res.setHeader('Content-Type',photo.mimeType);res.setHeader('Content-Disposition','inline');
          res.writeHead(200);res.end(photo.data);return;
        }
        if(route==='accounts'&&req.method==='GET'){send(200,{items:await cipaPortal.accounts(p)});return;}
        const summary=route.match(/^mandates\/([0-9a-f-]{36})\/summary$/i);
        if(summary&&req.method==='GET'){send(200,await cipaPortal.monthlySummary(p,summary[1],new URL(req.url,'http://localhost').searchParams.get('month')));return;}
        const detail=route.match(/^mandates\/([0-9a-f-]{36})$/i);
        if(detail&&req.method==='GET'){send(200,await cipaPortal.adminGet(p,detail[1]));return;}
        const post=route.match(/^mandates\/([0-9a-f-]{36})\/(accounts|link|revoke|reset|actions|entries)$/i);
        const status=route.match(/^actions\/([0-9a-f-]{36})\/status$/i);
        if(req.method==='POST'&&(post||status)){
          if(authService)authService.requireMutation(req);
          const body=await readJson(12000);let item;
          if(status)item=await cipaPortal.status(p,status[1],body,true);
          else if(post[2]==='accounts')item=await cipaPortal.createAccount(p,post[1],body);
          else if(post[2]==='actions')item=await cipaPortal.createAction(p,post[1],body);
          else if(post[2]==='entries')item=await cipaPortal.post(p,post[1],body,true);
          else item=await cipaPortal[post[2]](p,post[1],body);
          send(200,{item});return;
        }
        send(404,{ok:false,code:'NOT_FOUND'});return;
      }
      if (pathname==='/api/v1/health' && req.method==='GET') {
        send(200,{ok:true,service:'auditar-sst-web',environment:'homologacao-isolada',
          productionDataConnected:false});
        return;
      }

      // Criacao NATIVA de rascunhos NOVOS, segundo opt-in INDEPENDENTE.
      // Sem sync Flutter, sem dados legados, sem trocas de empresa ou ACK da fila.
      const nativeCreate=pathname==='/api/v1/native/drafts/inspections';
      const nativeFinding=pathname.match(
        /^\/api\/v1\/native\/drafts\/inspections\/([0-9a-f-]{36})\/findings$/i);
      if(nativeCreate||nativeFinding){
        if(!nativeAuthService||!nativeDraftsEnabled){
          send(404,{ok:false,code:'NATIVE_DRAFTS_DISABLED'});return;
        }
        if(req.method!=='POST'){send(405,{ok:false,code:'METHOD_NOT_ALLOWED'});return;}
        const p=await nativeAuthService.principal(req);
        const body=nativeDraftPayload(await readJson(6200),
          nativeCreate?'inspection':'finding');
        const item=nativeCreate
          ?await inspectionService.create(p,body)
          :await inspectionService.addFinding(p,nativeFinding[1],body);
        send(201,{item,syncEnabled:false,legacyQueueAcknowledged:false});return;
      }

      // Consultas NATIVAS SOMENTE leitura, usando dados NOVOS no tenant do token.
      // Nao aceitar syncPush/syncPull, uploads, escrita ou companyId passado pelo cliente.
      const nativeNcs=pathname==='/api/v1/native/data/nonconformities';
      const nativeInspections=pathname==='/api/v1/native/data/inspections';
      if(nativeNcs||nativeInspections){
        if(!nativeAuthService){send(404,{ok:false,code:'NATIVE_AUTH_DISABLED'});return;}
        if(req.method!=='GET'){send(405,{ok:false,code:'READ_ONLY'});return;}
        const nativePrincipal=await nativeAuthService.principal(req);
        const items=nativeNcs
          ?await ncService.list(nativePrincipal)
          :await inspectionService.list(nativePrincipal);
        send(200,{items,readOnly:true,syncEnabled:false});return;
      }

      // Auth NATIVA opcional: apenas login/me/logout e tokens exclusivos do app.
      // Nenhuma rota de dados/NC/foto aceita este bearer; cookie Web fica separado.
      const nativeLogin=pathname==='/api/v1/native/auth/login';
      const nativeMe=pathname==='/api/v1/native/auth/session';
      const nativeLogout=pathname==='/api/v1/native/auth/logout';
      if(nativeLogin||nativeMe||nativeLogout){
        if(!nativeAuthService){send(404,{ok:false,code:'NATIVE_AUTH_DISABLED'});return;}
        if(nativeLogin&&req.method==='POST'){
          send(200,await nativeAuthService.login(req,await readJson(1200)));return;
        }
        if(nativeMe&&req.method==='GET'){
          send(200,await nativeAuthService.session(req));return;
        }
        if(nativeLogout&&req.method==='POST'){
          send(200,await nativeAuthService.logout(req));return;
        }
        send(405,{ok:false,code:'METHOD_NOT_ALLOWED'});return;
      }

      // Handshake nativo estritamente informativo. NAO autentica, NAO sincroniza,
      // NAO consulta dados de clientes, NAO autoriza troca de endpoint nos apps.
      if(pathname==='/api/v1/native/handshake'&&req.method==='GET'){
        send(200,{
          ok:true,service:'auditar-sst-web',contract:'sst-native-probe-v1',
          apiVersion:1,environment:'homologacao-isolada',
          productionDataConnected:false,
          native:{android:false,windows:false,syncEnabled:false,
            writesEnabled:false,authentication:'not-implemented'},
        });return;
      }

      // Diagnostico da migração: contagens somente, jamais aceitar linhas legadas.
      // Este endpoint NAO e device_sync_pull/push nem muda Apps Script.
      const compatibilityRead=pathname==='/api/v1/migration/compatibility';
      const compatibilityCheck=pathname==='/api/v1/migration/compatibility/check';
      if((compatibilityRead&&req.method==='GET')||
         (compatibilityCheck&&req.method==='POST')){
        const resolver=authService
          ?authService.resolvePrincipal.bind(authService):resolvePrincipal;
        const principal=typeof resolver==='function'?await resolver(req):null;
        if(!principal){send(401,{ok:false,code:'UNAUTHENTICATED'});return;}
        if(compatibilityCheck&&authService)authService.requireMutation(req);
        if(compatibilityRead){
          send(200,legacyCompatibilityCapabilities(principal));return;
        }
        send(200,inspectLegacyManifest(principal,await readJson()));return;
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


      // PDF de vistoria concluida: download autenticado, gerado em memoria.
      const reportPath=pathname.match(/^\/api\/v1\/reports\/inspections\/([a-f0-9-]{36})\/pdf$/i);
      if(reportPath&&req.method==='GET'){
        const resolver=authService?authService.resolvePrincipal.bind(authService):resolvePrincipal;
        const principal=typeof resolver==='function'?await resolver(req):null;
        if(!principal){send(401,{ok:false,code:'UNAUTHENTICATED'});return;}
        const pdf=await reportService.inspectionPdf(principal,reportPath[1]);
        res.setHeader('Content-Type','application/pdf');
        res.setHeader('Content-Disposition','attachment; filename="auditar-sst-vistoria-hml.pdf"');
        res.writeHead(200);
        res.end(pdf);
        return;
      }

      // Minuta PDF nominal de participacao declarada: SEM assinaturas, nao vale como certificado.
      const trainingReport=pathname.match(
        /^\/api\/v1\/reports\/trainings\/([a-f0-9-]{36})\/attendance\.pdf$/i);
      if(trainingReport&&req.method==='GET'){
        const resolver=authService?authService.resolvePrincipal.bind(authService):resolvePrincipal;
        const principal=typeof resolver==='function'?await resolver(req):null;
        if(!principal){send(401,{ok:false,code:'UNAUTHENTICATED'});return;}
        const pdf=await trainingReportService.attendancePdf(principal,trainingReport[1]);
        res.setHeader('Content-Type','application/pdf');
        res.setHeader('Content-Disposition','attachment; filename="auditar-sst-treinamento-minuta-hml.pdf"');
        res.writeHead(200);res.end(pdf);return;
      }

      // Midia de homologacao: nome privado aleatorio, sem links publicos.
      const evidenceCollection=pathname==='/api/v1/evidence';
      const evidenceContent=pathname.match(/^\/api\/v1\/evidence\/([a-f0-9-]{36})\/content$/i);
      if((evidenceCollection||evidenceContent)&&['GET','POST'].includes(req.method)){
        const resolver=authService?authService.resolvePrincipal.bind(authService):resolvePrincipal;
        const principal=typeof resolver==='function'?await resolver(req):null;
        if(!principal){send(401,{ok:false,code:'UNAUTHENTICATED'});return;}
        if(req.method==='POST'&&authService)authService.requireMutation(req);
        if(evidenceCollection&&req.method==='POST'){
          send(201,await evidenceService.upload(principal,await readJson(3*1024*1024)));return;
        }
        if(evidenceCollection&&req.method==='GET'){
          const q=new URL(req.url||'/', 'http://localhost').searchParams;
          send(200,{items:await evidenceService.list(principal,{
            inspectionId:q.get('inspectionId'),nonConformityId:q.get('nonConformityId'),
          })});return;
        }
        if(evidenceContent&&req.method==='GET'){
          const image=await evidenceService.download(principal,evidenceContent[1]);
          res.setHeader('Content-Type',image.mimeType);
          res.setHeader('Content-Disposition','inline');
          res.writeHead(200);
          res.end(image.data);
          return;
        }
      }

      // Portal do Cliente e Central ADM: base NOVA, tenants e papeis da sessao.
      const portalDashboard=pathname==='/api/v1/portal/dashboard';
      const portalThreads=pathname==='/api/v1/portal/threads';
      const portalThread=pathname.match(/^\/api\/v1\/portal\/threads\/([a-f0-9-]{36})(?:\/(messages|close|reopen))?$/i);
      const adminOverview=pathname==='/api/v1/admin/overview';
      const adminTeam=pathname==='/api/v1/admin/team';
      const activityPing=pathname==='/api/v1/activity/ping';
      if ((portalDashboard||portalThreads||portalThread||adminOverview||adminTeam||activityPing)&&['GET','POST'].includes(req.method)) {
        const resolver=authService
          ? authService.resolvePrincipal.bind(authService)
          : resolvePrincipal;
        const principal=typeof resolver==='function'?await resolver(req):null;
        if (!principal) {send(401,{ok:false,code:'UNAUTHENTICATED'});return;}
        if(req.method==='POST'&&authService)authService.requireMutation(req);
        if(portalDashboard&&req.method==='GET'){
          send(200,await portalService.dashboard(principal));return;
        }
        if(portalThreads&&req.method==='GET'){
          send(200,{items:await portalService.threads(principal)});return;
        }
        if(portalThreads&&req.method==='POST'){
          send(201,{item:await portalService.createThread(principal,await readJson())});return;
        }
        if(portalThread&&!portalThread[2]&&req.method==='GET'){
          send(200,await portalService.thread(principal,portalThread[1]));return;
        }
        if(portalThread?.[2]==='messages'&&req.method==='POST'){
          send(200,{item:await portalService.reply(principal,portalThread[1],await readJson())});return;
        }
        if(portalThread?.[2]==='close'&&req.method==='POST'){
          send(200,{item:await portalService.changeStatus(principal,portalThread[1],'close',await readJson())});return;
        }
        if(portalThread?.[2]==='reopen'&&req.method==='POST'){
          send(200,{item:await portalService.changeStatus(principal,portalThread[1],'reopen',await readJson())});return;
        }
        if(adminOverview&&req.method==='GET'){
          send(200,await portalService.overview(principal));return;
        }
        if(adminTeam&&req.method==='GET'){
          send(200,{items:await portalService.team(principal)});return;
        }
        if(activityPing&&req.method==='POST'){
          await readJson();
          send(200,await portalService.ping(principal));return;
        }
      }

      // CIPA Web: mandato, composicao e reunioes SOMENTE na base ficticia de homologacao.
      const cipaCollection=pathname==='/api/v1/cipa/mandates';
      const cipaMandatePath=pathname.match(
        /^\/api\/v1\/cipa\/mandates\/([a-f0-9-]{36})(?:\/(members|meetings|status))?$/i,
      );
      const cipaMeetingPath=pathname.match(
        /^\/api\/v1\/cipa\/meetings\/([a-f0-9-]{36})\/status$/i,
      );
      if((cipaCollection||cipaMandatePath||cipaMeetingPath)&&['GET','POST'].includes(req.method)){
        const resolver=authService
          ?authService.resolvePrincipal.bind(authService):resolvePrincipal;
        const principal=typeof resolver==='function'?await resolver(req):null;
        if(!principal){send(401,{ok:false,code:'UNAUTHENTICATED'});return;}
        if(req.method!=='GET'&&authService)authService.requireMutation(req);
        if(cipaCollection&&req.method==='GET'){
          send(200,{items:await cipaService.list(principal)});return;
        }
        if(cipaCollection&&req.method==='POST'){
          send(201,{item:await cipaService.create(principal,await readJson())});return;
        }
        if(cipaMandatePath&&!cipaMandatePath[2]&&req.method==='GET'){
          send(200,await cipaService.get(principal,cipaMandatePath[1]));return;
        }
        if(cipaMandatePath?.[2]==='members'&&req.method==='POST'){
          send(201,{item:await cipaService.addMember(principal,cipaMandatePath[1],await readJson())});return;
        }
        if(cipaMandatePath?.[2]==='meetings'&&req.method==='POST'){
          send(201,{item:await cipaService.addMeeting(principal,cipaMandatePath[1],await readJson())});return;
        }
        if(cipaMandatePath?.[2]==='status'&&req.method==='POST'){
          send(200,{item:await cipaService.mandateStatus(principal,cipaMandatePath[1],await readJson())});return;
        }
        if(cipaMeetingPath&&req.method==='POST'){
          send(200,{item:await cipaService.decideMeeting(principal,cipaMeetingPath[1],await readJson())});return;
        }
      }

      // Treinamentos, DDS e Integracao: apenas registros sintéticos no banco NOVO.
      const trainingCollection=pathname==='/api/v1/training-sessions';
      const trainingPath=pathname.match(
        /^\/api\/v1\/training-sessions\/([a-f0-9-]{36})(?:\/(status|participants))?$/i,
      );
      if ((trainingCollection||trainingPath)&&['GET','POST','PATCH'].includes(req.method)){
        const resolver=authService
          ?authService.resolvePrincipal.bind(authService):resolvePrincipal;
        const principal=typeof resolver==='function'?await resolver(req):null;
        if(!principal){send(401,{ok:false,code:'UNAUTHENTICATED'});return;}
        if(req.method!=='GET'&&authService)authService.requireMutation(req);
        if(trainingCollection&&req.method==='GET'){
          const q=new URL(req.url||'/', 'http://localhost').searchParams;
          send(200,{items:await trainingService.list(principal,q.get('kind'))});return;
        }
        if(trainingCollection&&req.method==='POST'){
          send(201,{item:await trainingService.create(principal,await readJson())});return;
        }
        if(trainingPath&&!trainingPath[2]&&req.method==='GET'){
          send(200,await trainingService.get(principal,trainingPath[1]));return;
        }
        if(trainingPath&&!trainingPath[2]&&req.method==='PATCH'){
          send(200,{item:await trainingService.edit(principal,trainingPath[1],await readJson())});return;
        }
        if(trainingPath?.[2]==='participants'&&req.method==='POST'){
          send(201,{item:await trainingService.addParticipant(principal,trainingPath[1],await readJson())});
          return;
        }
        if(trainingPath?.[2]==='status'&&req.method==='POST'){
          send(200,{item:await trainingService.status(principal,trainingPath[1],await readJson())});return;
        }
      }

      // Planos de acao vinculados a NCs (homologacao privada, banco NOVO).
      const planCollection=pathname==='/api/v1/action-plans';
      const planPath=pathname.match(
        /^\/api\/v1\/action-plans\/([a-f0-9-]{36})(?:\/(status))?$/i,
      );
      if ((planCollection||planPath)&&['GET','POST','PATCH'].includes(req.method)) {
        const resolver=authService
          ?authService.resolvePrincipal.bind(authService):resolvePrincipal;
        const principal=typeof resolver==='function'?await resolver(req):null;
        if(!principal){send(401,{ok:false,code:'UNAUTHENTICATED'});return;}
        if(req.method!=='GET'&&authService)authService.requireMutation(req);
        if(planCollection&&req.method==='GET'){
          const q=new URL(req.url||'/', 'http://localhost').searchParams;
          send(200,{items:await actionPlanService.list(principal,q.get('nonConformityId'))});
          return;
        }
        if(planCollection&&req.method==='POST'){
          send(201,{item:await actionPlanService.create(principal,await readJson())});
          return;
        }
        if(planPath&&!planPath[2]&&req.method==='GET'){
          send(200,await actionPlanService.get(principal,planPath[1]));return;
        }
        if(planPath&&!planPath[2]&&req.method==='PATCH'){
          send(200,{item:await actionPlanService.edit(principal,planPath[1],await readJson())});
          return;
        }
        if(planPath?.[2]==='status'&&req.method==='POST'){
          send(200,{item:await actionPlanService.status(principal,planPath[1],await readJson())});
          return;
        }
      }

      // Agenda de homologacao: cliente nao acessa tarefas internas da equipe.
      const tasksCollection=pathname==='/api/v1/tasks';
      const taskAssignees=pathname==='/api/v1/tasks/assignees';
      const taskPath=pathname.match(
        /^\/api\/v1\/tasks\/([a-f0-9-]{36})(?:\/(status))?$/i,
      );
      if ((tasksCollection||taskAssignees||taskPath)&&['GET','POST','PATCH'].includes(req.method)) {
        const resolver=authService
          ? authService.resolvePrincipal.bind(authService)
          : resolvePrincipal;
        const principal=typeof resolver==='function'?await resolver(req):null;
        if(!principal){send(401,{ok:false,code:'UNAUTHENTICATED'});return;}
        if(req.method!=='GET'&&authService)authService.requireMutation(req);
        if(taskAssignees&&req.method==='GET'){
          send(200,{items:await taskService.assignees(principal)});return;
        }
        if(tasksCollection&&req.method==='GET'){
          send(200,{items:await taskService.list(principal)});return;
        }
        if(tasksCollection&&req.method==='POST'){
          send(201,{item:await taskService.create(principal,await readJson())});return;
        }
        if(taskPath&&!taskPath[2]&&req.method==='GET'){
          send(200,await taskService.get(principal,taskPath[1]));return;
        }
        if(taskPath&&!taskPath[2]&&req.method==='PATCH'){
          send(200,{item:await taskService.edit(principal,taskPath[1],await readJson())});return;
        }
        if(taskPath?.[2]==='status'&&req.method==='POST'){
          send(200,{item:await taskService.status(principal,taskPath[1],await readJson())});return;
        }
      }

      // Vistorias NOVAS na base dedicada de homologacao: nunca usar headers de identidade.
      const inspectionCollection=pathname==='/api/v1/inspections';
      const inspectionPath=pathname.match(
        /^\/api\/v1\/inspections\/([a-f0-9-]{36})(?:\/(findings|complete))?$/i,
      );
      if ((inspectionCollection||inspectionPath)&&['GET','POST','PATCH'].includes(req.method)) {
        const resolver=authService
          ? authService.resolvePrincipal.bind(authService)
          : resolvePrincipal;
        const principal=typeof resolver==='function' ? await resolver(req) : null;
        if (!principal) {
          send(401,{ok:false,code:'UNAUTHENTICATED'});
          return;
        }
        if (req.method!=='GET'&&authService) authService.requireMutation(req);
        if (inspectionCollection&&req.method==='GET') {
          send(200,{items:await inspectionService.list(principal)});
          return;
        }
        if (inspectionPath&&!inspectionPath[2]&&req.method==='GET') {
          send(200,await inspectionService.get(principal,inspectionPath[1]));
          return;
        }
        if (inspectionCollection&&req.method==='POST') {
          send(201,{item:await inspectionService.create(principal,await readJson())});
          return;
        }
        if (inspectionPath&&!inspectionPath[2]&&req.method==='PATCH') {
          send(200,{item:await inspectionService.update(principal,inspectionPath[1],await readJson())});
          return;
        }
        if (inspectionPath?.[2]==='findings'&&req.method==='POST') {
          send(201,{item:await inspectionService.addFinding(principal,inspectionPath[1],await readJson())});
          return;
        }
        if (inspectionPath?.[2]==='complete'&&req.method==='POST') {
          send(200,{item:await inspectionService.complete(principal,inspectionPath[1])});
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

