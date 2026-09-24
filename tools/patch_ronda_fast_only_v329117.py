#!/usr/bin/env python3
"""Limit AI wait ONLY for Ronda Expressa. Preserve checklist, SST and sync."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
service = root / "lib/services/ai_assistant_service.dart"
round_screen = root / "lib/screens/express_round_screen.dart"

def one(text, old, new, label):
    n=text.count(old)
    if n != 1:
        raise RuntimeError(f"{label}: expected one match, found {n}")
    return text.replace(old,new,1)

text=service.read_text(encoding="utf-8")
head, sep, tail=text.partition("  static Future<AiAssistantReply> analyzeSafetyObservationPhoto({")
assert sep, "Ronda photo service not found"
method, suffix, after=tail.partition("  static Future<AiAssistantReply> reviewExpressRound({")
assert suffix, "Ronda method boundary not found"

method=one(method, "    String technicianContext = '',\n  }) async {",
                 "    String technicianContext = '',\n    bool fastRound = false,\n  }) async {",
                 "Ronda-only parameter")
method=one(method, "      final reply = await _send({", "      final request = _send({",
                 "Ronda call")
method=one(method, "        'rondaDeferred': true,",
    """        // No fallback chain for Ronda: its one-photo fast path uses
        // the same first model as the fast Checklist. Other modules retain
        // the original fallback path; this does NOT edit the Checklist.
        'rondaDeferred': !fastRound,""", "Ronda backend mode")
method=one(method,
    """        'images': [image],
      });

      if (!reply.success) return reply;""",
    """        'images': [image],
      });
      // Apps Script redirects and alternative network hops can exceed the
      // per-hop timeout. Do not leave the Ronda UI waiting for minutes.
      // The original photo/record remain intact on timeout.
      final reply = fastRound
          ? await request.timeout(
              const Duration(seconds: 65),
              onTimeout: () => const AiAssistantReply(
                success: false,
                message: 'A análise rápida da Ronda demorou além de 65 segundos. '
                    'A foto e o registro permanecem salvos. Tente novamente depois.',
              ),
            )
          : await request;

      if (!reply.success) return reply;""", "Ronda overall timeout")
text=head+sep+method+suffix+after
assert text.count("'rondaDeferred': true,")==1, "Checklist fallback changed"
assert text.count("'rondaDeferred': !fastRound,")==1
service.write_text(text,encoding="utf-8",newline="\n")

text=round_screen.read_text(encoding="utf-8")
text=one(text,
    """      photoPath: photoPath,
      technicianContext: technicianContext,
    );""",
    """      photoPath: photoPath,
      technicianContext: technicianContext,
      fastRound: true,
    );""", "Ronda capture")
text=one(text,
    """          photoPath: path,
          technicianContext: _recordTechnicianContext(record),
        );""",
    """          photoPath: path,
          technicianContext: _recordTechnicianContext(record),
          fastRound: true,
        );""", "Ronda pending")
assert text.count("fastRound: true,")==2
round_screen.write_text(text,encoding="utf-8",newline="\n")
print("RONDA_FAST_ONLY_OK: two Ronda entry points, 65s cap, checklist unchanged")
