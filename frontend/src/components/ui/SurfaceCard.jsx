export default function SurfaceCard({ title, children }) {
  return (
    <article className="surface-card">
      {title ? <h2>{title}</h2> : null}
      {children}
    </article>
  );
}
