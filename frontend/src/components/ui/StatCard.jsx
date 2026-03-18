export default function StatCard({ label, value, valueStyle }) {
  return (
    <article className="stats-card">
      <p>{label}</p>
      <strong style={valueStyle}>{value}</strong>
    </article>
  );
}
