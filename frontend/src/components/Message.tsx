import type { FC } from "react";

type Props = {
  author: "user" | "assistant";
  text: string;
};

const Message: FC<Props> = ({ author, text }) => {
  return (
    <div
      style={{
        padding: "0.75rem 1rem",
        borderRadius: "0.75rem",
        background: author === "user" ? "#334155" : "#1d4ed8",
        marginBottom: "0.5rem",
        alignSelf: author === "user" ? "flex-end" : "flex-start",
        maxWidth: "70%",
        whiteSpace: "pre-wrap",
      }}
    >
      <strong style={{ display: "block", marginBottom: "0.25rem" }}>{author}</strong>
      {text}
    </div>
  );
};

export default Message;
