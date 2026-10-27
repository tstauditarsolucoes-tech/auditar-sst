#!/usr/bin/env python3
from pathlib import Path
import sys

root=Path(sys.argv[1])
p=root/'lib/services/training_list_import_service.dart'
text=p.read_text(encoding='utf-8')

old="""        final from = i > 0 ? i - 1 : i;
        final to = i + 2 < lines.length ? i + 2 : lines.length - 1;
        final context = lines.sublist(from, to + 1).join(' ');
        final dates = _extractDates(context);
        final code = _detectTrainingCode(context).isNotEmpty
            ? _detectTrainingCode(context)
            : globalCode;
        final title = globalTitle;
        result.add(
          _RawTrainingRow(
            sourceLine: i + 1,
            name: worker.name,
            role: worker.role,
            code: code,
            title: title,
            trainingDate:
                dates.isNotEmpty ? dates.first : globalDates.$1,
            expiryDate:
                dates.length > 1 ? dates[1] : globalDates.$2,
          ),
        );
"""

new="""        final from = i > 2 ? i - 2 : 0;
        final to = i + 2 < lines.length ? i + 2 : lines.length - 1;
        final contextLines = lines.sublist(from, to + 1);
        final context = contextLines.join(' ');
        final rowDates = _extractDates(lines[i]);
        final labeledContextDates = _detectGlobalDates(contextLines);
        final code = _detectTrainingCode(context).isNotEmpty
            ? _detectTrainingCode(context)
            : globalCode;
        final title = globalTitle;
        result.add(
          _RawTrainingRow(
            sourceLine: i + 1,
            name: worker.name,
            role: worker.role,
            code: code,
            title: title,
            trainingDate: rowDates.isNotEmpty
                ? rowDates.first
                : (labeledContextDates.$1 ?? globalDates.$1),
            expiryDate: rowDates.length > 1
                ? rowDates[1]
                : (labeledContextDates.$2 ?? globalDates.$2),
          ),
        );
"""

if new not in text:
    if old not in text:
        raise RuntimeError('Trecho de datas do PDF não localizado')
    text=text.replace(old,new,1)

p.write_text(text,encoding='utf-8',newline='\n')
assert 'final rowDates = _extractDates(lines[i]);' in text
assert 'labeledContextDates.$1 ?? globalDates.$1' in text
assert 'labeledContextDates.$2 ?? globalDates.$2' in text
print('TRAINING_LIST_IMPORT_DATE_FIX_V32973_OK')
