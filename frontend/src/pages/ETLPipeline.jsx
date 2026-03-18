import ETLPipelineBase from "./shared/ETLPipelineBase";

export default function ETLPipeline() {
  return (
    <ETLPipelineBase
      copy={{
        eyebrow: "ETL Pipeline",
        title: "Data synchronisation",
        sourcesTitle: "Data sources - LeaCall campaigns",
        emptySourcesMessage: "No data sources configured yet. Ask an admin to add a LeaCall campaign.",
        showClientColumn: true,
      }}
    />
  );
}
