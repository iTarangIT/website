export interface NBFCPartner {
  id: string;
  name: string;
  portfolioCr: number;
  activeLoans: number;
  delinquencyRatePct: number;
  recoveryRatePct: number;
  avgCds: number;
  onlineSharePct: number;
}

export const ecosystemKPIs = {
  connectedNBFCs: 3,
  totalPortfolioCr: 34.6,
  totalBatteries: 12480,
  platformUptimePct: 99.7,
  apiLatencyMs: 112,
  iotConnectivityPct: 94.3,
  alertVolume24h: 2848,
};

export const nbfcPartners: NBFCPartner[] = [
  { id: "nbfc-1", name: "Kosh Lending Co.", portfolioCr: 12.4, activeLoans: 4856, delinquencyRatePct: 9.2, recoveryRatePct: 64.2, avgCds: 18, onlineSharePct: 94.7 },
  { id: "nbfc-2", name: "Anvay Finserv", portfolioCr: 14.8, activeLoans: 5320, delinquencyRatePct: 7.8, recoveryRatePct: 68.5, avgCds: 15, onlineSharePct: 95.6 },
  { id: "nbfc-3", name: "Udaan Microfin", portfolioCr: 7.4, activeLoans: 2304, delinquencyRatePct: 11.5, recoveryRatePct: 58.2, avgCds: 24, onlineSharePct: 92.8 },
];
