'use client';

import { useModalDialog } from '@/shared/lib/use-modal-dialog';
import { useId, useRef } from 'react';

export function RemoveOfferDialog({
  name,
  pending,
  error,
  onCancel,
  onConfirm,
}: {
  name: string;
  pending: boolean;
  error: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  const titleId = useId();
  const descriptionId = useId();
  useModalDialog(dialog, cancel);
  return (
    <dialog
      ref={dialog}
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      aria-modal="true"
      onCancel={(event) => {
        event.preventDefault();
        if (!pending) onCancel();
      }}
      className="m-auto w-[calc(100%-2rem)] max-w-[480px] rounded-[24px] border border-border-light-subtle bg-ivory p-6 text-body shadow-lg backdrop:bg-black/30 backdrop:backdrop-blur-sm"
    >
      <h3 id={titleId} className="mb-3 text-2xl font-semibold text-slate">
        Удалить предложение?
      </h3>
      <p id={descriptionId} className="break-words text-[15px] text-body-subtle">
        «{name}» будет удалено из каталога. Повторный сбор цен не вернёт это предложение.
      </p>
      {error && (
        <p role="alert" className="mt-4 text-[14px] text-clay">
          Не удалось удалить. Попробуйте ещё раз.
        </p>
      )}
      <div className="mt-6 flex flex-wrap justify-end gap-3">
        <button
          ref={cancel}
          type="button"
          className="btn-secondary btn-sm disabled:opacity-50"
          disabled={pending}
          onClick={onCancel}
        >
          Отмена
        </button>
        <button
          type="button"
          className="btn-danger btn-sm disabled:opacity-50"
          disabled={pending}
          onClick={onConfirm}
        >
          {pending ? 'Удаляем…' : 'Удалить'}
        </button>
      </div>
    </dialog>
  );
}
