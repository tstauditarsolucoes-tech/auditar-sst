import 'package:flutter/material.dart';

import '../services/cipa_member_identity.dart';

/// Cabeçalho para a futura área individual de membros da CIPA.
/// Recebe exclusivamente um perfil previamente validado pelo serviço.
/// Não autentica, concede poderes ou lê dados de outras empresas.
class CipaMemberAccessHeader extends StatelessWidget {
  const CipaMemberAccessHeader({
    super.key,
    required this.profile,
    required this.companyName,
    required this.mandateLabel,
  });

  final CipaMemberAccessProfile profile;
  final String companyName;
  final String mandateLabel;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.badge_outlined),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Meu acesso à CIPA',
                    style: TextStyle(fontWeight: FontWeight.w800),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(
              profile.displayName,
              key: const ValueKey('cipa-member-identity-name-role'),
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w900,
                  ),
            ),
            if (profile.detailLine.isNotEmpty) ...[
              const SizedBox(height: 4),
              Text(
                profile.detailLine,
                key: const ValueKey('cipa-member-job-representation'),
              ),
            ],
            const SizedBox(height: 8),
            Text(
              '$companyName • Mandato: $mandateLabel',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 8),
            const Text(
              'Ações de membros exigem autorização individual e validação '
              'no servidor. Este cabeçalho não concede acesso.',
              style: TextStyle(fontSize: 11.5),
            ),
          ],
        ),
      ),
    );
  }
}
