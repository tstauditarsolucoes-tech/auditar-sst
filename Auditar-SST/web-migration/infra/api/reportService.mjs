/**
 * RELATORIO PDF DE HOMOLOGACAO. Nao e o modelo Auditar 3 definitivo.
 * Gera memoria somente de vistoria concluida da NOVA base, com foto privada opcional.
 * Sem Drive, Apps Script, assinatura ou dados de cliente importados.
 */
import {ApiError,withTenant} from './ncService.mjs';
import {createInspectionService} from './inspectionService.mjs';
import {createEvidenceService} from './evidenceService.mjs';
import {cleanPdfText,takePdfText} from './reportTextPagination.mjs';
const MAX_FINDINGS=30;
const MAX_PDF_BYTES=24*1024*1024;
function label(value){return cleanPdfText(value);}
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
    .text('Homologação técnica · dados fictícios · não utilizar como documento oficial',48,778,{width:435});
  doc.text(String(page),505,778,{width:42,align:'right'});
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
          const selected=list.filter(x=>['image/jpeg','image/png'].includes(x.mime_type)).slice(0,2);
          photo=[];
          for(const evidenceItem of selected){
            const blob=await evidence.download(principal,evidenceItem.id);
            photo.push({id:nc.id,title:nc.short_title||nc.description,bytes:blob.data,
              photoOrdinal:photo.length+1});

          }
        }
        media.push(photo||[]);
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
      const continuation=[];
      function addContinuation(number,heading,text){
        if(label(text))continuation.push({number,heading,text});
      }
      function slot(text,width,maxHeight,fontSize=9){
        const content=label(text);
        return takePdfText(doc,content,{width,maxHeight,fontSize,lineGap:1});
      }
      function drawSlot(text,x,y,width,maxHeight,fontSize=9){
        doc.font('Helvetica').fillColor('#182f41').fontSize(fontSize);
        const part=slot(text,width,maxHeight,fontSize);
        if(part.head)doc.text(part.head,x,y,{width,lineGap:1});
        return part.rest;
      }
      // Capa resumida: qualquer texto excedente vai para páginas complementares.
      doc.addPage();
      drawHeader(doc,'Relatório de vistoria - piloto','Base nova de homologação, sem dados legados');
      doc.font('Helvetica-Bold').fillColor('#10365b').fontSize(16);
      const mainTitle=label(detail.inspection.title);
      const titleSlot=slot(mainTitle,499,66,16);
      if(titleSlot.head)doc.font('Helvetica-Bold').fontSize(16).text(titleSlot.head,48,157,{width:499,lineGap:1});
      addContinuation(null,'Título da vistoria - continuação',titleSlot.rest);
      let y=233;
      const info=[
        ['Empresa',company],['Tipo',detail.inspection.inspection_type.replaceAll('_',' ')],
        ['Setor',detail.inspection.sector||'Não informado'],
        ['Local',detail.inspection.location||'Não informado'],
        ['Conclusão',displayTime(detail.inspection.completed_at)],
        ['NCs registradas',String(detail.findings.length)],
      ];
      for(const [key,value] of info){
        doc.fillColor('#476055').font('Helvetica-Bold').fontSize(10)
          .text(key+':',48,y,{width:140});
        const rest=drawSlot(value,188,y,355,22,10);
        addContinuation(null,key+' - continuação',rest);
        y+=33;
      }
      doc.fillColor('#10365b').font('Helvetica-Bold').fontSize(13).text('Observações',48,472);
      const coverTail=drawSlot(detail.inspection.description||'Sem observações adicionais.',
        48,500,493,230,10);
      addContinuation(null,'Observações - continuação',coverTail);
      footer(doc,page);

      // Resumo de no máximo dois achados por página, com recomendação em campo próprio.
      // Todo texto que não couber recebe páginas subsequentes, nunca é descartado.
      for(let i=0;i<detail.findings.length;i+=2){
        page++;doc.addPage();
        drawHeader(doc,'Achados e orientações - piloto','Até dois achados por página');
        for(let position=0;position<2;position++){
          const index=i+position;
          if(index>=detail.findings.length)continue;
          const nc=detail.findings[index],top=145+position*310;
          const score=nc.probability*nc.severity;
          doc.roundedRect(48,top,499,297,9).lineWidth(1).strokeColor('#ccd9e3').stroke();
          doc.font('Helvetica-Bold').fontSize(12).fillColor('#10365b');
          const heading=slot((index+1)+'. '+label(nc.short_title||nc.description),465,37,12);
          doc.font('Helvetica-Bold').fontSize(12)
            .text(heading.head,62,top+12,{width:465,lineGap:1});
          addContinuation(index+1,'Título da NC - continuação',heading.rest);
          doc.font('Helvetica').fillColor('#425c72').fontSize(9)
            .text('Risco: '+nc.probability+' x '+nc.severity+' = '+score+
              ' ('+risk(score)+') | '+nc.status.replaceAll('_',' ')+
              (nc.recurring?' | Recorrente':''),
              62,top+55,{width:465});
          doc.font('Helvetica-Bold').fillColor('#10365b').fontSize(9.5)
            .text('SITUAÇÃO ENCONTRADA',62,top+86,{width:463});
          const situationTail=drawSlot(nc.description,62,top+105,461,72,9);
          addContinuation(index+1,'Situação encontrada - continuação',situationTail);
          doc.font('Helvetica-Bold').fillColor('#08795c').fontSize(9.5)
            .text('RECOMENDAÇÃO TÉCNICA',62,top+186,{width:461});
          const recommendationTail=drawSlot(nc.recommendation||'Não registrada neste piloto.',
            62,top+205,461,65,9);
          addContinuation(index+1,'Recomendação técnica - continuação',recommendationTail);
          doc.font('Helvetica').fillColor('#587283').fontSize(8)
            .text(media[index].length?media[index].length+' evidência(s) em páginas ampliadas.':
              'Sem foto JPEG/PNG associada à NC.',62,top+276,{width:460});
        }
        footer(doc,page);
      }

      // Anexos só surgem quando houver excedente. A escrita continua até o
      // último caractere, incluindo parágrafos extensos ou palavras sem espaços.
      for(const item of continuation){
        let remaining=item.text;
        let sectionPage=0;
        while(label(remaining)){
          sectionPage++;
          page++;doc.addPage();
          drawHeader(doc,'Texto integral - continuação',
            item.number===null?'Vistoria':'Não conformidade '+item.number);
          doc.font('Helvetica-Bold').fillColor('#10365b').fontSize(12)
            .text(item.heading+(sectionPage>1?' (parte '+sectionPage+')':''),48,153,
              {width:495,height:40,ellipsis:true});
          const current=slot(remaining,493,520,10);
          if(!current.head)throw new ApiError(413,'REPORT_TEXT_LAYOUT','Texto não coube na página');
          doc.font('Helvetica').fillColor('#182f41').fontSize(10)
            .text(current.head,48,210,{width:493,lineGap:1});
          remaining=current.rest;
          footer(doc,page);
        }
      }

      // Fotografias ampliadas: no máximo duas JPEG/PNG por NC, uma foto por página.
      // Arquivos permanecem privados; download valida hash/tenant antes de desenhar.
      const photos=media.flat();
      for(const photo of photos){
        page++;doc.addPage();
        const ncIndex=detail.findings.findIndex(n=>n.id===photo.id);
        drawHeader(doc,'Registro fotográfico - piloto','Evidência ampliada da NC '+(ncIndex+1));
        doc.fillColor('#10365b').font('Helvetica-Bold').fontSize(12)
          .text('NC '+(ncIndex+1)+' · Foto '+photo.photoOrdinal,48,150,{width:495});
        const caption=slot(photo.title,493,35,10);
        doc.fillColor('#425c72').font('Helvetica').fontSize(10)
          .text(caption.head,48,174,{width:493,lineGap:1});
        // Nome completo permanece no resumo da NC ou em sua pagina de continuacao.
        doc.roundedRect(48,219,499,525,8).lineWidth(1).strokeColor('#ccd9e3').stroke();
        try{
          doc.image(photo.bytes,61,232,{fit:[473,500],align:'center',valign:'center'});
        }catch{
          doc.font('Helvetica').fillColor('#86542b').fontSize(10)
            .text('Imagem não renderizada. Verificar evidência na homologação.',62,450,{width:450});
        }
        footer(doc,page);
      }
      // A identificação longa de fotografia pode ir para nova página sem corte.
      // Em geral já cabe na legenda; o armazenamento original não é modificado.

      doc.end();
      return await output;
    },
  };
}
