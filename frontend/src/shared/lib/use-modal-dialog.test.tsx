import { render, screen } from '@testing-library/react';
import { useRef } from 'react';
import { afterEach, expect, it, vi } from 'vitest';
import { useModalDialog } from './use-modal-dialog';

function Dialog() {
  const dialog = useRef<HTMLDialogElement>(null);
  const cancel = useRef<HTMLButtonElement>(null);
  useModalDialog(dialog, cancel);
  return <dialog ref={dialog}><button ref={cancel}>Отмена</button></dialog>;
}

afterEach(() => { document.body.style.overflow = ''; vi.restoreAllMocks(); });

it('opens and focuses the dialog, then restores scroll and the previous focus', () => {
  const show = vi.fn(function (this: HTMLDialogElement) { this.setAttribute('open', ''); });
  const close = vi.fn(function (this: HTMLDialogElement) { this.removeAttribute('open'); });
  Object.defineProperty(HTMLDialogElement.prototype, 'showModal', { configurable: true, value: show });
  Object.defineProperty(HTMLDialogElement.prototype, 'close', { configurable: true, value: close });
  const trigger = document.createElement('button');
  document.body.append(trigger);
  trigger.focus();
  document.body.style.overflow = 'scroll';
  const view = render(<Dialog />);
  expect(show).toHaveBeenCalledOnce();
  expect(screen.getByRole('button', { name: 'Отмена' })).toHaveFocus();
  expect(document.body.style.overflow).toBe('hidden');
  view.unmount();
  expect(close).toHaveBeenCalledOnce();
  expect(document.body.style.overflow).toBe('scroll');
  expect(trigger).toHaveFocus();
  trigger.remove();
});
