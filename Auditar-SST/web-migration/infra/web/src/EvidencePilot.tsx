import {useEffect,useState} from 'react';

type Session={csrfToken:string;role:string};
type Evidence={id:string;sha256:string;mime_type:string;size_bytes:number;created_at:string};
const LIMIT=2*1024*1024;
async function api<T>(path:string,options?:RequestInit):Promise<T>{
  const response=await fetch('/api/v1/'+path,{credentials:'same-origin',cache:'no-store',...options});
  const body:unknown=await response.json().catch(()=>null);
  if(!response.ok){
    const code=body&&typeof body==='object'&&'code' in body?String((body as {code:string}).code):String(response.status);
    throw new Error('Não foi possível anexar a foto: '+code);
  }
  return body as T;
}
async function base64(file:File):Promise<string>{
  return new Promise((resolve,reject)=>{
    const reader=new FileReader();
    reader.onload=()=>{
      const result=String(reader.result||'');
      resolve(result.includes(',')?result.slice(result.indexOf(',')+1):'');
    };
    reader.onerror=()=>reject(new Error('Falha ao ler foto local'));
    reader.readAsDataURL(file);
  });
}
export function EvidencePilot({session,targetType,targetId}:{
  session:Session;targetType:'inspection'|'nc';targetId:string;
}){
  const [items,setItems]=useState<Evidence[]>([]);
  const [file,setFile]=useState<File|null>(null);
  const [key,setKey]=useState(()=>crypto.randomUUID());
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('');
  const query=targetType==='nc'?'nonConformityId':'inspectionId';
  useEffect(()=>{
    let current=true;
    api<{items:Evidence[]}>('evidence?'+query+'='+targetId)
      .then(value=>{if(current)setItems(value.items);})
      .catch(()=>{if(current)setMessage('Fotos ainda não habilitadas nesta homologação.');});
    return()=>{current=false;};
  },[targetId,query]);
  async function send(){
    if(!file)return;
    if(!['image/jpeg','image/png','image/webp'].includes(file.type)||!file.size||file.size>LIMIT){
      setMessage('Selecione foto JPEG, PNG ou WebP de até 2 MB.');
      return;
    }
    setBusy(true);setMessage('');
    try{
      await api('evidence',{
        method:'POST',
        headers:{'Content-Type':'application/json','X-CSRF-Token':session.csrfToken},
        body:JSON.stringify({
          mimeType:file.type,contentBase64:await base64(file),clientRequestId:key,[query]:targetId,
        }),
      });
      const updated=await api<{items:Evidence[]}>('evidence?'+query+'='+targetId);
      setItems(updated.items);setFile(null);setKey(crypto.randomUUID());
      setMessage('Foto fictícia armazenada no volume privado de homologação.');
    }catch(e){setMessage(e instanceof Error?e.message:'Falha no envio');}
    finally{setBusy(false);}
  }
  return <section className="evidence-pilot" aria-label="Fotos privadas de homologação">
    <h4>Fotos anexadas · armazenamento privado de teste</h4>
    <p className="muted">O arquivo ficará somente no servidor de homologação. Não é enviado ao Google Drive nem ao app atual. Máximo: 2 MB por foto, JPEG/PNG/WebP.</p>
    <div className="evidence-gallery">{items.map(photo=><figure key={photo.id} className="evidence-thumb">
      <img src={'/api/v1/evidence/'+photo.id+'/content'} alt="Foto de teste autenticada" loading="lazy"/>
      <figcaption>{(photo.size_bytes/1024).toFixed(0)} KB · {new Date(photo.created_at).toLocaleDateString('pt-BR')}</figcaption>
    </figure>)}</div>
    <div className="auth-actions">
      <label>Escolher foto fictícia
        <input type="file" accept="image/jpeg,image/png,image/webp" disabled={busy}
          onChange={e=>setFile(e.target.files?.[0]||null)}/>
      </label>
      <button type="button" className="secondary-button" disabled={busy||!file}
        onClick={()=>void send()}>Enviar foto de teste</button>
    </div>
    {message&&<p role="status" className="auth-message">{message}</p>}
  </section>;
}
