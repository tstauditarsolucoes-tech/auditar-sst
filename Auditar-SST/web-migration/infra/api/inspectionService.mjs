/**
 * Primeira vertical web de VISTORIAS em banco novo de homologacao.
 * Nao acessa Apps Script/Sheets/Drive nem altera as versoes Flutter.
 * Auth principal e role DB tenant sao obtidos unicamente pelo servidor.
 */
import { ApiError, withTenant } from './ncService.mjs';

const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
const TYPES=new Set(['vistoria','ronda_expressa','checklist']);
const WRITE_ROLES=new Set(['adm','gestor','tecnico']);
function requiredUuid(value,label) {
  if (typeof value!=='string'||!UUID.test(value)) {
    throw new ApiError(400,'INVALID_INPUT',label+' invalido');
  }
  return value.toLowerCase();
}
function field(value,max,label,optional=false) {
  if (optional && (value===undefined||value===null)) return '';
  if (typeof value!=='string') throw new ApiError(400,'INVALID_INPUT',label+' deve ser texto');
  const normalized=value.replace(/\s+/g,' ').trim();
  if ((!normalized&&!optional)||normalized.length>max) {
    throw new ApiError(400,'INVALID_INPUT',label+' invalido');
  }
  return normalized;
}
function canWrite(p) {
  if (!WRITE_ROLES.has(p.role)) throw new ApiError(403,'FORBIDDEN','Perfil sem permissao');
}
function risk(value,label) {
  if (!Number.isInteger(value)||value<1||value>5) {
    throw new ApiError(400,'INVALID_INPUT',label+' deve ser inteiro de 1 a 5');
  }
  return value;
}
function details(payload) {
  if (!TYPES.has(payload.inspectionType)) {
    throw new ApiError(400,'INVALID_INPUT','Tipo de vistoria invalido');
  }
  return {
    inspectionType:payload.inspectionType,
    title:field(payload.title,200,'Titulo'),
    description:field(payload.description,4000,'Descricao',true),
    sector:field(payload.sector,180,'Setor',true),
    location:field(payload.location,180,'Local',true),
  };
}
function finding(payload) {
  if (payload.recurring!==undefined&&typeof payload.recurring!=='boolean') {
    throw new ApiError(400,'INVALID_INPUT','Recorrencia invalida');
  }
  return {
    description:field(payload.description,4000,'Descricao'),
    shortTitle:field(payload.shortTitle,140,'Nome da NC',true),
    recommendation:field(payload.recommendation,1600,'Recomendacao',true),
    probability:risk(payload.probability,'Probabilidade'),
    severity:risk(payload.severity,'Severidade'),
    recurring:payload.recurring??false,
  };
}
async function inspectionEvent(db,p,id,kind,message='',nonConformityId=null) {
  await db.query(
    'INSERT INTO sst.inspection_event '+
    '(company_id,inspection_id,kind,message,non_conformity_id,created_by) '+
    'VALUES ($1,$2,$3,$4,$5,$6)',
    [p.companyId,id,kind,message,nonConformityId,p.userId],
  );
}
async function inspectionRow(db,p,id,lock=false) {
  const result=await db.query(
    'SELECT id,company_id,inspection_type,status,title,description,sector,location,revision,'+
    'client_request_id,created_at,updated_at,completed_at FROM sst.inspection '+
    'WHERE company_id=$1 AND id=$2 '+(lock?'FOR UPDATE':''),
    [p.companyId,id],
  );
  if (!result.rowCount) throw new ApiError(404,'NOT_FOUND','Vistoria nao encontrada');
  const row=result.rows[0];
  if (p.role==='cliente'&&row.status!=='concluida') {
    throw new ApiError(404,'NOT_FOUND','Vistoria nao disponivel');
  }
  return row;
}
function assertSameInspection(existing,values) {
  if (existing.inspection_type!==values.inspectionType ||
      existing.title!==values.title||existing.description!==values.description||
      existing.sector!==values.sector||existing.location!==values.location) {
    throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Identificador ja utilizado com outros dados');
  }
}
function assertSameFinding(existing,inspectionId,values) {
  if (existing.inspection_id!==inspectionId||
    existing.description!==values.description||
    existing.short_title!==values.shortTitle||
    existing.recommendation!==values.recommendation||
    existing.probability!==values.probability||
    existing.severity!==values.severity||
    existing.recurring!==values.recurring) {
    throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Identificador ja utilizado com outro achado');
  }
}

export function createInspectionService(pool) {
  return {
    list(principal) {
      return withTenant(pool,principal,async(db,p)=>{
        const result=await db.query(
          'SELECT id,inspection_type,status,title,description,sector,location,revision,'+
          'created_at,updated_at,completed_at FROM sst.inspection '+
          'WHERE company_id=$1 '+(p.role==='cliente'?"AND status='concluida' ":'')+
          'ORDER BY updated_at DESC,id DESC LIMIT 100',
          [p.companyId],
        );
        return result.rows;
      });
    },
    get(principal,id) {
      return withTenant(pool,principal,async(db,p)=>{
        const inspection=await inspectionRow(db,p,requiredUuid(id,'Vistoria'));
        const findings=await db.query(
          'SELECT id,short_title,description,recommendation,probability,severity,recurring,status,created_at '+
          'FROM sst.non_conformity WHERE company_id=$1 AND inspection_id=$2 '+
          'ORDER BY created_at,id', [p.companyId,inspection.id],
        );
        const events=await db.query(
          'SELECT id,kind,message,non_conformity_id,created_by,created_at '+
          'FROM sst.inspection_event WHERE company_id=$1 AND inspection_id=$2 '+
          'ORDER BY created_at,id', [p.companyId,inspection.id],
        );
        return {inspection,findings:findings.rows,events:events.rows};
      });
    },
    create(principal,payload={}) {
      return withTenant(pool,principal,async(db,p)=>{
        canWrite(p);
        const values=details(payload);
        const requestId=requiredUuid(payload.clientRequestId,'Chave de envio');
        const result=await db.query(
          'INSERT INTO sst.inspection '+
          '(company_id,inspection_type,title,description,sector,location,client_request_id,created_by) '+
          'VALUES ($1,$2,$3,$4,$5,$6,$7,$8) '+
          'ON CONFLICT (company_id,client_request_id) WHERE client_request_id IS NOT NULL '+
          'DO NOTHING RETURNING id,inspection_type,title,description,sector,location,status,revision',
          [p.companyId,values.inspectionType,values.title,values.description,
            values.sector,values.location,requestId,p.userId],
        );
        if (result.rowCount) {
          await inspectionEvent(db,p,result.rows[0].id,'criada');
          return result.rows[0];
        }
        const original=await db.query(
          'SELECT id,inspection_type,title,description,sector,location,status,revision '+
          'FROM sst.inspection WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId],
        );
        if (!original.rowCount) throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Envio repetido divergente');
        assertSameInspection(original.rows[0],values);
        return original.rows[0];
      });
    },
    update(principal,id,payload={}) {
      return withTenant(pool,principal,async(db,p)=>{
        canWrite(p);
        const inspected=await inspectionRow(db,p,requiredUuid(id,'Vistoria'),true);
        if (inspected.status!=='rascunho') throw new ApiError(409,'INVALID_STATE','Vistoria ja concluida');
        if (!Number.isInteger(payload.expectedRevision)||
            payload.expectedRevision!==inspected.revision) {
          throw new ApiError(409,'STALE_REVISION','Rascunho foi alterado em outro dispositivo');
        }
        const values=details({...payload,inspectionType:inspected.inspection_type});
        const changed=await db.query(
          'UPDATE sst.inspection SET title=$3,description=$4,sector=$5,location=$6,'+
          'revision=revision+1,updated_at=now() WHERE company_id=$1 AND id=$2 '+
          'RETURNING id,inspection_type,title,description,sector,location,status,revision',
          [p.companyId,inspected.id,values.title,values.description,values.sector,values.location],
        );
        await inspectionEvent(db,p,inspected.id,'editada');
        return changed.rows[0];
      });
    },
    addFinding(principal,id,payload={}) {
      return withTenant(pool,principal,async(db,p)=>{
        canWrite(p);
        const inspectionId=requiredUuid(id,'Vistoria');
        const requestId=requiredUuid(payload.clientRequestId,'Chave do achado');
        const values=finding(payload);
        const inspected=await inspectionRow(db,p,inspectionId,true);
        const previous=await db.query(
          'SELECT id,inspection_id,short_title,description,recommendation,probability,severity,recurring,status '+
          'FROM sst.non_conformity WHERE company_id=$1 AND client_request_id=$2',
          [p.companyId,requestId],
        );
        if (previous.rowCount) {
          assertSameFinding(previous.rows[0],inspectionId,values);
          return previous.rows[0];
        }
        if (inspected.status!=='rascunho') throw new ApiError(409,'INVALID_STATE','Vistoria ja concluida');
        const created=await db.query(
          'INSERT INTO sst.non_conformity '+
          '(company_id,inspection_id,short_title,description,recommendation,probability,severity,recurring,'+
          'client_request_id,created_by) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) '+
          'ON CONFLICT (company_id,client_request_id) WHERE client_request_id IS NOT NULL '+
          'DO NOTHING RETURNING id,inspection_id,short_title,description,recommendation,probability,severity,recurring,status',
          [p.companyId,inspectionId,values.shortTitle,values.description,values.recommendation,
            values.probability,values.severity,values.recurring,requestId,p.userId],
        );
        if (!created.rowCount) {
          const duplicate=await db.query(
            'SELECT id,inspection_id,short_title,description,recommendation,probability,severity,recurring,status '+
            'FROM sst.non_conformity WHERE company_id=$1 AND client_request_id=$2',
            [p.companyId,requestId],
          );
          if (!duplicate.rowCount) throw new ApiError(409,'IDEMPOTENCY_CONFLICT','Achado duplicado divergente');
          assertSameFinding(duplicate.rows[0],inspectionId,values);
          return duplicate.rows[0];
        }
        const nc=created.rows[0];
        await db.query(
          'INSERT INTO sst.nc_treatment_event '+
          "(company_id,non_conformity_id,kind,message,created_by) VALUES ($1,$2,'identificada','',$3)",
          [p.companyId,nc.id,p.userId],
        );
        await inspectionEvent(db,p,inspectionId,'achado_incluido',values.shortTitle||values.description.slice(0,140),nc.id);
        await db.query(
          'UPDATE sst.inspection SET revision=revision+1,updated_at=now() '+
          'WHERE company_id=$1 AND id=$2', [p.companyId,inspectionId],
        );
        return nc;
      });
    },
    complete(principal,id) {
      return withTenant(pool,principal,async(db,p)=>{
        canWrite(p);
        const inspected=await inspectionRow(db,p,requiredUuid(id,'Vistoria'),true);
        if (inspected.status==='concluida') return {id:inspected.id,status:'concluida'};
        if (inspected.status!=='rascunho') throw new ApiError(409,'INVALID_STATE','Vistoria arquivada');
        await db.query(
          "UPDATE sst.inspection SET status='concluida',completed_at=now(),updated_at=now(),"+
          'revision=revision+1 WHERE company_id=$1 AND id=$2',
          [p.companyId,inspected.id],
        );
        await inspectionEvent(db,p,inspected.id,'concluida');
        return {id:inspected.id,status:'concluida'};
      });
    },
  };
}
