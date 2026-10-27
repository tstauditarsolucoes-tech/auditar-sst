/// No item is marked compliant unless the technician explicitly inspected it.
class ChecklistFieldCapturePolicy {
  const ChecklistFieldCapturePolicy._();

  static bool canAddOccurrence(String? status) =>
      status == null || status.isEmpty || status == 'Não Conforme';

  static bool isAdditionalOccurrence(String? status, String currentDescription) =>
      status == 'Não Conforme' && currentDescription.trim().isNotEmpty;

  static bool acceptsEvidence(int current, int added) =>
      current >= 0 && added > 0 && current + added <= 10;
}
