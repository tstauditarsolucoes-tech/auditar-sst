#!/usr/bin/env python3
"""Aplica ajustes de estabilização ao fonte montado do Auditar SST.

O projeto ainda é montado a partir de um ZIP legado + source_overrides.
Este script concentra transformações determinísticas enquanto a migração para
uma árvore fonte canônica não é concluída.
"""
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f"Marcador não encontrado ao aplicar {label}.")
    return text.replace(old, new, 1)


def patch_management_panel(index_path: Path) -> None:
    if not index_path.exists():
        raise RuntimeError(f"Index do painel não encontrado: {index_path}")

    text = index_path.read_text(encoding="utf-8")
    if 'id="tab-agenda"' in text and 'id="agendaTable"' in text:
        return

    agenda_css = """    .agenda-shell{background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden}.agenda-shell summary{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px;cursor:pointer;list-style:none;font-size:14px;font-weight:850;color:var(--navy)}.agenda-shell summary::-webkit-details-marker{display:none}.agenda-shell summary:after{content:'+';font-size:20px;color:var(--muted)}.agenda-shell[open] summary:after{content:'–';font-size:20px;color:var(--muted)}.agenda-body{padding:0 14px 14px}.agenda-preview{display:grid;gap:8px}.agenda-item{display:grid;grid-template-columns:84px minmax(0,1fr) auto;gap:10px;align-items:center;padding:10px 0;border-top:1px solid #edf0f3}.agenda-date{font-size:10px;font-weight:850;color:var(--navy)}.agenda-title{font-size:11.5px;font-weight:800}.agenda-meta{font-size:9.8px;color:var(--muted);margin-top:3px}.agenda-help{margin-top:10px;padding:10px;border-radius:10px;background:var(--navy-soft);color:var(--navy);font-size:10.5px;line-height:1.45}\n"""
    text = replace_once(
        text,
        "    footer{padding:0 14px 28px;color:#8a93a3;font-size:10px;text-align:center}\n",
        agenda_css + "    footer{padding:0 14px 28px;color:#8a93a3;font-size:10px;text-align:center}\n",
        "estilos da agenda",
    )
    text = replace_once(
        text,
        "    @media(max-width:600px){.page{",
        "    @media(max-width:600px){.agenda-item{grid-template-columns:68px minmax(0,1fr)}.agenda-item>.status{grid-column:2;width:fit-content}.page{",
        "responsividade da agenda",
    )
    text = replace_once(
        text,
        '    <button class="tab" id="tab-improvements" role="tab" aria-controls="panel-improvements" aria-selected="false" type="button">Melhorias</button>\n',
        '    <button class="tab" id="tab-improvements" role="tab" aria-controls="panel-improvements" aria-selected="false" type="button">Melhorias</button>\n'
        '    <button class="tab" id="tab-agenda" role="tab" aria-controls="panel-agenda" aria-selected="false" type="button">Agenda SST</button>\n',
        "aba Agenda SST",
    )
    text = replace_once(
        text,
        '      <div style="height:10px"></div><div class="summary-message" id="managementReading"></div>\n',
        '      <div style="height:10px"></div><div class="summary-message" id="managementReading"></div>\n\n'
        '      <div class="section-head"><div><div class="section-title">Agenda semanal SST</div><div class="section-note">Atividades programadas e compromissos registrados no Auditar SST.</div></div><button class="control-link" data-open="tab-agenda" type="button">Abrir agenda completa</button></div>\n'
        '      <details class="agenda-shell" id="agendaWeek" open>\n'
        '        <summary><span>Próximos 7 dias</span><span class="chip" id="agendaWeekCount">0 atividades</span></summary>\n'
        '        <div class="agenda-body"><div class="agenda-preview" id="agendaWeekPreview"></div><div class="agenda-help">Para incluir ou alterar atividades, use <strong>Rotina SST → Agenda SST</strong> no aplicativo ou no computador. O painel atualiza automaticamente.</div></div>\n'
        '      </details>\n',
        "resumo semanal",
    )
    text = replace_once(
        text,
        '    <section id="panel-inspections" role="tabpanel" aria-labelledby="tab-inspections" hidden>\n',
        '    <section id="panel-agenda" role="tabpanel" aria-labelledby="tab-agenda" hidden>\n'
        '      <div class="section-head"><div><div class="section-title">Agenda SST</div><div class="section-note">Planejamento semanal de visitas, treinamentos, reuniões, entregas e demais atividades de SST.</div></div><span class="chip">Sincronizada com o app/PC</span></div>\n'
        '      <div class="mini-grid" id="agendaMini"></div>\n'
        '      <div class="section-head"><div><div class="section-title">Atividades programadas</div><div class="section-note">Ordenadas por data para facilitar o acompanhamento da gerência.</div></div></div>\n'
        '      <div class="table-panel" id="agendaTable"></div>\n'
        '      <div class="agenda-help">Cadastro e edição permanecem protegidos dentro do Auditar SST. No sistema, abra <strong>Rotina SST → Agenda SST</strong>. Este painel é destinado ao acompanhamento gerencial.</div>\n'
        '    </section>\n\n'
        '    <section id="panel-inspections" role="tabpanel" aria-labelledby="tab-inspections" hidden>\n',
        "painel completo da agenda",
    )
    text = replace_once(
        text,
        "    function dueText(days){if(days===null)return'Sem prazo';if(days<0)return`Vencido há ${Math.abs(days)} dia(s)`;if(days===0)return'Vence hoje';return`Vence em ${days} dia(s)`}\n",
        "    function dueText(days){if(days===null)return'Sem prazo';if(days<0)return`Vencido há ${Math.abs(days)} dia(s)`;if(days===0)return'Vence hoje';return`Vence em ${days} dia(s)`}\n"
        "    function isDone(v){const s=upper(v);return s.includes('CONCLU')||s.includes('REALIZ')}\n"
        "    function dayKey(v){const p=dateParts(v);return p?`${p[0]}-${String(p[1]).padStart(2,'0')}-${String(p[2]).padStart(2,'0')}`:''}\n",
        "funções da agenda",
    )
    old_data = "const company=DATA.company||{},summary=DATA.summary||{},trainingSummary=DATA.trainingSummary||{},trainingRecords=DATA.trainingRecords||DATA.trainingAlerts||[],missing=DATA.missingRequiredTrainings||[],workers=DATA.workforceDetails||[],ncs=DATA.openNonConformities||[],actions=DATA.pendingActions||[],sectors=DATA.sectors||[],inspections=DATA.recentInspections||[],extSummary=DATA.extinguisherSummary||{},extinguishers=DATA.extinguishers||[],safetySummary=DATA.safetyObservationSummary||{},safety=DATA.safetyObservations||[],impSummary=DATA.improvementSummary||{},improvements=DATA.improvements||[],activities=DATA.recentActivities||[],trend=DATA.monthlyTrend||[];"
    new_data = "const company=DATA.company||{},summary=DATA.summary||{},trainingSummary=DATA.trainingSummary||{},trainingRecords=DATA.trainingRecords||DATA.trainingAlerts||[],missing=DATA.missingRequiredTrainings||[],workers=DATA.workforceDetails||[],ncs=DATA.openNonConformities||[],actions=DATA.pendingActions||[],sectors=DATA.sectors||[],inspections=DATA.recentInspections||[],extSummary=DATA.extinguisherSummary||{},extinguishers=DATA.extinguishers||[],safetySummary=DATA.safetyObservationSummary||{},safety=DATA.safetyObservations||[],impSummary=DATA.improvementSummary||{},improvements=DATA.improvements||[],agendaSummary=DATA.agendaSummary||{},agenda=DATA.agenda||[],activities=DATA.recentActivities||[],trend=DATA.monthlyTrend||[];"
    text = replace_once(text, old_data, new_data, "dados da agenda")

    agenda_js = """    const agendaSorted=[...agenda].sort((a,b)=>(dayKey(a.date)||'9999').localeCompare(dayKey(b.date)||'9999'));\n    const today=new Date(),todayKey=`${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`,weekLimit=new Date(today.getFullYear(),today.getMonth(),today.getDate()+7),weekLimitKey=`${weekLimit.getFullYear()}-${String(weekLimit.getMonth()+1).padStart(2,'0')}-${String(weekLimit.getDate()).padStart(2,'0')}`;\n    const agendaNext7=agendaSorted.filter(x=>{const k=dayKey(x.date);return k&&k>=todayKey&&k<weekLimitKey&&!isDone(x.status)});\n    $('agendaWeekCount').textContent=`${agendaNext7.length} atividade(s)`;\n    $('agendaWeekPreview').innerHTML=agendaNext7.length?agendaNext7.slice(0,7).map(x=>{const tone=isDone(x.status)?'green':upper(x.status).includes('ANDAMENTO')?'yellow':dayKey(x.date)<todayKey?'red':'purple';return`<div class=\"agenda-item\"><div class=\"agenda-date\">${formatDate(x.date)}</div><div><div class=\"agenda-title\">${esc(x.title||'Atividade SST')}</div><div class=\"agenda-meta\">${esc([x.subtype,x.sector,x.location].filter(Boolean).join(' • ')||'Agenda SST')}</div></div>${status(x.status||'Programado',tone)}</div>`}).join(''):'<div class=\"empty good\">Nenhuma atividade pendente nos próximos 7 dias.</div>';\n    $('agendaMini').innerHTML=[mini('Hoje',num(agendaSummary.today),num(agendaSummary.today)?'yellow':'green'),mini('Próximos 7 dias',num(agendaSummary.next7Days),num(agendaSummary.next7Days)?'yellow':'green'),mini('Atrasadas',num(agendaSummary.overdue),num(agendaSummary.overdue)?'red':'green'),mini('Concluídas',num(agendaSummary.completed),'green')].join('');\n    renderTable('agendaTable',agendaSorted,[['Data',r=>formatDate(r.date)],['Atividade',r=>`<strong>${esc(r.title||'-')}</strong><div class=\"meta\">${esc(r.description||r.notes||'')}</div>`,'html'],['Tipo',r=>r.subtype||'-'],['Setor / local',r=>[r.sector,r.location].filter(Boolean).join(' • ')||'-'],['Responsável',r=>r.responsible||'-'],['Situação',r=>{const overdue=dayKey(r.date)&&dayKey(r.date)<todayKey&&!isDone(r.status);return status(overdue?'Atrasada':r.status||'Programado',overdue?'red':isDone(r.status)?'green':'yellow')},'html']],'Nenhuma atividade cadastrada na Agenda SST.');\n\n"""
    text = replace_once(
        text,
        "    $('improvementMini').innerHTML=",
        agenda_js + "    $('improvementMini').innerHTML=",
        "renderização da agenda",
    )

    index_path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: prepare_sst_source.py <pasta-do-projeto>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    patch_management_panel(root / "painel_web_google_apps_script" / "Index.html")
    print(f"Fonte Auditar SST preparado: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
