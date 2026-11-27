// Server-only adapter. Never expose organizer credentials or invoke from public member routes.
const RESOURCE = /^[A-Za-z0-9_-]{1,160}$/;
const resource = (value, prefix) => typeof value === 'string' &&
  value.startsWith(prefix) && RESOURCE.test(value.slice(prefix.length));
const instant = x => {const t = Date.parse(x); if(!Number.isFinite(t)) throw new Error('INVALID_TIME');return t;};
export function meetingLink(value) {
  const u = new URL(value);
  if(u.protocol !== 'https:' || u.hostname !== 'meet.google.com' ||
    u.port || u.username || u.password || !/^\/[a-z]{3}-[a-z]{4}-[a-z]{3}\/?$/.test(u.pathname))
    throw new Error('INVALID_MEET_LINK');
  return 'https://meet.google.com'+u.pathname.replace(/\/$/,'');
}
async function pages(path, field, get, filters={}) {
  const rows=[];let token='';const seen=new Set();
  do {
    if(seen.has(token)||seen.size>=100) throw new Error('INCOMPLETE_PAGINATION');
    seen.add(token);
    const data=await get(path,{pageSize:'100',...filters,...(token?{pageToken:token}:{})});
    if(!data||typeof data!=='object'||(data[field]!==undefined&&!Array.isArray(data[field])))
      throw new Error('INVALID_MEET_RESPONSE');
    rows.push(...(data[field]??[]));
    token=data.nextPageToken??'';
    if(typeof token!=='string') throw new Error('INVALID_PAGE_TOKEN');
  }while(token);
  return rows;
}
export function createGoogleReader(accessToken, fetcher=fetch) {
  if(typeof accessToken!=='string'||!accessToken.trim()||/[\r\n]/.test(accessToken))throw new Error('GOOGLE_AUTH_REQUIRED');
  return async (path,params={})=>{
    if(!/^(spaces\/[A-Za-z0-9_-]+|conferenceRecords(?:\/[A-Za-z0-9_-]+(?:\/participants(?:\/[A-Za-z0-9_-]+\/participantSessions)?)?)?)$/.test(path))
      throw new Error('INVALID_GOOGLE_RESOURCE');
    const url=new URL('https://meet.googleapis.com/v2/'+path);
    for(const [k,v] of Object.entries(params))url.searchParams.set(k,v);
    const reply=await fetcher(url,{method:'GET',headers:{Authorization:'Bearer '+accessToken,Accept:'application/json'},redirect:'error',signal:AbortSignal.timeout(15000)});
    if(!reply.ok) throw new Error('MEET_HTTP_'+reply.status);
    return reply.json();
  };
}
function merge(sessions,from,to,asOf) {
  const ids=new Set();let open=false;const intervals=[];
  for(const s of sessions){
    if(typeof s.name!=='string'||ids.has(s.name)) continue;
    ids.add(s.name);
    const a=instant(s.startTime);
    const b=s.endTime?instant(s.endTime):asOf;
    if(b<a)throw new Error('INVALID_SESSION_INTERVAL');
    const left=Math.max(a,from),right=Math.min(b,to,asOf);
    if(right>left||right===left&&a>=from&&a<=to){
      intervals.push([left,right]);if(!s.endTime&&asOf<=to)open=true;
    }
  }
  intervals.sort((a,b)=>a[0]-b[0]);
  const combined=[];
  for(const x of intervals){
    const last=combined.at(-1);if(last&&x[0]<=last[1])last[1]=Math.max(last[1],x[1]);else combined.push([...x]);
  }
  return {firstEntry:combined.length?new Date(combined[0][0]).toISOString():null,
    lastExit:combined.length&&!open?new Date(combined.at(-1)[1]).toISOString():null,
    durationSeconds:Math.floor(combined.reduce((a,[s,e])=>a+e-s,0)/1000),currentlyConnected:open,
    observed:combined.length>0,sessionCount:ids.size};
}
// The server must load meeting, roster and verified Google account mappings from trusted storage,
// never from member input. Callers must scope organizer permission to company + mandate + meeting.
export async function collectAttendance({actor,meetingId,loadAuthorizedMeeting,get,now=new Date().toISOString()}) {
  const m=await loadAuthorizedMeeting(actor,meetingId);
  if(!m||m.id!==meetingId||!m.companyId||!m.mandateId||m.organizerAuthorized!==true)
    throw new Error('ACCESS_DENIED');
  if(!['online','hybrid'].includes(m.mode)) throw new Error('NOT_ONLINE');
  const link=meetingLink(m.meetUrl),code=link.split('/').at(-1);
  const start=instant(m.windowStart),end=instant(m.windowEnd),asOf=instant(now);
  if(end<=start||end-start>24*60*60*1000)throw new Error('INVALID_MEETING_WINDOW');
  if(!Array.isArray(m.roster)||m.roster.some(r=>r.companyId!==m.companyId||r.mandateId!==m.mandateId||!r.memberId))
    throw new Error('INVALID_ROSTER_SCOPE');
  if(new Set(m.roster.map(r=>r.memberId)).size!==m.roster.length)throw new Error('DUPLICATE_MEMBER');
  const space=await get('spaces/'+code,{});
  if(!resource(space?.name,'spaces/'))throw new Error('INVALID_SPACE');
  // Explicit bound instance prevents reuse of the same meeting link from conflating meetings.
  if(!resource(m.conferenceRecord,'conferenceRecords/')){
    const candidates=await pages('conferenceRecords','conferenceRecords',get,{
      filter:'space.name = "'+space.name+'" AND start_time>="'+new Date(start).toISOString()+'" AND start_time<="'+new Date(end).toISOString()+'"'});
    return {status:'awaiting_binding',meetingId,source:'google_meet',candidates:candidates.filter(c=>resource(c.name,'conferenceRecords/')&&c.space===space.name&&instant(c.startTime)>=start&&instant(c.startTime)<=end).map(c=>({name:c.name,startTime:c.startTime,endTime:c.endTime??null}))};
  }
  const c=await get(m.conferenceRecord,{});
  if(c?.name!==m.conferenceRecord||c.space!==space.name||instant(c.startTime)<start||instant(c.startTime)>end)throw new Error('CONFERENCE_SCOPE_MISMATCH');
  const boundEnd=c.endTime?instant(c.endTime):asOf;
  if(boundEnd<instant(c.startTime))throw new Error('INVALID_CONFERENCE_INTERVAL');
  const roster=m.roster;const verified=new Map();
  for(const r of roster){
    if(r.googleIdentityVerified===true&&resource(r.googleUser,'users/')){
      const v=verified.get(r.googleUser)??[];v.push(r.memberId);verified.set(r.googleUser,v);
    }
  }
  const groups=new Map(),unmatched=[];
  const participants=await pages(c.name+'/participants','participants',get);
  for(const p of participants){
    if(!resource(p.name,c.name+'/participants/'))throw new Error('PARTICIPANT_SCOPE_MISMATCH');
    const sessions=await pages(p.name+'/participantSessions','participantSessions',get);
    if(sessions.some(s=>!resource(s.name,p.name+'/participantSessions/')))throw new Error('SESSION_SCOPE_MISMATCH');
    const matches=verified.get(p.signedinUser?.user)??[];
    if(matches.length!==1){
      unmatched.push({participantRef:p.name,displayName:p.signedinUser?.displayName??p.anonymousUser?.displayName??'Participante não identificado',...merge(sessions,instant(c.startTime),Math.min(end,boundEnd),asOf),status:'needs_review'});
    }else{
      const id=matches[0];groups.set(id,[...(groups.get(id)??[]),...sessions]);
    }
  }
  const rows=roster.map(r=>{
    const s=merge(groups.get(r.memberId)??[],instant(c.startTime),Math.min(end,boundEnd),asOf);
    return {memberId:r.memberId,displayName:r.displayName,...s,status:s.observed?'observed_online':'not_observed_online',requiresReview:true};
  });
  return {status:c.endTime?'ended':'active',meetingId,companyId:m.companyId,mandateId:m.mandateId,source:'google_meet',conferenceRecord:c.name,checkedAt:now,rows,unmatched,requiresReview:true};
}
