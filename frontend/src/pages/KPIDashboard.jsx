import KPIDashboardBase from "./shared/KPIDashboardBase";

export default function KPIDashboard() {
  return (
    <KPIDashboardBase
      copy={{
        eyebrow: "Agent KPIs",
        title: "KPI dashboard",
        campaignFieldLabel: "Campaign name (from datasource)",
        selectedCampaignIdLabel: "Campaign id used",
        formSectionTitle: "Generate or refresh KPI",
        latestSectionTitle: "Latest KPI output (template values)",
        historySectionTitle: "Execution history (persistent)",
      }}
    />
  );
}
