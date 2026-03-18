import KPIDashboardBase from "./shared/KPIDashboardBase";

export default function ClientKPIDashboard() {
  return (
    <KPIDashboardBase
      copy={{
        eyebrow: "KPI Analysis",
        title: "Campaign KPIs",
        campaignFieldLabel: "Campaign name",
        selectedCampaignIdLabel: "Campaign id",
        formSectionTitle: "Generate or refresh KPI",
        latestSectionTitle: "Latest KPI output (metrics & values)",
        historySectionTitle: "Execution history",
      }}
    />
  );
}
