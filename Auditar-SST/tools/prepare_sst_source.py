#!/usr/bin/env python3
"""Adiciona a Agenda SST ao painel executivo preservando o layout existente."""
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

    agenda_css = """    .agenda-shell{background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden;box-shadow:0 1px 2px #10182808}.agenda-shell summary{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px;cursor:pointer;list-style:none;color:var(--navy);font-size:13px;font-weight:800}.agenda-shell summary::-webkit-details-marker{display:none}.agenda-shell summary:after{content:'+';font-size:20px;color:var(--muted)}.agenda-shell[open] summary:after{content:'–'}.agenda-body{padding:0 14px 14px}.agenda-preview{display:grid;gap:0}.agenda-item{display:grid;grid-template-columns:82px minmax(0,1fr) auto;gap:10px;align-items:center;padding:10px 0;border-top:1px solid #edf0f3}.agenda-date{color:var(--navy);font-size:10px;font-weight:800}.agenda-title{font-size:11.5px;font-weight:800}.agenda-meta{margin-top:3px;color:var(--muted);font-size:9.8px}.agenda-help{margin-top:10px;padding:10px;border-radius:10px;background:var(--navy-soft);color:var(--navy);font-size:10.5px;line-height:1.45}\n"""
    marker = "    @media(max-width:820px){.metric-grid"
    text = replace_once(
        text,
        marker,
        agenda_css + marker,
        "estilos da Agenda SST",
    )

    text = replace_once(
        text,
        '<button class="tab-button" id="tab-improvements" role="tab" aria-controls="panel-improvements" aria-selected="false" type="button">Melhorias</button><button class="tab-button" id="tab-extinguishers"',
        '<button class="tab-button" id="tab-improvements" role="tab" aria-controls="panel-improvements" aria-selected="false" type="button">Melhorias</button><button class="tab-button" id="tab-agenda" role="tab" aria-controls="panel-agenda" aria-selected="false" type="button">Agenda SST</button><button class="tab-button" id="tab-extinguishers"',
        "aba Agenda SST",
    )

    text = replace_once(
        text,
        '      <div class="executive-reading" id="executiveReading"></div>\n',
        '      <div class="executive-reading" id="executiveReading"></div>\n\n'
        '      <div class="section-head spaced"><div><div class="section-title">Agenda semanal SST</div><div class="section-note">Atividades programadas e compromissos dos próximos 7 dias.</div></div><button class="text-button" type="button" data-open-tab="tab-agenda">Ver agenda completa</button></div>\n'
        '      <details class="agenda-shell" id="agendaWeek" open><summary><span>Próximas atividades</span><span class="count-chip" id="agendaWeekCount">0 atividades</span></summary><div class="agenda-body"><div class="agenda-preview" id="agendaWeekPreview"></div><div class="agenda-help">A agenda é cadastrada em <strong>Rotina SST → Agenda SST</strong> no aplicativo ou no computador. Este painel é somente para acompanhamento da gerência.</div></div></details>\n',
        "resumo semanal da Agenda SST",
    )

    text = replace_once(
        text,
        '    <section id="panel-extinguishers" role="tabpanel" aria-labelledby="tab-extinguishers" hidden>',
        '    <section id="panel-agenda" role="tabpanel" aria-labelledby="tab-agenda" hidden><div class="section-title">Agenda SST</div><div class="section-note">Planejamento de visitas, treinamentos, reuniões, entregas e outras atividades de SST.</div><div class="mini-grid" id="agendaMiniMetrics"></div><div class="section-title">Atividades programadas</div><div class="table-panel" id="agendaTable"></div><div class="agenda-help">Cadastro e edição permanecem dentro do Auditar SST. O link da gerência continua somente para consulta.</div></section>\n    <section id="panel-extinguishers" role="tabpanel" aria-labelledby="tab-extinguishers" hidden>',
        "painel completo da Agenda SST",
    )

    text = replace_once(
        text,
        "improvementSummary=DATA.improvementSummary||{},improvements=DATA.improvements||[],company=DATA.company||{}",
        "improvementSummary=DATA.improvementSummary||{},improvements=DATA.improvements||[],agendaSummary=DATA.agendaSummary||{},agenda=DATA.agenda||[],company=DATA.company||{}",
        "dados da Agenda SST",
    )

    agenda_helpers = """    function agendaDone(value){const status=String(value||'').toUpperCase();return status.includes('CONCLU')||status.includes('REALIZ')}function dayKey(value){const parts=dateParts(value);return parts?`${parts[0]}-${String(parts[1]).padStart(2,'0')}-${String(parts[2]).padStart(2,'0')}`:''}\n"""
    text = replace_once(
        text,
        "    function statusChip(text,tone){",
        agenda_helpers + "    function statusChip(text,tone){",
        "funções auxiliares da Agenda SST",
    )

    agenda_js = """    const agendaSorted=[...agenda].sort((a,b)=>(dayKey(a.date)||'9999').localeCompare(dayKey(b.date)||'9999'));const agendaNow=new Date(),agendaTodayKey=`${agendaNow.getFullYear()}-${String(agendaNow.getMonth()+1).padStart(2,'0')}-${String(agendaNow.getDate()).padStart(2,'0')}`,agendaWeekLimit=new Date(agendaNow.getFullYear(),agendaNow.getMonth(),agendaNow.getDate()+7),agendaWeekLimitKey=`${agendaWeekLimit.getFullYear()}-${String(agendaWeekLimit.getMonth()+1).padStart(2,'0')}-${String(agendaWeekLimit.getDate()).padStart(2,'0')}`;const agendaNext7=agendaSorted.filter(item=>{const key=dayKey(item.date);return key&&key>=agendaTodayKey&&key<agendaWeekLimitKey&&!agendaDone(item.status)});$('agendaWeekCount').textContent=plural(agendaNext7.length,'atividade','atividades');$('agendaWeekPreview').innerHTML=agendaNext7.length?agendaNext7.slice(0,7).map(item=>{const status=String(item.status||'Programado'),tone=agendaDone(status)?'green':status.toUpperCase().includes('ANDAMENTO')?'purple':'yellow';return`<div class="agenda-item"><div class="agenda-date">${formatDate(item.date)}</div><div><div class="agenda-title">${esc(item.title||'Atividade SST')}</div><div class="agenda-meta">${esc([item.subtype,item.sector,item.location].filter(Boolean).join(' • ')||'Agenda SST')}</div></div>${statusChip(status,tone)}</div>`}).join(''):'<div class="empty good-empty">Nenhuma atividade pendente nos próximos 7 dias.</div>';$('agendaMiniMetrics').innerHTML=[miniMetric('Hoje',number(agendaSummary.today),number(agendaSummary.today)>0?'yellow':'green'),miniMetric('Próximos 7 dias',number(agendaSummary.next7Days),number(agendaSummary.next7Days)>0?'purple':'green'),miniMetric('Atrasadas',number(agendaSummary.overdue),number(agendaSummary.overdue)>0?'red':'green'),miniMetric('Concluídas',number(agendaSummary.completed),'green')].join('');renderTable('agendaTable',agendaSorted,[['Data',row=>formatDate(row.date)],['Atividade',row=>`<strong>${esc(row.title||'-')}</strong><div class="priority-meta">${esc(row.description||row.notes||'')}</div>`,'html'],['Tipo',row=>row.subtype||'-'],['Setor / local',row=>[row.sector,row.location].filter(Boolean).join(' • ')||'-'],['Responsável',row=>row.responsible||'-'],['Situação',row=>{const overdue=dayKey(row.date)&&dayKey(row.date)<agendaTodayKey&&!agendaDone(row.status);return statusChip(overdue?'ATRASADA':row.status||'PROGRAMADO',overdue?'red':agendaDone(row.status)?'green':'yellow')},'html']],'Nenhuma atividade cadastrada na Agenda SST.');\n"""
    text = replace_once(
        text,
        "    $('improvementMiniMetrics').innerHTML=",
        agenda_js + "    $('improvementMiniMetrics').innerHTML=",
        "renderização da Agenda SST",
    )

    index_path.write_text(text, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: prepare_sst_source.py <pasta-do-projeto>", file=sys.stderr)
        return 2

    root = Path(sys.argv[1]).resolve()
    patch_management_panel(root / "painel_web_google_apps_script" / "Index.html")
    print("Agenda SST adicionada ao painel executivo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
