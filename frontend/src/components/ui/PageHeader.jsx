export default function PageHeader({ eyebrow, title, action }) {
  return (
    <header className="content-header">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h1>{title}</h1>
      </div>
      {action || null}
    </header>
  );
}
