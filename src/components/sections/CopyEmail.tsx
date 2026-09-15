"use client";

import { useState } from "react";

export function CopyEmail({ email }: { email: string }) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  return (
    <>
      <button
        type="button"
        className="btn btn-secondary"
        onClick={async () => {
          try {
            await navigator.clipboard.writeText(email);
            setState("copied");
          } catch {
            setState("failed");
          }
          window.setTimeout(() => setState("idle"), 2400);
        }}
      >
        {state === "copied" ? "Email copied" : "Copy email"}
      </button>
      <span className="sr-only" aria-live="polite">
        {state === "copied" ? "Email copied" : state === "failed" ? `Couldn't copy. The address is ${email}` : ""}
      </span>
    </>
  );
}
