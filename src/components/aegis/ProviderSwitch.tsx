"use client";

import { providers, type Provider } from "@/content/aegis";
import styles from "./Journey.module.css";

/** The `AI_PROVIDER` setting, as a radio group. `none` is the platform default. */
export function ProviderSwitch({
  value,
  onChange,
  name,
  label = "LLM provider for the AI analyst stage",
}: {
  value: Provider;
  onChange: (p: Provider) => void;
  name: string;
  label?: string;
}) {
  return (
    <fieldset className={styles.setting}>
      <legend className="sr-only">{label}</legend>
      <span className={`mono ${styles.settingKey}`} aria-hidden="true">
        AI_PROVIDER =
      </span>
      {providers.map((p) => (
        <label key={p} className={styles.opt}>
          <input type="radio" name={name} value={p} checked={value === p} onChange={() => onChange(p)} />
          <span className={`mono ${styles.optFace} ${p !== "none" ? styles.optFaceLlm : ""}`}>{p}</span>
        </label>
      ))}
    </fieldset>
  );
}
