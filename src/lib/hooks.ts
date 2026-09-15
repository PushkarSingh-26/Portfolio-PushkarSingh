"use client";

import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

const RM_QUERY = "(prefers-reduced-motion: reduce)";

function subscribeRM(cb: () => void) {
  const mq = window.matchMedia(RM_QUERY);
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
}

/** True when the visitor prefers reduced motion. SSR assumes reduced (safe default: no motion). */
export function usePrefersReducedMotion() {
  return useSyncExternalStore(
    subscribeRM,
    () => window.matchMedia(RM_QUERY).matches,
    () => true,
  );
}

/** Media query as state. `serverValue` is used during SSR and hydration. */
export function useMediaQuery(query: string, serverValue = false) {
  const subscribe = useCallback(
    (cb: () => void) => {
      const mq = window.matchMedia(query);
      mq.addEventListener("change", cb);
      return () => mq.removeEventListener("change", cb);
    },
    [query],
  );
  return useSyncExternalStore(subscribe, () => window.matchMedia(query).matches, () => serverValue);
}

/** Fine pointer + hover capable (desktop). Touch devices get tap-to-select. */
export function useCanHover() {
  return useMediaQuery("(hover: hover) and (pointer: fine)", true);
}

/** Fires once when the element first comes near the viewport. */
export function useInViewOnce<T extends Element>(rootMargin = "0px 0px -15% 0px") {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || inView) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setInView(true);
          io.disconnect();
        }
      },
      { rootMargin },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [inView, rootMargin]);
  return [ref, inView] as const;
}
