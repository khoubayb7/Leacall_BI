export default function FormInput({ label, type = "text", value, onChange, placeholder, name }) {
  return (
    <label className="form-label">
      <span>{label}</span>
      <input
        className="form-input"
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        name={name}
        required
      />
    </label>
  );
}
