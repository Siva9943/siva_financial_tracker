import { Outlet, useLocation } from 'react-router-dom'

export default function PageTransition() {
  const location = useLocation()

  return (
    <div key={location.pathname} className="animate-fade-in-up">
      <Outlet />
    </div>
  )
}
