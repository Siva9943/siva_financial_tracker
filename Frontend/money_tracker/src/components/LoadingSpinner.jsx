import { Loader2 } from 'lucide-react'

export default function LoadingSpinner({ className = '' }) {
  return <Loader2 className={`size-5 animate-spin text-brand-600 dark:text-brand-400 ${className}`} />
}
