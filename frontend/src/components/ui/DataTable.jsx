export default function DataTable({
  loading = false,
  loadingMessage = "Loading...",
  emptyMessage = "No data.",
  rows = [],
  columns = [],
  getRowKey,
  getRowProps,
  renderRow,
}) {
  if (loading) {
    return <p style={{ color: "var(--text-soft)", margin: "8px 0" }}>{loadingMessage}</p>;
  }

  if (!rows.length) {
    return <p style={{ color: "var(--text-soft)", margin: "8px 0" }}>{emptyMessage}</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          {columns.map((column, index) => (
            <th key={`${String(column)}-${index}`}>{column}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => {
          const key = typeof getRowKey === "function" ? getRowKey(row, index) : index;
          const rowProps = typeof getRowProps === "function" ? getRowProps(row, index) : undefined;
          return (
            <tr key={key} {...rowProps}>
              {renderRow(row, index)}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
