import 'package:flutter/material.dart';

import 'brand.dart';
import 'screens/splash_screen.dart';
import 'services/sync_coordinator.dart';
import 'services/web_service_config.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await WebServiceConfig.applyEmbeddedConfiguration();
  runApp(const AuditarSstApp());
}

class AuditarSstApp extends StatelessWidget {
  const AuditarSstApp({super.key});

  @override
  Widget build(BuildContext context) {
    const scheme = ColorScheme(
      brightness: Brightness.light,
      primary: AuditarBrand.navy,
      onPrimary: Colors.white,
      secondary: AuditarBrand.green,
      onSecondary: Colors.white,
      error: AuditarBrand.danger,
      onError: Colors.white,
      surface: Colors.white,
      onSurface: Color(0xFF182230),
    );

    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Auditar SST',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: scheme,
        scaffoldBackgroundColor: AuditarBrand.background,
        appBarTheme: const AppBarTheme(
          backgroundColor: AuditarBrand.navyDark,
          foregroundColor: Colors.white,
          centerTitle: false,
          elevation: 0,
          scrolledUnderElevation: 0,
          titleTextStyle: TextStyle(
            color: Colors.white,
            fontSize: 18,
            fontWeight: FontWeight.w800,
          ),
        ),
        cardTheme: CardThemeData(
          color: Colors.white,
          elevation: 0,
          shadowColor: const Color(0x180E1A43),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: const BorderSide(color: AuditarBrand.line),
          ),
        ),
        dividerColor: AuditarBrand.line,
        inputDecorationTheme: InputDecorationTheme(
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 14,
            vertical: 13,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(13),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(13),
            borderSide: const BorderSide(color: AuditarBrand.line),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(13),
            borderSide: const BorderSide(
              color: AuditarBrand.green,
              width: 1.7,
            ),
          ),
          filled: true,
          fillColor: Colors.white,
          labelStyle: const TextStyle(color: AuditarBrand.neutral),
        ),
        filledButtonTheme: FilledButtonThemeData(
          style: FilledButton.styleFrom(
            backgroundColor: AuditarBrand.greenDark,
            foregroundColor: Colors.white,
            minimumSize: const Size(0, 48),
            textStyle: const TextStyle(fontWeight: FontWeight.w800),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(13),
            ),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: AuditarBrand.navy,
            side: const BorderSide(color: AuditarBrand.line),
            minimumSize: const Size(0, 46),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(13),
            ),
          ),
        ),
        floatingActionButtonTheme: const FloatingActionButtonThemeData(
          backgroundColor: AuditarBrand.greenDark,
          foregroundColor: Colors.white,
        ),
        navigationBarTheme: NavigationBarThemeData(
          backgroundColor: Colors.white,
          indicatorColor: AuditarBrand.greenSoft,
          height: 66,
          labelTextStyle: WidgetStateProperty.resolveWith((states) {
            final selected = states.contains(WidgetState.selected);
            return TextStyle(
              color: selected ? AuditarBrand.greenDark : AuditarBrand.neutral,
              fontSize: 11,
              fontWeight: selected ? FontWeight.w800 : FontWeight.w600,
            );
          }),
          iconTheme: WidgetStateProperty.resolveWith((states) {
            final selected = states.contains(WidgetState.selected);
            return IconThemeData(
              color: selected ? AuditarBrand.greenDark : AuditarBrand.neutral,
            );
          }),
        ),
        chipTheme: const ChipThemeData(
          side: BorderSide(color: AuditarBrand.line),
          backgroundColor: Colors.white,
          selectedColor: AuditarBrand.greenSoft,
          labelStyle: TextStyle(fontWeight: FontWeight.w700),
        ),
      ),
      home: const SyncCoordinator(child: SplashScreen()),
    );
  }
}
