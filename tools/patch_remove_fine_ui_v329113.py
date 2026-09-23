#!/usr/bin/env python3
"""Remove fine-entry UI while preserving historical metadata and database compatibility."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'lib/screens/checklist_screen.dart'
s=p.read_text(encoding='utf-8')
marker="'Multa por descumprimento • opcional'"
assert s.count(marker)==1, 'Expected one fine card'
idx=s.index(marker)
start=s.rfind('                                      Container(\n',0,idx)
assert start>=0 and idx-start<4000, 'Fine container not isolated'
after=s.index('                                      const SizedBox(height: 12),',idx)
assert s[after-44:after].strip().endswith('),'), 'Fine block boundary changed'
# Remove the fine block and its following spacer, not the NC classification.
end=after+len('                                      const SizedBox(height: 12),\n')
section=s[start:end]
assert 'fineAmounts[item.id]' in section and 'fineBases[item.id]' in section
assert 'fineShowInReport[item.id]' in section
assert 'DropdownButtonFormField' not in section
s=s[:start]+('                                      // Multa retirada da interface: registros legados preservados.\n')+s[end:]
assert marker not in s and 'Icons.gavel_outlined' not in s
# Never re-enable an old fine for client PDF if this record is edited.
old="'showInReport': fineCents != null && (fineShowInReport[itemId] ?? false),"
assert old in s
s=s.replace(old,"'showInReport': false, // compatibilidade com o histórico; não exibir em PDF",1)
p.write_text(s,encoding='utf-8',newline='\n')
print('CHECKLIST_FINE_UI_REMOVED_WITH_HISTORY_PRESERVED')
