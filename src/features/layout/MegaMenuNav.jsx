import { ChevronDown } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { NavLink, useLocation } from 'react-router-dom'
import { NAV_GROUPS } from '../../config/navigation.js'

export default function MegaMenuNav() {
  const { t } = useTranslation()
  const location = useLocation()
  const [openGroup, setOpenGroup] = useState(null)
  const containerRef = useRef(null)

  useEffect(() => {
    setOpenGroup(null)
  }, [location.pathname])

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpenGroup(null)
      }
    }
    const handleEscape = (event) => {
      if (event.key === 'Escape') setOpenGroup(null)
    }
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('keydown', handleEscape)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [])

  const isGroupActive = (group) => group.items.some((item) => location.pathname.startsWith(item.to))

  const inactiveTriggerClass =
    'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
  const activeTriggerClass = 'text-brand-600 dark:text-brand-400'

  return (
    <nav ref={containerRef} className="hidden items-center gap-1 lg:flex">
      {NAV_GROUPS.map((entry) => {
        if (entry.type === 'link') {
          const Icon = entry.icon
          return (
            <NavLink
              key={entry.to}
              to={entry.to}
              end={entry.end}
              className={({ isActive }) =>
                `flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium ${
                  isActive ? activeTriggerClass : inactiveTriggerClass
                }`
              }
            >
              <Icon className="size-4" />
              {t(entry.labelKey)}
            </NavLink>
          )
        }

        const Icon = entry.icon
        const active = isGroupActive(entry)
        const isOpen = openGroup === entry.key

        return (
          <div key={entry.key} className="relative">
            <button
              type="button"
              onClick={() => setOpenGroup(isOpen ? null : entry.key)}
              aria-expanded={isOpen}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium ${
                active || isOpen ? activeTriggerClass : inactiveTriggerClass
              }`}
            >
              <Icon className="size-4" />
              {t(entry.labelKey)}
              <ChevronDown className={`size-3.5 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {isOpen && (
              <div
                className={`absolute top-full z-40 mt-2 w-72 animate-slide-down rounded-xl border border-slate-200 bg-white p-3 shadow-lg dark:border-slate-700 dark:bg-slate-800 ${
                  entry.key === 'more' ? 'right-0 left-auto' : 'left-0'
                }`}
              >
                <p className="mb-2 px-2 text-xs text-slate-400 dark:text-slate-500">{t(entry.descriptionKey)}</p>
                <div className="space-y-0.5">
                  {entry.items.map((item) => {
                    const ItemIcon = item.icon
                    return (
                      <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) =>
                          `flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm ${
                            isActive
                              ? 'bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300'
                              : 'text-slate-600 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-slate-700'
                          }`
                        }
                      >
                        <ItemIcon className="size-4" />
                        {t(item.labelKey)}
                      </NavLink>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )
      })}
    </nav>
  )
}
