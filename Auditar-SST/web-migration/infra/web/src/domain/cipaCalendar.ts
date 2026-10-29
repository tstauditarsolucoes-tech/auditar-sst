/** Optional personal-calendar export; never sends events or contact data to an external provider. */
export type CipaCalendarMeeting={id:string;title:string;scheduled_at:string;status:string};
export function upcomingCipaMeetings(items:CipaCalendarMeeting[],now:Date=new Date()){
  const timestamp=now.getTime();
  return items.filter(x=>x.status==='planejada'&&Number.isFinite(new Date(x.scheduled_at).getTime())
      &&new Date(x.scheduled_at).getTime()>=timestamp)
    .slice().sort((a,b)=>new Date(a.scheduled_at).getTime()-new Date(b.scheduled_at).getTime());
}
function escapeIcs(value:string){
  return value.replace(/[\r\n]+/g,' ').replace(/\\/g,'\\\\').replace(/;/g,'\\;').replace(/,/g,'\\,');
}
function utc(value:Date){return value.toISOString().replace(/[-:]/g,'').replace(/\.\d{3}/,'');}
export function buildCipaIcs(items:CipaCalendarMeeting[],now:Date=new Date()){
  const active=upcomingCipaMeetings(items,now);
  const parts=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Auditar Solucoes//CIPA Private Portal//PT-BR','CALSCALE:GREGORIAN','METHOD:PUBLISH'];
  for(const m of active){
    // The IDs and names are from tenant-scoped server results, never free-form URLs.
    if(!/^[0-9a-f-]{36}$/i.test(m.id))continue;
    parts.push('BEGIN:VEVENT','UID:'+m.id.toLowerCase()+'@auditar-cipa.local',
      'DTSTAMP:'+utc(now),'DTSTART:'+utc(new Date(m.scheduled_at)),
      'SUMMARY:'+escapeIcs(m.title.slice(0,200)),'DESCRIPTION:Convocacao da CIPA. Confirme os detalhes com a equipe. A inclusao no calendario nao comprova presenca.',
      'BEGIN:VALARM','TRIGGER:-P1D','ACTION:DISPLAY',
      'DESCRIPTION:Lembrete de reuniao da CIPA','END:VALARM','END:VEVENT');
  }
  parts.push('END:VCALENDAR');
  return parts.join('\r\n')+'\r\n';
}
