import Button from './Button.jsx'
import Modal from './Modal.jsx'

export default function ConfirmDialog({ isOpen, title, message, onConfirm, onCancel, isConfirming }) {
  return (
    <Modal title={title} isOpen={isOpen} onClose={onCancel}>
      <p className="text-sm text-slate-600 dark:text-slate-300">{message}</p>
      <div className="mt-6 flex justify-end gap-3">
        <Button variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button
          onClick={onConfirm}
          disabled={isConfirming}
          className="!bg-red-600 hover:!bg-red-700 disabled:!bg-red-300"
        >
          {isConfirming ? 'Deleting…' : 'Delete'}
        </Button>
      </div>
    </Modal>
  )
}
