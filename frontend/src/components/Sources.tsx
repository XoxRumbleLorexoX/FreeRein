import type { FC } from "react";

type Props = {
  sources: string[];
};

const Sources: FC<Props> = ({ sources }) => {
  if (!sources.length) return null;
  return (
    <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
      {sources.map((source) => (
        <span
          key={source}
          style={{
            background: "#475569",
            padding: "0.25rem 0.5rem",
            borderRadius: "9999px",
            fontSize: "0.75rem",
          }}
        >
          {source}
        </span>
      ))}
    </div>
  );
};

export default Sources;
