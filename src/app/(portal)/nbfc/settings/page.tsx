import ComingSoon from "@/components/portal/ComingSoon";

export default function NBFCSettingsPage() {
  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-semibold text-white tracking-tight mb-8">Settings</h1>
      <ComingSoon
        title="Settings & configuration"
        description="Threshold overrides, alert routing, notification preferences and consent management will live here. In the demo, admin-level threshold controls are available on the iTarang Risk Rule Engine page."
      />
    </div>
  );
}
