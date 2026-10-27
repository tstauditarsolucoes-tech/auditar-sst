#!/usr/bin/env python3
"""Fix Ronda edit preservation and make Ronda photo AI use the fast checklist path.
Does not touch DB schema, device sync, media sync, authentication, GS or other AI flows.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1])
platform=sys.argv[2]
assert platform in ('android','windows')

def read(rel): return (root/rel).read_text(encoding='utf-8')
def write(rel,s):
    p=root/rel
    p.write_text(s,encoding='utf-8',newline='\n')
def one(s,a,b,label):
    c=s.count(a)
    if c!=1: raise RuntimeError(f'{label}: expected once, found {c}')
    return s.replace(a,b,1)

# 1) Editing an existing Ronda record must retain Ronda metadata.
rel='lib/screens/safety_observations_screen.dart'
s=read(rel)
old="""    final payload = <String, dynamic>{
      'observationKind': observationKind,"""
new="""    // Preserve metadata that belongs to the original record (roundId,
    // roundStartedAt, aiStatus, source, etc.). Rebuilding the payload from
    // scratch made edited Ronda records disappear from the Ronda history.
    final payload = <String, dynamic>{
      ...?widget.existing?.payload,
      'observationKind': observationKind,"""
s=one(s,old,new,'preserve existing Ronda payload')

old="""    await AppDatabase.instance.upsertSstRecord(record);
    await ManagementPanelService.syncCompany(widget.company);
    if (!mounted) return;
    setState(() => saving = false);
    Navigator.pop(context, true);"""
new="""    await AppDatabase.instance.upsertSstRecord(record);
    // Saving is local-first. A slow web panel must never keep the edit screen
    // spinning or tempt the user to leave before receiving confirmation.
    if (!mounted) return;
    setState(() => saving = false);
    Navigator.pop(context, true);
    // Keep the existing management-panel refresh, but do not block the save.
    ManagementPanelService.syncCompany(widget.company).catchError((_) =>
      const ManagementPanelSyncResult(success:false, message:'Atualização do painel pendente.'));
"""
s=one(s,old,new,'non blocking management panel after save')
write(rel,s)

# 2) Ronda photo AI should use the same single fast model path as the quick
# checklist request; no long 95s deferred fallback chain.
rel='lib/services/ai_assistant_service.dart'
s=read(rel)
needle="""      final reply = await _send({
        'mode': 'checklist_photo',
        'rondaDeferred': true,
        'companyName': company.name,"""
replacement="""      final reply = await _send({
        'mode': 'checklist_photo',
        // Use the fast single-model photo path. The record is already saved
        // locally, so a failed attempt remains pending and can be retried.
        'rondaDeferred': false,
        'companyName': company.name,"""
s=one(s,needle,replacement,'Ronda fast AI mode')
write(rel,s)

# Version bump only; no schema migration.
p=root/'pubspec.yaml'; v=p.read_text(encoding='utf-8')
if platform=='android':
    if 'version: 3.29.116+258' in v: v=v.replace('version: 3.29.116+258','version: 3.29.117+259',1)
    elif 'version: 3.29.116' in v: v=v.replace('version: 3.29.116','version: 3.29.117',1)
    else: raise RuntimeError('Android version marker not found: '+[x for x in v.splitlines() if x.startswith('version:')][0])
else:
    if 'version: 3.30.40+227' in v: v=v.replace('version: 3.30.40+227','version: 3.30.41+228',1)
    elif 'version: 3.30.40' in v: v=v.replace('version: 3.30.40','version: 3.30.41',1)
    else: raise RuntimeError('Windows version marker not found: '+[x for x in v.splitlines() if x.startswith('version:')][0])
p.write_text(v,encoding='utf-8',newline='\n')

# Guards.
safety=read('lib/screens/safety_observations_screen.dart')
ai=read('lib/services/ai_assistant_service.dart')
assert '...?widget.existing?.payload' in safety
assert "ManagementPanelService.syncCompany(widget.company).catchError" in safety
assert "'rondaDeferred': false,\n        'companyName': company.name" in ai
# Checklist fast implementation itself remains otherwise untouched.
assert ai.count("static Future<AiAssistantReply> analyzeSafetyObservationPhoto") == 1
print('RONDA_EDIT_AND_FAST_AI_FIX_OK', platform)
