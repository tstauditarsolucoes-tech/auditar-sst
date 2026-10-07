#!/usr/bin/env python3
"""Regressão da exclusão definitiva de empresa somente ADM."""
from pathlib import Path
import re
import sys

if len(sys.argv) < 3:
    raise SystemExit(
        "uso: regression_admin_company_permanent_delete_v329171_v33094.py "
        "<APP_DIR> <android|windows>"
    )

root = Path(sys.argv[1])
platform = sys.argv[2].strip().lower()
db = (root / "lib/database.dart").read_text(encoding="utf-8")
screen = (root / "lib/screens/companies_screen.dart").read_text(encoding="utf-8")
service = (root / "lib/services/admin_company_deletion_service.dart").read_text(
    encoding="utf-8"
)
pub = (root / "pubspec.yaml").read_text(encoding="utf-8")

expected = "3.29.171+313" if platform == "android" else "3.30.94+281"

checks = {
    "version": f"version: {expected}" in pub,
    "normal_db_method": "Future<bool> deleteCompanyIfUnused(String companyId)" in db,
    "normal_ui_method": "Future<void> _deleteCompany(Company company)" in screen,
    "normal_ui_still_calls_safe_method": (
        "AppDatabase.instance.deleteCompanyIfUnused(company.id)" in screen
    ),
    "normal_block_message": (
        "A empresa possui vistorias. Desative-a em vez de excluir." in screen
    ),
    "admin_database_method": "deleteCompanyPermanentlyAdmin" in db,
    "admin_service": "class AdminCompanyDeletionService" in service,
    "admin_guard_service": "if (!AuthService.isAdmin)" in service,
    "admin_guard_menu": "if (AuthService.isAdmin)" in screen,
    "admin_menu_value": "delete_permanent_admin" in screen,
    "typed_confirmation": "Digite exatamente:" in screen,
    "irreversible_warning": "Esta ação não pode ser desfeita" in screen,
    "admin_route": "AdminCompanyDeletionService.deletePermanently" in screen,
    "sync_existing_call_only": "DeviceSyncService.synchronize(force: true)" in screen,
    "sync_scope_preserved": "table.startsWith('device_sync_')" in db,
    "company_deleted_last": "txn.delete(\n        'companies'" in db,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    raise AssertionError("regressão exclusão ADM: " + repr(failed))

# O método comum deve continuar tendo o bloqueio de histórico.
normal_match = re.search(
    r"Future<bool> deleteCompanyIfUnused\(String companyId\) async \{(.*?)\n  \}",
    db,
    flags=re.S,
)
if not normal_match:
    raise AssertionError("não foi possível inspecionar deleteCompanyIfUnused")
normal = normal_match.group(1)
for required in (
    "inspectionCount",
    "workerCount",
    "cipaCount",
    "routineCount",
    "return false",
):
    if required not in normal:
        raise AssertionError("bloqueio normal enfraquecido: " + required)

# A rotina nova é destrutiva, mas não pode alterar schema.
admin_start = db.find("Future<int> deleteCompanyPermanentlyAdmin")
admin_end = db.find("\n  // WORKSITES", admin_start)
admin = db[admin_start:admin_end if admin_end > admin_start else len(db)]
for forbidden in ("CREATE TABLE", "ALTER TABLE", "DROP TABLE"):
    if forbidden in admin:
        raise AssertionError("rotina ADM alterou schema: " + forbidden)

print("ADMIN_PERMANENT_DELETE_REGRESSION_OK")
print("NORMAL_AND_TECHNICIAN_BLOCK_PRESERVED_OK")
print("ADMIN_ONLY_MENU_AND_SERVICE_GUARD_OK")
print("NO_SCHEMA_CHANGE_OK")
