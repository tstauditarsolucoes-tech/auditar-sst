/** Minuta PDF de treinamento, sem assinaturas/certificacoes, SOMENTE homologacao. */
import {ApiError,withTenant} from './ncService.mjs';
import {createTrainingService} from './trainingService.mjs';
function label(value){return String(value??'').replace(/[\u0000-\u001f\u007f]/g,' ').trim();}
function date(value){
 if(!value)return 'Não informada';
 return new Date(value).toLocaleString('pt-BR',{timeZone:'America/Fortaleza'});
}
const TYPE={treinamento:'Treinamento',dds:'DDS',integracao:'Integração'};
export function createTrainingReportService(pool){
 const service=createTrainingService(pool);
 return {
  async attendancePdf(principal,id){
   const detail=await service.get(principal,id); // Nega cliente e cruza tenant com RLS.
   const company=await withTenant(pool,principal,async(db,p)=>{
    const r=await db.query('SELECT name FROM sst.company WHERE id=$1',[p.companyId]);
    if(!r.rowCount)throw new ApiError(404,'NOT_FOUND','Empresa indisponivel');
    return r.rows[0].name;
   });
   const {PDFDocument}=await import('pdfkit');
   const doc=new PDFDocument({size:'A4',autoFirstPage:false,margin:42,
     info:{Title:'Minuta de acompanhamento educativo - Homologação Auditar SST',
       Author:'Auditar SST - testes'}});
   const blocks=[];
   let size=0;
   const result=new Promise((resolve,reject)=>{
    doc.on('data',v=>{
     size+=v.length;
     if(size>4*1024*1024){doc.destroy(new Error('PDF_TOO_LARGE'));return;}
     blocks.push(v);
    });
    doc.on('error',reject);
    doc.on('end',()=>resolve(Buffer.concat(blocks)));
   });
   const a=detail.training,attendance=detail.attendance||[];
   const max=14;
   const pages=Math.max(1,Math.ceil(attendance.length/max));
   for(let page=0;page<pages;page++){
    doc.addPage();
    doc.rect(0,0,595,90).fill('#10365b');
    doc.fillColor('#ffffff').font('Helvetica-Bold').fontSize(17)
       .text('AUDITAR SST - HOMOLOGAÇÃO',42,23,{width:510});
    doc.font('Helvetica').fontSize(11).text('Controle administrativo de atividade educativa',42,54);
    doc.fillColor('#933d21').font('Helvetica-Bold').fontSize(12)
       .text('MINUTA - SEM ASSINATURAS - NÃO COMPROVA PRESENÇA',42,112,{width:515});
    const info=[
     ['Empresa',label(company)],['Atividade',TYPE[a.kind]||a.kind],
     ['Tema',label(a.title)],['Setor',label(a.sector)||'Não registrado'],
     ['NR de referência',label(a.nr_reference)||'Não informada'],
     ['Instrutor informado',label(a.instructor)||'Não informado'],
     ['Data prevista',date(a.planned_at)],
     ['Duração informada',a.duration_minutes==null?'Não informada':String(a.duration_minutes)+' minutos'],
     ['Participantes (contagem informada)',a.participants_count==null?'Não informada':String(a.participants_count)],
     ['Situação',label(a.status)],
    ];
    let y=153;
    for(const [key,value] of info){
      doc.font('Helvetica-Bold').fontSize(9).fillColor('#38516b')
       .text(key+':',42,y,{width:185,height:19,ellipsis:true});
      doc.font('Helvetica').fillColor('#182c42')
       .text(value,229,y,{width:310,height:19,ellipsis:true});
      y+=24;
    }
    const top=415;
    doc.font('Helvetica-Bold').fontSize(11).fillColor('#10365b')
     .text('Relação informada de participantes - TESTE',42,top,{width:490});
    doc.font('Helvetica').fontSize(8.5).fillColor('#4e6276')
     .text('Nomes são registros declarados; nenhum deles confirma comparecimento.',42,top+20,{width:490});
    const header=top+49;
    doc.rect(42,header,511,24).fill('#e5edf4');
    doc.font('Helvetica-Bold').fillColor('#153751').fontSize(9)
      .text('Nº',50,header+7,{width:30})
      .text('Nome informado',88,header+7,{width:315})
      .text('Situação declarada',414,header+7,{width:125});
    const rows=attendance.slice(page*max,(page+1)*max);
    rows.forEach((item,index)=>{
      const y=header+26+index*21;
      doc.font('Helvetica').fontSize(9).fillColor('#24384c')
       .text(String(page*max+index+1),50,y,{width:31,height:15})
       .text(label(item.display_name),88,y,{width:315,height:16,ellipsis:true})
       .text(item.presence==='declarada'?'Declarada':'Não confirmada',414,y,{width:125,height:16});
      doc.moveTo(42,y+18).lineTo(552,y+18).strokeColor('#dbe6ee').lineWidth(.5).stroke();
    });
    if(!rows.length)doc.font('Helvetica').fontSize(10).fillColor('#526277')
      .text('Nenhum participante de teste cadastrado.',52,header+35);
    doc.fillColor('#526277').fontSize(8).font('Helvetica')
      .text('Homologação com dados fictícios | Não é certificado, ata ou lista assinada',42,791,{width:454});
    doc.text(String(page+1)+'/'+String(pages),508,791,{width:40,align:'right'});
   }
   doc.end();
   return await result;
  },
 };
}
