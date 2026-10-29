/**
 * Paginação de parágrafos de relatório com PDFKit.
 * Não utiliza height/ellipsis de doc.text para descartar caracteres.
 */
export function cleanPdfText(value){
  return String(value??'').replace(/[\u0000-\u001f\u007f]/g,' ').replace(/\s+/g,' ').trim();
}
/**
 * Devolve um segmento que cabe no espaço disponível, e o restante sem perda.
 * Se uma palavra for maior que o quadro, divide também a palavra.
 */
export function takePdfText(doc,value,{width,maxHeight,fontSize=9,lineGap=1}){
  const source=String(value??'');
  if(!source)return {head:'',rest:''};
  doc.font('Helvetica').fontSize(fontSize);
  const config={width,lineGap};
  const fits=content=>doc.heightOfString(content,config)<=maxHeight;
  if(fits(source))return {head:source,rest:''};
  const chars=Array.from(source);
  let lo=1,hi=chars.length-1,best=0;
  while(lo<=hi){
    const mid=Math.floor((lo+hi)/2);
    const candidate=chars.slice(0,mid).join('');
    if(fits(candidate)){best=mid;lo=mid+1;}else hi=mid-1;
  }
  if(!best)throw new Error('PDF_TEXT_SLOT_TOO_SMALL');
  let stop=best;
  // Evita quebrar palavra se ela couber integralmente neste quadro.
  const prefix=chars.slice(0,best).join('');
  const lastSpace=prefix.lastIndexOf(' ');
  if(lastSpace>=Math.floor(best*0.5))stop=lastSpace+1;
  return {
    head:chars.slice(0,stop).join(''),
    rest:chars.slice(stop).join(''),
  };
}
