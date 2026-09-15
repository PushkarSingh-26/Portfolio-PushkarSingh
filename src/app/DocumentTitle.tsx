"use client";

import { useEffect } from "react";

/**
 * For pages that can't export metadata (the 404 page). Next streams the layout's
 * <title> in after hydration, so re-apply ours whenever the head changes.
 */
export function DocumentTitle({ title }: { title: string }) {
  useEffect(() => {
    const apply = () => {
      if (document.title !== title) document.title = title;
    };
    apply();
    const mo = new MutationObserver(apply);
    mo.observe(document.head, { childList: true, subtree: true, characterData: true });
    return () => mo.disconnect();
  }, [title]);
  return null;
}
