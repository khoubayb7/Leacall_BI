import ETLPipelineBase from "./shared/ETLPipelineBase";

export default function ClientETLPipeline() {
  return (
    <ETLPipelineBase
      copy={{
        eyebrow: "ETL Pipeline",
        title: "Data synchronisation",
        sourcesTitle: "Your campaigns",
        emptySourcesMessage: "No campaigns configured yet. Your administrator will add them shortly.",
        showClientColumn: false,
      }}
    />
  );
}
