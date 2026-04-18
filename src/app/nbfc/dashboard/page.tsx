import KPIGrid from "@/components/nbfc-dashboard/KPIGrid";
import DialerDonut from "@/components/nbfc-dashboard/DialerDonut";

export default function OverviewPage() {
  return (
    <div className="space-y-6 max-w-7xl">
      <header>
        <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">
          Portfolio overview
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          Real-time visibility across your financed EV battery book.
        </p>
      </header>

      <KPIGrid />

      <DialerDonut />
    </div>
  );
}
