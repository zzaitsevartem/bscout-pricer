'use client';

import { useEffect, type RefObject } from 'react';

export function useModalDialog(dialog: RefObject<HTMLDialogElement>, cancel: RefObject<HTMLButtonElement>) {
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const modal = dialog.current;
    modal?.showModal();
    cancel.current?.focus();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      modal?.close();
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [dialog, cancel]);
}
