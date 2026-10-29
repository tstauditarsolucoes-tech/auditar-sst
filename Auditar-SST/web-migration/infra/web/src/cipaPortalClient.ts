export type CipaSession={ok:true;name:string;companyId:string;csrfToken:string;mustChangePassword:boolean};
export type StaffSession={companyId:string;role:'adm'|'gestor'|'tecnico'|'cliente';csrfToken:string};
export type Mandate={id:string;name:string;status:string;starts_on:string;ends_on:string};
export type PortalAction={id:string;assigned_to:string;title:string;description:string;due_on:string;priority:string;status:string;revision:number};
export type PortalEntry={id:string;kind:string;message:string;action_id:string|null;meeting_id:string|null;author_account_id:string|null;created_at:string};
export type PortalMeeting={id:string;title:string;scheduled_at:string;summary:string;status:string};
export type CipaMonthlySummary={mandate:{id:string;name:string;status:string};period:string;actions:{total:number;pending:number;reviewing:number;done:number;overdue:number};meetings:{status:string;total:number}[];participation:{kind:string;total:number}[];activeMembers:number;note:string};
export type PortalAccount={id:string;display_name:string;email:string;active:boolean;grant_active?:boolean;member_id?:string;must_change_password?:boolean};
export type PortalWorkspace={mandate:Mandate;actions:PortalAction[];meetings:PortalMeeting[];entries:PortalEntry[];checklist?:{message:string;created_at:string}[];accounts?:PortalAccount[];members?:{id:string;display_name:string}[];counts:{pending:number;reviewing:number;scheduled:number};limits:{actions:number;meetings:number;entries:number}};
const messages:Record<string,string>={
  CIPA_PORTAL_DISABLED:'O portal ainda não foi habilitado neste ambiente. Solicite a ativação da homologação à equipe.',
  UNAUTHENTICATED:'A sessão expirou. Entre novamente.',LOGIN_FAILED:'Empresa, e-mail ou senha não conferem.',
  FORBIDDEN:'Sua conta não pode executar esta ação.',PASSWORD_CHANGE_REQUIRED:'Troque sua senha temporária primeiro.',
  LOGIN_THROTTLED:'Muitas tentativas. Aguarde 15 minutos antes de tentar novamente.',
  WEAK_PASSWORD:'A senha deve ter de 12 a 256 caracteres e ser diferente da temporária.',
  ACCOUNT_EXISTS:'Já existe uma conta com esse e-mail. Use Vincular conta existente; a senha não foi alterada.',
  INVALID_INPUT:'Confira os campos e seus limites.',CLOSED_MANDATE:'O mandato está encerrado e disponível apenas para consulta.',
  STALE_REVISION:'Esta ação foi alterada por outra pessoa. Atualize a tela antes de tentar novamente.',
  INVALID_STATE:'A mudança solicitada não está disponível no estado atual. Atualize a tela.',
  NOT_FOUND:'Registro não encontrado ou sem permissão.',CSRF_DENIED:'Atualize sua sessão antes de continuar.',
  IDEMPOTENCY_CONFLICT:'Esta chave de envio já foi usada. Atualize a tela e confira se o registro foi salvo.',
  INVALID_RESPONSE:'O servidor do portal não respondeu corretamente. Nenhum acesso foi confirmado; tente novamente mais tarde.',
  LINK_CONFLICT:'Este membro já tem outra conta vinculada neste mandato. Confira os vínculos antes de continuar.',
};
export class PortalError extends Error{code:string;constructor(code:string){super(messages[code]||'Não foi possível concluir. Atualize e confira antes de reenviar.');this.code=code;}}
export async function portalRequest<T>(path:string,body?:object,csrf?:string,signal?:AbortSignal):Promise<T>{
  const r=await fetch('/api/v1/'+path,{method:body?'POST':'GET',credentials:'same-origin',cache:'no-store',signal,
    headers:{...(body?{'Content-Type':'application/json'}:{}),...(csrf?{'X-CSRF-Token':csrf}:{})},body:body?JSON.stringify(body):undefined});
  if(!r.headers.get('content-type')?.toLowerCase().includes('application/json'))throw new PortalError('INVALID_RESPONSE');
  const value=await r.json().catch(()=>null);if(!value||typeof value!=='object'||Array.isArray(value))throw new PortalError('INVALID_RESPONSE');
  if(!r.ok)throw new PortalError(value.code||'HTTP_'+r.status);
  if(/^cipa-portal\/auth\/(session|login|password)$/.test(path)&&
    (value.ok!==true||typeof value.name!=='string'||typeof value.companyId!=='string'||typeof value.csrfToken!=='string'||typeof value.mustChangePassword!=='boolean'))throw new PortalError('INVALID_RESPONSE');
  return value as T;
}
export const statusLabel:Record<string,string>={aberta:'Aberta',andamento:'Em andamento',aguardando_validacao:'Aguardando validação',concluida:'Concluída',planejada:'Agendada',realizada:'Realizada',cancelada:'Cancelada',ativo:'Ativo',preparacao:'Em preparação',encerrado:'Encerrado'};
export const entryLabel:Record<string,string>={checklist:'Checklist mensal',observacao:'Situação observada',sugestao:'Sugestão de prevenção',apoio:'Pedido de apoio',atualizacao:'Atualização do membro',decisao:'Validação da equipe',orientacao:'Orientação da equipe',aviso:'Aviso do mandato',ciencia_reuniao:'Ciência da reunião',acesso:'Gestão de acesso'};
export function shortDate(value:string){const d=value.slice(0,10).split('-');return d.length===3?`${d[2]}/${d[1]}/${d[0]}`:value;}
export function localTime(value:string){return new Date(value).toLocaleString('pt-BR',{dateStyle:'short',timeStyle:'short'});}
