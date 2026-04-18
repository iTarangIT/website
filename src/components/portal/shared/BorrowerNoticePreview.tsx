import { FileCheck2, PhoneCall, Globe } from "lucide-react";

interface Props {
  borrowerName: string;
  loanId: string;
  outstanding: number;
  actionLabel: string;          // "battery immobilization", "loan restructuring", etc
  reversibility: string;        // "Yes — re-mobilization within 2–4 hours after EMI settlement + dual approval"
  lenderName?: string;          // NBFC
  lspName?: string;             // iTarang
  grievanceUrl?: string;
  helpline?: string;
}

function formatINR(n: number) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n);
}

export default function BorrowerNoticePreview({
  borrowerName,
  loanId,
  outstanding,
  actionLabel,
  reversibility,
  lenderName = "Kosh Lending Co. (NBFC)",
  lspName = "iTarang Battery Solutions (LSP)",
  grievanceUrl = "https://kosh.example.com/grievance",
  helpline = "+91 1800-XXX-XXXX",
}: Props) {
  return (
    <div className="rounded-xl border-2 border-accent-amber/30 bg-accent-amber/5 p-4 space-y-3">
      <div className="flex items-center gap-2 text-accent-amber">
        <FileCheck2 className="h-4 w-4" />
        <p className="text-xs font-bold uppercase tracking-wider">Borrower notice · exact copy</p>
      </div>

      <div className="bg-black/20 rounded-lg p-3.5 text-[12px] leading-relaxed text-gray-100 space-y-2.5 border border-white/10">
        <p className="text-white">Dear {borrowerName},</p>
        <p>
          Your loan <span className="font-mono text-brand-200">{loanId}</span> with <strong className="text-white">{lenderName}</strong>{" "}
          is currently overdue. Outstanding amount: <strong className="text-white">{formatINR(outstanding)}</strong>.
        </p>
        <p>
          As part of our recovery process — delivered through our Loan Service Provider{" "}
          <strong className="text-white">{lspName}</strong> — we are initiating a <em>{actionLabel}</em> on the battery
          financed under this loan.
        </p>
        <p>
          <strong className="text-white">Restoration steps:</strong> settle the overdue amount via the NBFC app or call our
          helpline below. Restoration typically completes within 2–4 hours after dual-approval verification.
        </p>
        <p className="text-accent-green">
          <strong>Reversibility:</strong> {reversibility}
        </p>
        <p className="text-gray-400 text-[11px] italic border-l-2 border-white/20 pl-2 mt-3">
          This action is taken in accordance with your loan agreement dated at origination and with the RBI Digital Lending
          Directions 2025. It is a non-coercive measure intended only to protect the financed asset.
        </p>
        <div className="pt-2 border-t border-white/10 flex flex-wrap items-center gap-4 text-[11px] text-gray-300">
          <span className="flex items-center gap-1">
            <Globe className="h-3 w-3" /> Grievance: <a className="text-brand-200 underline" href={grievanceUrl}>{grievanceUrl}</a>
          </span>
          <span className="flex items-center gap-1">
            <PhoneCall className="h-3 w-3" /> Helpline: <span className="text-white">{helpline}</span>
          </span>
        </div>
      </div>

      <p className="text-[10px] text-gray-500">
        This preview is what the borrower will receive verbatim on SMS + App. No delivery yet — triggered on action approval.
      </p>
    </div>
  );
}
