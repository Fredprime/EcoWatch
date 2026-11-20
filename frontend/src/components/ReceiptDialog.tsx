import { useEffect, useRef } from 'react';
import type { IntakeReceiptResponse } from '../api/types';
import { CopyButton } from './CopyButton';
import { formatTime } from './phase3Format';

type ReceiptDialogProps = {
  open: boolean;
  receipt: IntakeReceiptResponse | null;
  onClose: () => void;
};

/** Post-submission confirmation: the receipt and its copyable tracking reference. */
export function ReceiptDialog({ open, receipt, onClose }: ReceiptDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog === null) return;
    if (open && !dialog.open) {
      if (typeof dialog.showModal === 'function') dialog.showModal();
      else dialog.setAttribute('open', '');
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  if (receipt === null) return null;

  return (
    <dialog
      ref={dialogRef}
      className="receipt-dialog"
      aria-labelledby="receipt-dialog-title"
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose();
      }}
    >
      <div className="receipt-dialog-content">
        <h2 id="receipt-dialog-title">Report received</h2>
        <p role="status">
          The server has a durable receipt for observation {receipt.observationId}.
        </p>
        <p className="field-hint">
          Keep your tracking reference private. You need it to look up this receipt later.
        </p>
        <div className="tracking-reference">
          <code data-testid="tracking-reference">
            {receipt.trackingCode ?? 'No reference was returned for this replay.'}
          </code>
          {receipt.trackingCode && (
            <CopyButton
              value={receipt.trackingCode}
              label="Copy tracking reference"
              ariaLabel="Copy tracking reference"
            />
          )}
        </div>
        <p className="muted">
          Received {formatTime(receipt.receivedAt)} · time precision {receipt.timePrecision} ·
          location precision {receipt.locationPrecision}
          {receipt.idempotentReplay ? ' · server receipt already recorded' : ''}
        </p>
        <div className="receipt-dialog-actions">
          <button type="button" className="btn" onClick={onClose} autoFocus>
            Done
          </button>
          <a className="btn btn-secondary" href="/track">
            Track this report
          </a>
        </div>
      </div>
    </dialog>
  );
}
