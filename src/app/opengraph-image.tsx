import { ImageResponse } from "next/og";
import tokens from "@/content/generated/tokens.json";

export const alt = "Pushkar Singh — AI/ML engineer. His name shown as o200k_base tokens with their real IDs.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpengraphImage() {
  const name = tokens.phrases.name.tokens;
  const areas = [
    { text: "LLMs", bg: "#FFE7A3" },
    { text: "Generative AI", bg: "#C9EFD9" },
    { text: "Machine learning", bg: "#CFE3FF" },
    { text: "Intelligent systems", bg: "#F6D2E0" },
  ];
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          background: "#F3F5F7",
          color: "#14233A",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: "72px 80px",
        }}
      >
        <div style={{ display: "flex", gap: 18 }}>
          {name.map((t) => (
            <div key={t.id} style={{ display: "flex", flexDirection: "column" }}>
              <div style={{ display: "flex", fontSize: 132, fontWeight: 800, letterSpacing: -5, lineHeight: 1 }}>{t.text.trim()}</div>
              <div
                style={{
                  display: "flex",
                  height: 12,
                  marginTop: 10,
                  border: "3px solid #7A8596",
                  borderTop: "0px solid transparent",
                }}
              />
              <div style={{ display: "flex", marginTop: 10, fontSize: 26, color: "#4A5668" }}>{t.id}</div>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div style={{ display: "flex", fontSize: 56, fontWeight: 700 }}>AI/ML engineer</div>
          <div style={{ display: "flex", gap: 14 }}>
            {areas.map((a) => (
              <div key={a.text} style={{ display: "flex", background: a.bg, borderRadius: 8, padding: "8px 18px", fontSize: 30, fontWeight: 600 }}>
                {a.text}
              </div>
            ))}
          </div>
        </div>
      </div>
    ),
    size,
  );
}
