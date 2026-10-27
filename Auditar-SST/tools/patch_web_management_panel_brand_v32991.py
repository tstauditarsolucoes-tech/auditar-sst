from pathlib import Path
import re, sys
if len(sys.argv) < 2:
    raise SystemExit('uso: patch_web_management_panel_brand_v32991.py <APP_DIR>')
root=Path(sys.argv[1])/'painel_web_google_apps_script'
code=(root/'Code.gs').read_text(encoding='utf-8')
idx=(root/'Index.html').read_text(encoding='utf-8')

helper=r'''function panelCompanyLogoDataUri_(companyId) {
  const id = String(companyId || '').trim();
  if (!id) return '';

  let bestFileId = '';
  let bestVersion = -1;
  try {
    const sheet = ensureDeviceSyncStorage_();
    const lastRow = sheet.getLastRow();
    const width = Math.max(8, sheet.getLastColumn());
    const rows = lastRow >= 2
      ? sheet.getRange(2, 1, lastRow - 1, width).getValues()
      : [];
    rows.forEach(row => {
      if (String(row[0] || '') !== 'media_assets') return;
      const deleted = row[2] === true || String(row[2] || '').toLowerCase() === 'true';
      if (deleted) return;
      let payload = {};
      try { payload = JSON.parse(String(row[7] || '{}')); } catch (_) {}
      const rowCompany = String(
        payload.company_id || payload.companyId || row[8] || ''
      ).trim();
      const entityType = String(
        payload.entity_type || payload.entityType || ''
      ).trim().toLowerCase();
      const entityId = String(
        payload.entity_id || payload.entityId || ''
      ).trim();
      const fileId = String(
        payload.drive_file_id || payload.driveFileId || ''
      ).trim();
      const version = Number(row[3]) || 0;
      if (rowCompany === id && entityType === 'company_logo' &&
          entityId === id && fileId && version >= bestVersion) {
        bestVersion = version;
        bestFileId = fileId;
      }
    });
  } catch (_) {
    // O painel continua abrindo mesmo se a tabela de mídia ainda não existir.
  }

  if (bestFileId) {
    try {
      const data = panelLogoDataUriFromFile_(DriveApp.getFileById(bestFileId), id);
      if (data) return data;
    } catch (_) {}
  }

  const names = [
    'company_logo - ' + id + '.png',
    'company_logo - ' + id + '.jpg',
    'company_logo - ' + id + '.webp'
  ];
  for (let i = 0; i < names.length; i++) {
    try {
      const files = DriveApp.getFilesByName(names[i]);
      while (files.hasNext()) {
        const data = panelLogoDataUriFromFile_(files.next(), id);
        if (data) return data;
      }
    } catch (_) {}
  }
  return '';
}

function panelLogoDataUriFromFile_(file, companyId) {
  if (!file) return '';
  let description = '';
  try { description = String(file.getDescription() || ''); } catch (_) {}
  const expectedName = 'company_logo - ' + companyId;
  const validOwner = description.indexOf('Auditar SST mídia | company:' + companyId) >= 0 ||
    String(file.getName() || '').indexOf(expectedName) === 0;
  if (!validOwner) return '';

  let blob;
  try { blob = file.getBlob(); } catch (_) { return ''; }
  let mimeType = String(blob.getContentType() || '').toLowerCase();
  if (['image/jpeg', 'image/png', 'image/webp'].indexOf(mimeType) < 0) return '';
  let bytes = blob.getBytes();

  // O HTML do painel precisa continuar leve. Quando disponível, usa a miniatura
  // privada gerada pelo Drive em vez de publicar o arquivo original pesado.
  if (bytes.length > 1600000) {
    try {
      const thumb = file.getThumbnail();
      if (thumb) {
        const thumbBytes = thumb.getBytes();
        const thumbType = String(thumb.getContentType() || '').toLowerCase();
        if (thumbBytes.length && thumbBytes.length < bytes.length &&
            ['image/jpeg', 'image/png', 'image/webp'].indexOf(thumbType) >= 0) {
          blob = thumb;
          bytes = thumbBytes;
          mimeType = thumbType;
        }
      }
    } catch (_) {}
  }
  if (!bytes.length || bytes.length > 3000000) return '';
  return 'data:' + mimeType + ';base64,' + Utilities.base64Encode(bytes);
}

'''
anchor='function doGet(e) {'
assert anchor in code
if 'function panelCompanyLogoDataUri_' not in code:
    code=code.replace(anchor,helper+anchor,1)
old="""  const template = HtmlService.createTemplateFromFile('Index');
  template.payloadJson = safeJsonForHtml_(publicPanelPayload_(record.payload));
  return template.evaluate()
    .setTitle('Painel Gerencial SST')
"""
new="""  const template = HtmlService.createTemplateFromFile('Index');
  const publicPayload = publicPanelPayload_(record.payload);
  if (publicPayload.company && typeof publicPayload.company === 'object') {
    publicPayload.company.logoDataUri = panelCompanyLogoDataUri_(
      String(publicPayload.company.id || '')
    );
  }
  template.payloadJson = safeJsonForHtml_(publicPayload);
  const publicCompanyName = publicPayload.company && publicPayload.company.name
    ? String(publicPayload.company.name)
    : 'Empresa';
  return template.evaluate()
    .setTitle(publicCompanyName + ' • Painel Gerencial SST')
"""
assert old in code
code=code.replace(old,new,1)

idx=idx.replace('<!-- Auditar SST • Painel Executivo Gerencial v3.29.28 -->','<!-- Auditar SST • Painel Executivo Gerencial Web v3.29.91 -->')
css=r'''
    /* Identidade visual dinâmica da empresa */
    .company-logo-shell{display:flex;align-items:center;justify-content:center;min-width:48px;max-width:170px;height:52px;padding:6px;border-radius:14px;background:#fff;box-shadow:0 8px 22px #0612352e;overflow:hidden}
    .company-logo-shell img{display:block;max-width:158px;max-height:40px;width:auto;height:auto;object-fit:contain}
    .company-logo-shell .brand-mark{width:40px;height:40px;border-radius:10px;box-shadow:none}
    .brand-copy{min-width:0}.brand-name{max-width:min(56vw,520px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#fff}.brand-name span{color:inherit}.powered-by{opacity:.84}.company-identity-note{display:inline-flex;align-items:center;gap:6px;margin-top:4px;color:#d9def0;font-size:10px}.company-identity-dot{width:5px;height:5px;border-radius:50%;background:#fff8}
    .topbar{transition:background .25s ease}.tab-button[aria-selected="true"],.period-chip,.count-chip,.agenda-help{transition:color .2s ease,background .2s ease}.overall-badge{backdrop-filter:blur(4px)}
    @media(max-width:560px){.company-logo-shell{max-width:132px;height:46px}.company-logo-shell img{max-width:120px;max-height:34px}.brand-name{font-size:15px;max-width:48vw}.brand-subtitle{font-size:10px}}
    @media print{.company-logo-shell{box-shadow:none;border:1px solid #e1e5ec}.brand-name,.brand-subtitle,.company-identity-note{color:#fff!important}}
'''
assert '</style>' in idx
idx=idx.replace('</style>',css+'\n  </style>',1)
old_brand='''    <div class="brand-row"><div class="brand"><div class="brand-mark" aria-hidden="true">A</div><div><div class="brand-name">Auditar <span>SST</span></div><div class="brand-subtitle">Painel Gerencial</div></div></div><button class="print-button" type="button" onclick="printExecutiveReport()">Gerar Relatório Gerencial PDF</button></div>'''
new_brand='''    <div class="brand-row"><div class="brand"><div class="company-logo-shell" id="companyLogoShell"><img id="companyLogo" alt="Logo da empresa" hidden><div class="brand-mark" id="companyLogoFallback" aria-hidden="true">A</div></div><div class="brand-copy"><div class="brand-name">Painel Gerencial SST</div><div class="brand-subtitle" id="brandCompanySubtitle">Empresa <span class="powered-by">• Auditar</span></div><div class="company-identity-note" id="companyIdentityNote"><span class="company-identity-dot"></span><span>Identidade visual da empresa</span></div></div></div><button class="print-button" type="button" onclick="printExecutiveReport()">Gerar Relatório Gerencial PDF</button></div>'''
assert old_brand in idx
idx=idx.replace(old_brand,new_brand,1)

branding_js=r'''
    function clamp(value,min,max){return Math.max(min,Math.min(max,value))}
    function rgbToHsl(r,g,b){r/=255;g/=255;b/=255;const max=Math.max(r,g,b),min=Math.min(r,g,b);let h=0,s=0;const l=(max+min)/2;if(max!==min){const d=max-min;s=l>.5?d/(2-max-min):d/(max+min);switch(max){case r:h=(g-b)/d+(g<b?6:0);break;case g:h=(b-r)/d+2;break;default:h=(r-g)/d+4}h/=6}return[h,s,l]}
    function hslToRgb(h,s,l){let r,g,b;if(s===0){r=g=b=l}else{const hue=(p,q,t)=>{if(t<0)t+=1;if(t>1)t-=1;if(t<1/6)return p+(q-p)*6*t;if(t<1/2)return q;if(t<2/3)return p+(q-p)*(2/3-t)*6;return p};const q=l<.5?l*(1+s):l+s-l*s,p=2*l-q;r=hue(p,q,h+1/3);g=hue(p,q,h);b=hue(p,q,h-1/3)}return[Math.round(r*255),Math.round(g*255),Math.round(b*255)]}
    function rgbHex(rgb){return'#'+rgb.map(value=>clamp(Math.round(value),0,255).toString(16).padStart(2,'0')).join('')}
    function setupCompanyBranding(company){
      const name=String(company.name||'Empresa').trim()||'Empresa';
      const logo=String(company.logoDataUri||'').trim();
      const initials=name.split(/\s+/).filter(Boolean).slice(0,2).map(part=>part[0]).join('').toUpperCase().slice(0,2)||'A';
      const subtitle=$('brandCompanySubtitle');if(subtitle)subtitle.innerHTML=`${esc(name)} <span class="powered-by">• Auditar</span>`;
      const fallback=$('companyLogoFallback'),image=$('companyLogo'),note=$('companyIdentityNote');
      if(!logo){if(fallback)fallback.textContent=initials;if(image)image.hidden=true;if(note)note.hidden=true;return}
      if(fallback)fallback.textContent=initials;
      image.onload=()=>{image.hidden=false;if(fallback)fallback.hidden=true;if(note)note.hidden=false;applyCompanyTheme(image)};
      image.onerror=()=>{image.hidden=true;if(fallback){fallback.hidden=false;fallback.textContent=initials}if(note)note.hidden=true};
      image.src=logo;
    }
    function applyCompanyTheme(image){
      try{
        const canvas=document.createElement('canvas');canvas.width=48;canvas.height=48;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.clearRect(0,0,48,48);ctx.drawImage(image,0,0,48,48);const data=ctx.getImageData(0,0,48,48).data,bins=new Map();
        for(let i=0;i<data.length;i+=16){const r=data[i],g=data[i+1],b=data[i+2],a=data[i+3];if(a<170)continue;const max=Math.max(r,g,b),min=Math.min(r,g,b),spread=max-min;if(min>238||max<26||spread<16)continue;const key=`${r>>4}-${g>>4}-${b>>4}`,weight=1+Math.floor(spread/36);bins.set(key,(bins.get(key)||0)+weight)}
        if(!bins.size)return;let selected='',best=-1;bins.forEach((value,key)=>{if(value>best){best=value;selected=key}});const parts=selected.split('-').map(Number),r=(parts[0]<<4)+8,g=(parts[1]<<4)+8,b=(parts[2]<<4)+8;let[h,s,l]=rgbToHsl(r,g,b);s=clamp(s,.32,.88);const accent=hslToRgb(h,s,clamp(l,.30,.50)),dark=hslToRgb(h,clamp(s,.26,.9),clamp(l,.14,.27));const root=document.documentElement;root.style.setProperty('--navy',rgbHex(accent));root.style.setProperty('--navy-dark',rgbHex(dark));root.style.setProperty('--navy-soft',`rgba(${accent[0]},${accent[1]},${accent[2]},.09)`);const theme=document.querySelector('meta[name="theme-color"]');if(theme)theme.setAttribute('content',rgbHex(dark));
      }catch(_){/* A identidade visual nunca impede o painel de abrir. */}
    }
'''
anchor_js='    const summary=DATA.summary||{}'
assert anchor_js in idx
idx=idx.replace(anchor_js,branding_js+'\n'+anchor_js,1)
old_line="    $('companyName').textContent=company.name||'Empresa';$('location').textContent=[company.city,company.uf].filter(Boolean).join(' - ');"
new_line="    setupCompanyBranding(company);$('companyName').textContent=company.name||'Empresa';$('location').textContent=[company.city,company.uf].filter(Boolean).join(' - ');"
assert old_line in idx
idx=idx.replace(old_line,new_line,1)

(root/'Code.gs').write_text(code, encoding='utf-8', newline='\n')
(root/'Index.html').write_text(idx, encoding='utf-8', newline='\n')
assert 'function panelCompanyLogoDataUri_' in code
assert 'publicPayload.company.logoDataUri' in code
assert 'setupCompanyBranding(company)' in idx
assert 'applyCompanyTheme(image)' in idx
assert 'Identidade visual da empresa' in idx
print('WEB_MANAGEMENT_PANEL_BRAND_OK')
