export default function ModulePlaceholder({ title, description }) {
  return (
    <section className="workspace-content">
      <header className="content-header">
        <div>
          <p className="eyebrow">Module</p>
          <h1>{title}</h1>
        </div>
      </header>

      <article className="surface-card">
        <p>{description}</p>
      </article>
    </section>
  );
}
