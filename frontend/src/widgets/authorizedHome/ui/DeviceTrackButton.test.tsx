import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DeviceTrackButton } from './DeviceTrackButton';
const { mutate } = vi.hoisted(() => ({ mutate: vi.fn() }));
vi.mock('effector-react', () => ({ useUnit: () => true }));
vi.mock('@/models/tracking', () => ({
  useTrackingUsage: () => ({ data: { plan: 'advanced' } }),
  useTrackedDevices: () => ({ data: [{ id: 4 }] }),
  useDeviceTrackingMutation: () => ({ mutate, reset: vi.fn(), isPending: false, isError: false }),
}));
vi.mock('./RemoveTrackingDialog', () => ({
  RemoveTrackingDialog: ({ onConfirm, onCancel }: { onConfirm: () => void; onCancel: () => void }) => (
    <div role="dialog"><button onClick={onConfirm}>Удалить</button><button onClick={onCancel}>Отмена</button></div>
  ),
}));
describe('DeviceTrackButton', () => {
  it('requires confirmation before removing tracking', () => {
    render(<DeviceTrackButton id={4} name="iPhone" />);
    fireEvent.click(screen.getByRole('button', { name: 'Перестать отслеживать устройство' }));
    expect(mutate).not.toHaveBeenCalled();
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Отмена' }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(mutate).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: 'Перестать отслеживать устройство' }));
    fireEvent.click(screen.getByRole('button', { name: 'Удалить' }));
    expect(mutate).toHaveBeenCalledWith({ id: 4, remove: true }, expect.any(Object));
  });
});
