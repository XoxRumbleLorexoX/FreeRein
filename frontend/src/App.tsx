import { useEffect, useState } from "react";
import Message from "./components/Message";
import Sources from "./components/Sources";
import Toggle from "./components/Toggle";
import Spinner from "./components/Spinner";
import { chat, getHealth } from "./api";

type ConversationMessage = {
  role: "user" | "assistant";
  text: string;
  sources?: string[];
};

const App = () => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [pending, setPending] = useState(false);
  const [mode, setMode] = useState("hybrid");
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<string>("Loading...");

  useEffect(() => {
    getHealth()
      .then((info) => {
        setStatus(
          `Model: ${info.model} | Web: ${info.web_enabled ? "on" : "off"} | CopilotKit: ${info.submodules.copilotkit ? "on" : "off"}`
        );
      })
      .catch(() => setStatus("Backend unavailable"));
  }, []);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg: ConversationMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setPending(true);
    setInput("");
    try {
      const response = await chat(userMsg.text, mode);
      const assistant: ConversationMessage = {
        role: "assistant",
        text: response.reply,
        sources: response.sources,
      };
      setMessages((prev) => [...prev, assistant]);
    } catch (error) {
      const assistant: ConversationMessage = {
        role: "assistant",
        text: error instanceof Error ? error.message : "Unknown error",
      };
      setMessages((prev) => [...prev, assistant]);
    } finally {
      setPending(false);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        padding: "2rem",
        gap: "1rem",
      }}
    >
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1 style={{ margin: 0 }}>lam-agent-unified</h1>
        <Toggle value={mode} onChange={setMode} options={["offline", "web", "hybrid"]} />
      </header>
      <p style={{ margin: 0, color: "#cbd5f5" }}>{status}</p>
      <main style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {messages.map((msg, idx) => (
          <div key={idx} style={{ display: "flex", flexDirection: "column" }}>
            <Message author={msg.role} text={msg.text} />
            {msg.sources && <Sources sources={msg.sources} />}
          </div>
        ))}
        {pending && (
          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <Spinner />
            <span>Generating...</span>
          </div>
        )}
      </main>
      <div style={{ display: "flex", gap: "0.5rem" }}>
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask something..."
          style={{ flex: 1, minHeight: "4rem", padding: "0.75rem", borderRadius: "0.5rem", border: "1px solid #334155" }}
        />
        <button
          onClick={send}
          disabled={pending}
          style={{
            width: "6.5rem",
            background: pending ? "#475569" : "#2563eb",
            border: "none",
            color: "white",
            borderRadius: "0.5rem",
            cursor: pending ? "not-allowed" : "pointer",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default App;
