import type { FC } from "react";

type Props = {
  value: string;
  onChange: (mode: string) => void;
  options: string[];
};

const Toggle: FC<Props> = ({ value, onChange, options }) => {
  return (
    <div style={{ display: "flex", gap: "0.5rem" }}>
      {options.map((option) => (
        <button
          key={option}
          onClick={() => onChange(option)}
          style={{
            background: option === value ? "#2563eb" : "#1e293b",
            color: "#e2e8f0",
            border: "none",
            padding: "0.5rem 0.75rem",
            borderRadius: "0.5rem",
            cursor: "pointer",
          }}
        >
          {option}
        </button>
      ))}
    </div>
  );
};

export default Toggle;
