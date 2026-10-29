import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';

class FieldConnectivityBadge extends StatefulWidget {
  const FieldConnectivityBadge({super.key});

  @override
  State<FieldConnectivityBadge> createState() => _FieldConnectivityBadgeState();
}

class _FieldConnectivityBadgeState extends State<FieldConnectivityBadge> {
  bool? online;

  @override
  void initState() {
    super.initState();
    unawaited(_check());
  }

  Future<void> _check() async {
    if (mounted) setState(() => online = null);
    var connected = false;
    try {
      final result = await InternetAddress.lookup('script.google.com')
          .timeout(const Duration(seconds: 3));
      connected = result.isNotEmpty && result.first.rawAddress.isNotEmpty;
    } catch (_) {
      connected = false;
    }
    if (mounted) setState(() => online = connected);
  }

  @override
  Widget build(BuildContext context) {
    final value = online;
    final label = value == null
        ? 'Conferindo conexão'
        : (value ? 'Online' : 'Offline');
    return Tooltip(
      message: '$label • toque para atualizar',
      child: IconButton(
        onPressed: _check,
        icon: value == null
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : Icon(
                value ? Icons.cloud_done_outlined : Icons.cloud_off_outlined,
              ),
      ),
    );
  }
}
