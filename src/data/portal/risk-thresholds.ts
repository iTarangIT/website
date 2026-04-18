export interface Threshold {
  id: string;
  label: string;
  description: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  currentValue: number;
  affectsAccounts: number;
}

export const defaultThresholds: Threshold[] = [
  { id: "cds-low", label: "CDS · Low band ceiling", description: "Scores below this are 'Low' risk. Monitor only.", unit: "", min: 10, max: 30, step: 1, currentValue: 20, affectsAccounts: 3122 },
  { id: "cds-med", label: "CDS · Medium band ceiling", description: "Scores below this are 'Medium'. Reminder cadence applies.", unit: "", min: 30, max: 55, step: 1, currentValue: 40, affectsAccounts: 607 },
  { id: "cds-high", label: "CDS · High band ceiling", description: "Scores below this are 'High'. Immobilization eligible.", unit: "", min: 55, max: 75, step: 1, currentValue: 60, affectsAccounts: 890 },
  { id: "pci-floor", label: "PCI · Reliable payer floor", description: "PCI above this is treated as a reliable payer.", unit: "", min: 0.5, max: 0.95, step: 0.01, currentValue: 0.7, affectsAccounts: 4856 },
  { id: "emi-dpd", label: "EMI · Overdue trigger", description: "Days past due before telemetry-linked risk engine engages.", unit: "days", min: 3, max: 30, step: 1, currentValue: 7, affectsAccounts: 1124 },
  { id: "usage-drop", label: "Usage drop threshold", description: "% drop in 7-day km vs prior 7 days to trigger a warning.", unit: "%", min: 20, max: 60, step: 5, currentValue: 40, affectsAccounts: 234 },
  { id: "geo-shift", label: "Geo-shift radius", description: "Km from onboarding location before a geo-shift alert.", unit: "km", min: 50, max: 200, step: 10, currentValue: 100, affectsAccounts: 18 },
];
