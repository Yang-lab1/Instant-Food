export function formatStepLabel(index) {
  return `步骤 ${String(index + 1).padStart(2, "0")}`;
}
