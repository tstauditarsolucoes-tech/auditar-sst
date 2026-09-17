#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else 'app/Auditar_SST_v1_5_dashboard')
path = root / 'lib/widgets/auditar_brand_logo.dart'
path.write_text('''import 'package:flutter/material.dart';

import '../brand.dart';

class AuditarBrandLogo extends StatelessWidget {
  final double iconSize;
  final bool showSubtitle;
  final Color? textColor;
  final bool compact;
  final bool onDark;

  const AuditarBrandLogo({
    super.key,
    this.iconSize = 44,
    this.showSubtitle = true,
    this.textColor,
    this.compact = false,
    this.onDark = false,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveIconSize = compact ? iconSize * .82 : iconSize;
    final color = textColor ?? (onDark ? Colors.white : AuditarBrand.navyDark);
    final secondaryColor = onDark
        ? Colors.white.withValues(alpha: .78)
        : color.withValues(alpha: .72);

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Image.asset(
          AuditarBrand.iconAsset,
          width: effectiveIconSize,
          height: effectiveIconSize,
          fit: BoxFit.contain,
        ),
        SizedBox(width: compact ? 7 : 10),
        Flexible(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'SST Gestão',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: color,
                  fontWeight: FontWeight.w900,
                  fontSize: effectiveIconSize * .40,
                  letterSpacing: -.3,
                ),
              ),
              if (showSubtitle && !compact)
                Text(
                  'Segurança do Trabalho',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: secondaryColor,
                    fontWeight: FontWeight.w600,
                    fontSize: effectiveIconSize * .20,
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }
}
''', encoding='utf-8', newline='\n')
print('Componente de marca neutro mantém parâmetros compact/onDark usados pelas telas existentes.')
