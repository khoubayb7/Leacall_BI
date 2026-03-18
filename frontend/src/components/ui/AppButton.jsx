function getVariantClass(variant) {
  if (variant === "secondary") return "secondary-btn";
  if (variant === "danger") return "danger-btn";
  return "primary-btn";
}

export default function AppButton({
  variant = "primary",
  compact = false,
  className = "",
  children,
  ...props
}) {
  const classes = [getVariantClass(variant), compact ? "compact" : "", className]
    .filter(Boolean)
    .join(" ");

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
