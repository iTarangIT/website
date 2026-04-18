import { ShieldCheck } from "lucide-react";

interface Props {
  compact?: boolean;
}

export default function RegulatoryFooter({ compact = false }: Props) {
  return (
    <p
      role="contentinfo"
      className={
        "text-[10px] text-gray-500 flex items-center gap-2 " +
        (compact ? "" : "border-t border-white/10 pt-4")
      }
    >
      <ShieldCheck className="h-3 w-3 text-gray-500 shrink-0" />
      This view complies with RBI Digital Lending Directions 2025 and the Fair Practices Code.
    </p>
  );
}
