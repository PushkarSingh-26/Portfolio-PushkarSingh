"use client";

import Image from "next/image";
import { useCallback, useRef } from "react";
import type { Photo } from "@/content/photos";
import styles from "./PhotoEvidence.module.css";

/**
 * A photo shown the way a quote is: as evidence attached to a claim.
 * The thumbnail opens a native <dialog>, which handles Esc, the focus trap
 * and returning focus to the trigger.
 */
export function PhotoEvidence({ photo, caption }: { photo: Photo; caption: string }) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  const open = useCallback(() => dialogRef.current?.showModal(), []);
  const close = useCallback(() => dialogRef.current?.close(), []);

  // Clicking the backdrop (the dialog element itself, outside its content) closes it.
  const onDialogClick = useCallback((e: React.MouseEvent<HTMLDialogElement>) => {
    if (e.target === dialogRef.current) dialogRef.current?.close();
  }, []);

  return (
    <>
      <button type="button" className={styles.trigger} onClick={open}>
        <Image
          src={photo.src}
          alt=""
          width={40}
          height={40}
          sizes="40px"
          className={styles.thumb}
          aria-hidden="true"
        />
        <span>
          Photo<span className="sr-only">: {caption}</span>
        </span>
      </button>

      <dialog ref={dialogRef} className={styles.dialog} onClick={onDialogClick} aria-label={caption}>
        <div className={styles.inner}>
          <Image
            src={photo.src}
            alt={photo.alt}
            sizes="(max-width: 780px) 92vw, 720px"
            placeholder="blur"
            className={styles.image}
          />
          <div className={styles.footer}>
            <p className={`small ${styles.caption}`}>{caption}</p>
            <button type="button" className="btn btn-secondary" onClick={close} autoFocus>
              Close
            </button>
          </div>
        </div>
      </dialog>
    </>
  );
}
