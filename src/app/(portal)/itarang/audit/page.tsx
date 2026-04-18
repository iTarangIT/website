import AuditLogTable from "@/components/portal/shared/AuditLogTable";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";

export default function ITarangAuditPage() {
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-5">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Audit Log</h1>
          <p className="text-sm text-gray-400 mt-1">Shared with NBFC role · same entries · admin can filter by admin-privileged actions</p>
        </div>
        <DataFreshnessBadge label="Live" timestamp="updates instantly" />
      </header>
      <AuditLogTable />
    </div>
  );
}
