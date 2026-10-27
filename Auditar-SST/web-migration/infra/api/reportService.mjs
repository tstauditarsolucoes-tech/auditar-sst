/**
 * RELATORIO PDF DE HOMOLOGACAO. Nao e o modelo Auditar 3 definitivo.
 * Gera memoria somente de vistoria concluida da NOVA base, com foto privada opcional.
 * Sem Drive, Apps Script, assinatura ou dados de cliente importados.
 */
import {ApiError,withTenant} from './ncService.mjs';
import {createInspectionService} from './inspectionService.mjs';
import {createEvidenceService} from './evidenceService.mjs';
const MAX_FINDINGS=30;
const MAX_PDF_BYTES=24*1024*1024;
function label(value){
  return String(value??'').replace(/[\u0000-\u001f\u007f]/g,' ').trim();
}
function displayTime(value){
  if(!value)return 'Não informada';
  return new Date(value).toLocaleString('pt-BR',{timeZone:'America/Fortaleza'});
}
function risk(score){
  return score>=20?'Crítica':score>=12?'Alta':score>=6?'Média':'Baixa';
}
function drawHeader(doc,title,subtitle){
  doc.rect(0,0,595,92).fill('#10365b');
  doc.fillColor('#ffffff').font('Helvetica-Bold').fontSize(20)
    .text('AUDITAR SST',48,23,{width:495});
  doc.font('Helvetica').fontSize(10).text(title,48,54,{width:495});
  doc.fillColor('#122d24').fontSize(10).text(subtitle,48,108,{width:495});
  doc.moveTo(48,130).lineTo(547,130).strokeColor('#b8d0c7').lineWidth(1).stroke();
}
function footer(doc,page){
  doc.fillColor('#52645c').fontSize(8).font('Helvetica')
    .text('Homologação técnica · dados fictícios · não utilizar como documento oficial',48,794,{width:435});
  doc.text(String(page),505,794,{width:42,align:'right'});
}
function itemText(doc,text,x,y,width,height,fontSize){
  doc.font('Helvetica').fillColor('#172a23').fontSize(fontSize).text(label(text),x,y,{
    width,height,ellipsis:true,breakLine:false,
  });
}
export function createReportService(pool,evidenceDir){
  const inspections=createInspectionService(pool);
  const evidence=createEvidenceService(pool,evidenceDir);
  return {
    async inspectionPdf(principal,id){
      const detail=await inspections.get(principal,id);
      if(detail.inspection.status!=='concluida'){
        throw new ApiError(409,'REPORT_NOT_FINAL','Conclua a vistoria antes do relatorio');
      }
      if(detail.findings.length>MAX_FINDINGS){
        throw new ApiError(413,'REPORT_TOO_LARGE','Relatorio de homologacao limitado a 30 achados');
      }
      const company=await withTenant(pool,principal,async(db,p)=>{
        const row=await db.query('SELECT name FROM sst.company WHERE id=$1',[p.companyId]);
        if(!row.rowCount)throw new ApiError(404,'NOT_FOUND','Empresa nao encontrada');
        return row.rows[0].name;
      });
      const media=[];
      for(const nc of detail.findings){
        let photo=null;
        if(evidenceDir){
          const list=await evidence.list(principal,{nonConformityId:nc.id});
          const first=list.find(x=>['image/jpeg','image/png'].includes(x.mime_type));
          if(first){
            const blob=await evidence.download(principal,first.id);
            photo=blob.data;
          }
        }
        media.push(photo?{id:nc.id,title:nc.short_title||nc.description,bytes:photo}:null);
      }
      // Importar PDFKit somente quando requisitado. API desativada por padrao
      // nao precisa carregar bibliotecas de PDF na inicializacao.
      const {PDFDocument}=await import('pdfkit');
      const doc=new PDFDocument({size:'A4',autoFirstPage:false,margins:{top:45,bottom:45,left:48,right:48},
        info:{Title:'Relatorio de Vistoria Auditar SST - Homologacao',Author:'Auditar SST'}});
      const chunks=[];
      let total=0;
      const output=new Promise((resolve,reject)=>{
        doc.on('data',part=>{
          total+=part.length;
          if(total>MAX_PDF_BYTES){doc.destroy(new Error('PDF_TOO_LARGE'));return;}
          chunks.push(part);
        });
        doc.on('error',reject);
        doc.on('end',()=>resolve(Buffer.concat(chunks)));
      });
      let page=1;
      doc.addPage();
      drawHeader(doc,'Relatório de vistoria - piloto','Relatório produzido na base NOVA de homologação');
      doc.font('Helvetica-Bold').fillColor('#075a45').fontSize(17)
        .text(label(detail.inspection.title),48,157,{width:499,height:65,ellipsis:true});
      let y=233;
      const info=[
        ['Empresa',company],['Tipo',detail.inspection.inspection_type.replaceAll('_',' ')],
        ['Setor',detail.inspection.sector||'Não informado'],
        ['Local',detail.inspection.location||'Não informado'],
        ['Conclusão',displayTime(detail.inspection.completed_at)],
        ['NCs registradas',String(detail.findings.length)],
      ];
      for(const [k,v] of info){
        doc.fillColor('#476055').font('Helvetica-Bold').fontSize(10).text(k+':',48,y,{width:140});
        itemText(doc,v,188,y,355,20,10);y+=33;
      }
      doc.fillColor('#075a45').font('Helvetica-Bold').fontSize(13).text('Observações',48,472);
      doc.font('Helvetica').fillColor('#172a23').fontSize(10)
        .text(label(detail.inspection.description)||'Sem observações adicionais.',48,500,{
          width:493,height:230,ellipsis:true,
        });
      footer(doc,page);
      // Sumario visual: ate dois achados por pagina. Fotos sao grandes em anexo
      // separado, sem reduzir o espaco de leitura das recomendacoes.
      for(let i=0;i<detail.findings.length;i+=2){
        page++;doc.addPage();
        drawHeader(doc,'Achados e orientações - piloto','Até dois achados por página');
        for(let position=0;position<2;position++){
          const index=i+position;
          if(index>=detail.findings.length)continue;
          const nc=detail.findings[index],top=145+position*310;
          const score=nc.probability*nc.severity;
          doc.roundedRect(48,top,499,297,9).lineWidth(1).strokeColor('#ccd9e3').stroke();
          doc.fillColor('#10365b').font('Helvetica-Bold').fontSize(13)
            .text((index+1)+'. '+label(nc.short_title||nc.description),
              62,top+12,{width:465,height:35,ellipsis:true});
          doc.fillColor('#425c72').font('Helvetica').fontSize(9)
            .text('Risco: '+nc.probability+' x '+nc.severity+' = '+score+
              ' ('+risk(score)+') | '+nc.status.replaceAll('_',' ')+
              (nc.recurring?' | Recorrente':''),
              62,top+53,{width:465,height:18,ellipsis:true});
          doc.font('Helvetica-Bold').fillColor('#10365b').fontSize(9.5)
            .text('SITUAÇÃO ENCONTRADA',62,top+82,{width:463,height:16});
          doc.font('Helvetica').fillColor('#182f41').fontSize(9)
            .text(label(nc.description),62,top+99,{width:461,height:77,ellipsis:true});
          doc.font('Helvetica-Bold').fillColor('#08795c').fontSize(9.5)
            .text('RECOMENDAÇÃO TÉCNICA',62,top+185,{width:461,height:16});
          doc.font('Helvetica').fillColor('#182f41').fontSize(9)
            .text(label(nc.recommendation)||'Não registrada neste piloto.',
              62,top+202,{width:461,height:67,ellipsis:true});
          doc.fillColor('#587283').font('Helvetica').fontSize(8)
            .text(media[index]?'Evidência ampliada no anexo fotográfico.':'Sem foto JPEG/PNG associada à NC.',
              62,top+278,{width:460,height:12});
        }
        footer(doc,page);
      }
      // Uma foto por NC nesta fase. Cada foto aparece em area de ate 460x225 pt.
      // O arquivo original do volume privado nao e alterado nem recomprimido.
      const photos=media.filter(Boolean);
      for(let i=0;i<photos.length;i+=2){
        page++;doc.addPage();
        drawHeader(doc,'Registro fotográfico - piloto','Fotos ampliadas das NCs desta vistoria');
        for(let position=0;position<2;position++){
          const photo=photos[i+position];
          if(!photo)continue;
          const top=148+position*308;
          const ncIndex=detail.findings.findIndex(n=>n.id===photo.id);
          doc.roundedRect(48,top,499,294,8).lineWidth(1).strokeColor('#ccd9e3').stroke();
          doc.fillColor('#10365b').font('Helvetica-Bold').fontSize(11)
            .text('NC '+(ncIndex+1)+' - '+label(photo.title),62,top+11,
              {width:465,height:30,ellipsis:true});
          try {
            doc.image(photo.bytes,62,top+48,{fit:[465,226],align:'center',valign:'center'});
          } catch {
            doc.font('Helvetica').fillColor('#86542b').fontSize(10)
              .text('Esta imagem não pôde ser exibida na homologação.',62,top+145,
                {width:455,height:24});
          }
        }
        footer(doc,page);
      }
      doc.end();
      return await output;
    },
  };
}
