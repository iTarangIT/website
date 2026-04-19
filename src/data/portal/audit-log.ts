export type AuditActionType =
  | "immobilization-requested"
  | "immobilization-approved"
  | "immobilization-rejected"
  | "remobilization"
  | "field-visit"
  | "restructuring-review"
  | "payment-reminder"
  | "threshold-change"
  | "auction-time-extended"
  | "auction-time-reduced"
  | "auction-paused"
  | "auction-cancelled"
  | "reserve-price-set"
  | "winning-bid-approved"
  | "score-override"
  | "data-export"
  | "pii-access"
  | "consent-withdraw"
  | "bid-placed"
  | "ai-call-placed";

export type AuditStatus = "completed" | "pending-approval" | "rejected";

export interface AuditEntry {
  id: string;
  timestamp: string;          // "2026-04-18 10:42 IST"
  actionType: AuditActionType;
  actionLabel: string;
  entity: string;             // IMEI or loan id or "-"
  reasonCode: string;
  requestedBy: string;
  approvedBy: string | null;
  status: AuditStatus;
  details?: string;
  beforeValue?: string;
  afterValue?: string;
}

export const seedAuditLog: AuditEntry[] = [
  { id: "aud-0001", timestamp: "2026-04-18 09:12 IST", actionType: "payment-reminder", actionLabel: "Send Payment Reminder", entity: "BT-DL-0170", reasonCode: "EMI overdue 30+ days", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: null, status: "completed", details: "SMS + App notification · borrower notified per RBI DL guidelines" },
  { id: "aud-0002", timestamp: "2026-04-18 08:58 IST", actionType: "field-visit", actionLabel: "Request Field Visit", entity: "BT-KOL-0082", reasonCode: "Usage drop 31% + offline 12.5h", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed", details: "Agent R-214 dispatched; ETA 2 hrs" },
  { id: "aud-0003", timestamp: "2026-04-18 08:30 IST", actionType: "immobilization-requested", actionLabel: "Request Battery Immobilization", entity: "BT-3567", reasonCode: "EMI overdue + high CDS + usage anomaly", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: null, status: "pending-approval", details: "Dual approval required: Risk Head + Ops Lead" },
  { id: "aud-0004", timestamp: "2026-04-18 08:15 IST", actionType: "auction-time-extended", actionLabel: "Extend Auction Time", entity: "LOT-2026-041", reasonCode: "High bidder activity in final 5 min", requestedBy: "Rohit Jain (Platform Admin)", approvedBy: "Meera Khanna (Ops Head)", status: "completed", beforeValue: "T-05:00", afterValue: "T-20:00" },
  { id: "aud-0005", timestamp: "2026-04-18 07:40 IST", actionType: "threshold-change", actionLabel: "CDS High threshold adjusted", entity: "-", reasonCode: "Reduced false positives in Delhi cluster", requestedBy: "Rohit Jain (Platform Admin)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed", beforeValue: "41", afterValue: "45", details: "Affects 1,124 accounts — new evaluation runs nightly" },
  { id: "aud-0006", timestamp: "2026-04-17 22:10 IST", actionType: "remobilization", actionLabel: "Re-mobilize after EMI settlement", entity: "BT-LKO-0128", reasonCode: "EMI paid in full + 7-day compliance window observed", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed", details: "Battery command sent; confirmation received 22:11 IST" },
  { id: "aud-0007", timestamp: "2026-04-17 18:22 IST", actionType: "restructuring-review", actionLabel: "Loan restructuring review", entity: "LN-2024-00876", reasonCode: "Force majeure — medical emergency documented", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed", details: "Tenure extended by 3 months; EMI reduced 12%" },
  { id: "aud-0008", timestamp: "2026-04-17 16:45 IST", actionType: "winning-bid-approved", actionLabel: "Approve Winning Bid", entity: "LOT-2026-038", reasonCode: "Reserve price met + 15% premium over base", requestedBy: "Rohit Jain (Platform Admin)", approvedBy: "Meera Khanna (Ops Head)", status: "completed", details: "Winner: Bidder #B-7821 · Final price ₹2,38,000" },
  { id: "aud-0009", timestamp: "2026-04-17 15:10 IST", actionType: "score-override", actionLabel: "CDS override", entity: "BT-EDGE-03", reasonCode: "Force majeure — medical emergency · documented", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: null, status: "completed", details: "Override reason logged. Computed score unchanged — override applies to collections action queue only." },
  { id: "aud-0010", timestamp: "2026-04-17 14:08 IST", actionType: "immobilization-rejected", actionLabel: "Immobilization request rejected", entity: "BT-EDGE-04", reasonCode: "Borrower dispute pending resolution", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Meera Khanna (Ops Head)", status: "rejected", details: "Dispute ticket #DSP-2026-0412; awaiting grievance officer resolution" },
  { id: "aud-0011", timestamp: "2026-04-17 11:30 IST", actionType: "reserve-price-set", actionLabel: "Set Reserve Price", entity: "LOT-2026-044", reasonCode: "Premium lot – refurb margin target", requestedBy: "Rohit Jain (Platform Admin)", approvedBy: "Meera Khanna (Ops Head)", status: "completed", beforeValue: "-", afterValue: "₹3,05,000" },
  { id: "aud-0012", timestamp: "2026-04-17 10:15 IST", actionType: "payment-reminder", actionLabel: "Send Payment Reminder", entity: "BT-VNS-0021", reasonCode: "EMI overdue 14 days", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: null, status: "completed" },
  { id: "aud-0013", timestamp: "2026-04-17 09:50 IST", actionType: "field-visit", actionLabel: "Request Field Visit", entity: "BT-VNS-0028", reasonCode: "Geo-shift 168 km + offline 7d — possible absconding", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed" },
  { id: "aud-0014", timestamp: "2026-04-17 09:22 IST", actionType: "auction-paused", actionLabel: "Pause auction for review", entity: "LOT-2026-042", reasonCode: "Bidder verification check", requestedBy: "Rohit Jain (Platform Admin)", approvedBy: "Meera Khanna (Ops Head)", status: "completed" },
  { id: "aud-0015", timestamp: "2026-04-17 08:40 IST", actionType: "immobilization-approved", actionLabel: "Immobilization approved", entity: "BT-DL-0170", reasonCode: "CDS 82 + DPD 42 + usage drop 56%", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Amit Raghavan (Risk Head) + Meera Khanna (Ops Head)", status: "completed", details: "Dual approval completed. Borrower notice delivered via SMS + App." },
  { id: "aud-0016", timestamp: "2026-04-16 20:02 IST", actionType: "threshold-change", actionLabel: "PCI reliable-payer floor raised", entity: "-", reasonCode: "Tightening underwriting for Patna cluster", requestedBy: "Rohit Jain (Platform Admin)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed", beforeValue: "0.65", afterValue: "0.70" },
  { id: "aud-0017", timestamp: "2026-04-16 17:45 IST", actionType: "data-export", actionLabel: "Portfolio export (anonymized)", entity: "-", reasonCode: "Quarterly board reporting", requestedBy: "Amit Raghavan (Risk Head)", approvedBy: "Neha Desai (CRO)", status: "completed", details: "PII redacted · MFA verified · export token expires in 24h" },
  { id: "aud-0018", timestamp: "2026-04-16 15:10 IST", actionType: "winning-bid-approved", actionLabel: "Approve Winning Bid", entity: "LOT-2026-037", reasonCode: "Reserve met", requestedBy: "Rohit Jain (Platform Admin)", approvedBy: "Meera Khanna (Ops Head)", status: "completed" },
  { id: "aud-0019", timestamp: "2026-04-16 12:48 IST", actionType: "field-visit", actionLabel: "Field visit", entity: "BT-PAT-0055", reasonCode: "Idle > 4 days + CDS 82", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed" },
  { id: "aud-0020", timestamp: "2026-04-16 11:30 IST", actionType: "restructuring-review", actionLabel: "Restructure review", entity: "LN-2024-01234", reasonCode: "Recent restructuring eligibility check", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed" },
  { id: "aud-0021", timestamp: "2026-04-16 10:02 IST", actionType: "auction-time-reduced", actionLabel: "Reduce auction time", entity: "LOT-2026-036", reasonCode: "Closed early due to reserve met & 2h cool-down", requestedBy: "Rohit Jain (Platform Admin)", approvedBy: "Meera Khanna (Ops Head)", status: "completed", beforeValue: "T+02:00", afterValue: "T-00:00" },
  { id: "aud-0022", timestamp: "2026-04-16 09:18 IST", actionType: "payment-reminder", actionLabel: "Bulk payment reminder", entity: "-", reasonCode: "DPD 7 EMI batch", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: null, status: "completed", details: "98 accounts notified via SMS + App" },
  { id: "aud-0023", timestamp: "2026-04-15 17:22 IST", actionType: "score-override", actionLabel: "Intent Score override", entity: "ld-047", reasonCode: "Model v0.2 misclassification flagged by sales", requestedBy: "Manoj Gupta (Sales Lead)", approvedBy: null, status: "completed", beforeValue: "42", afterValue: "78" },
  { id: "aud-0024", timestamp: "2026-04-15 15:40 IST", actionType: "immobilization-requested", actionLabel: "Request Immobilization", entity: "BT-VNS-0028", reasonCode: "Absconding suspected", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: null, status: "pending-approval", details: "Awaiting grievance officer review before dual approval" },
  { id: "aud-0025", timestamp: "2026-04-15 14:11 IST", actionType: "pii-access", actionLabel: "PII access — borrower contact", entity: "LN-2024-08932", reasonCode: "Manual recovery call preparation", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed", details: "MFA verified · access window: 15 min" },
  { id: "aud-0026", timestamp: "2026-04-15 12:00 IST", actionType: "remobilization", actionLabel: "Re-mobilization", entity: "BT-KOL-0101", reasonCode: "EMI settled + cooling period observed", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed" },
  { id: "aud-0027", timestamp: "2026-04-15 10:35 IST", actionType: "consent-withdraw", actionLabel: "Telemetry consent withdrawn", entity: "LN-2024-00544", reasonCode: "Borrower request via grievance channel", requestedBy: "Grievance Officer", approvedBy: null, status: "completed", details: "Telemetry purposes paused. Risk monitoring continues via EMI signal only." },
  { id: "aud-0028", timestamp: "2026-04-14 18:10 IST", actionType: "reserve-price-set", actionLabel: "Reserve Price set", entity: "LOT-2026-045", reasonCode: "Standard lot pricing model", requestedBy: "Rohit Jain (Platform Admin)", approvedBy: "Meera Khanna (Ops Head)", status: "completed", beforeValue: "-", afterValue: "₹3,30,000" },
  { id: "aud-0029", timestamp: "2026-04-14 15:25 IST", actionType: "field-visit", actionLabel: "Field visit", entity: "BT-LKO-0103", reasonCode: "Cell imbalance cluster 7d", requestedBy: "Priya Sharma (Risk Analyst)", approvedBy: "Amit Raghavan (Risk Head)", status: "completed" },
  { id: "aud-0030", timestamp: "2026-04-14 11:05 IST", actionType: "auction-cancelled", actionLabel: "Auction cancelled", entity: "LOT-2026-032", reasonCode: "Lot quality dispute — pulled for re-inspection", requestedBy: "Rohit Jain (Platform Admin)", approvedBy: "Meera Khanna (Ops Head)", status: "completed" },
  { id: "aud-0031", timestamp: "2026-04-14 09:42 IST", actionType: "bid-placed", actionLabel: "Bid placed", entity: "LOT-2026-041", reasonCode: "Dealer bid", requestedBy: "Bidder #B-7821", approvedBy: null, status: "completed", afterValue: "₹2,73,000" },
];
