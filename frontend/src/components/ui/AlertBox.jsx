export default function AlertBox({ type = "error", className = "", children, ...props }) {
  const baseClass = type === "error" ? "error-box" : "success-box";
  const classes = [baseClass, className].filter(Boolean).join(" ");
  return (
    <div className={classes} {...props}>
      {children}
    </div>
  );
}
