/** Contrato MINIMO de escrita de vistorias NOVAS na homologacao nativa.
 * Nunca aceitar payloads de tabela, filas de sync Flutter ou empresa/perfil do cliente.
 */
import {ApiError} from './ncService.mjs';
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const ALLOWED={
 inspection:new Set(['inspectionType','title','description','sector','location','clientRequestId']),
 finding:new Set(['shortTitle','description','recommendation','probability','severity','recurring','clientRequestId']),
};
export function nativeDraftPayload(payload,kind){
  if(!payload||typeof payload!=='object'||Array.isArray(payload)||
     !Object.prototype.hasOwnProperty.call(ALLOWED,kind)){
    throw new ApiError(400,'INVALID_NATIVE_DRAFT','Tipo de envio invalido');
  }
  const allowed=ALLOWED[kind],keys=Object.keys(payload);
  if(!keys.length||keys.some(key=>!allowed.has(key))){
    throw new ApiError(400,'INVALID_NATIVE_DRAFT','Campo nao permitido para novo registro');
  }
  if(typeof payload.clientRequestId!=='string'||!UUID.test(payload.clientRequestId)){
    throw new ApiError(400,'INVALID_NATIVE_DRAFT','Identificador unico de envio obrigatorio');
  }
  // Nunca gerar chave no servidor: a fila offline deve manter o mesmo UUID nos retries.
  return payload;
}
