import { Construction } from "lucide-react";

interface ComingSoonProps {
  title: string;
  description?: string;
}

export default function ComingSoon({ title, description }: ComingSoonProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-6 text-center">
      <div className="h-14 w-14 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center mb-5">
        <Construction className="h-6 w-6 text-brand-400" />
      </div>
      <h2 className="text-xl font-semibold text-white mb-2">{title}</h2>
      <p className="text-sm text-gray-400 max-w-sm">
        {description ?? "This section is part of the iTarang roadmap and will be available once the full workflow is wired up."}
      </p>
    </div>
  );
}
