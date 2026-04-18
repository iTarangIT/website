import AuditLogTable from "@/components/portal/shared/AuditLogTable";
import DataFreshnessBadge from "@/components/portal/shared/DataFreshnessBadge";

export default function NBFCAuditPage() {
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 space-y-5">
      <header className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold text-white tracking-tight">Audit Log</h1>
          <p className="text-sm text-gray-400 mt-1">Compliance spine · every privileged action across the portal</p>
        </div>
        <DataFreshnessBadge label="Live" timestamp="updates instantly" />
      </header>
      <AuditLogTable />
      <p className="text-[10px] text-gray-500 border-t border-white/10 pt-4">
        All entries are immutable, timestamped, and include requester + approver chain + reason code. Meets RBI DL Directions 2025 audit trail requirements.
      </p>
    </div>
  );
}
