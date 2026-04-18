import { Sparkles } from "lucide-react";

interface Props {
  title: string;
  bullets: string[];
}

export default function NarrativeTile({ title, bullets }: Props) {
  return (
    <section className="rounded-xl bg-gradient-to-r from-brand-500/15 via-brand-500/5 to-transparent border border-brand-500/20 p-5">
      <div className="flex items-center gap-2 mb-3 text-brand-200">
        <Sparkles className="h-4 w-4" />
        <p className="text-xs font-bold uppercase tracking-wider">{title}</p>
      </div>
      <ul className="space-y-2 text-sm text-gray-200 leading-relaxed">
        {bullets.map((b, i) => (
          <li key={i} className="flex gap-2">
            <span className="shrink-0 mt-2 h-1 w-1 rounded-full bg-brand-300" />
            <span>{b}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
