import { auctionLots } from "@/data/portal/auction";
import LotAdminControls from "@/components/portal/itarang/auction/LotAdminControls";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";
import RegulatoryFooter from "@/components/portal/shared/RegulatoryFooter";

export default function AuctionControlPage() {
  const liveLots = auctionLots.filter((l) => l.status !== "settled");

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Auction Control Centre</h1>
          <p className="text-sm text-gray-400 mt-1">
            Platform-admin power screen · every action gates through MFA + dual approval + audit
          </p>
        </div>
        <DataFreshnessBadge label="Live" timestamp="updates each second" />
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {liveLots.map((lot) => (
          <LotAdminControls key={lot.id} lot={lot} />
        ))}
      </div>

      <p className="text-[10px] text-gray-500 leading-relaxed">
        Admin privileged actions are role-restricted and logged to the shared audit trail visible to both NBFC and Admin roles.
      </p>

      <RegulatoryFooter />
    </div>
  );
}
