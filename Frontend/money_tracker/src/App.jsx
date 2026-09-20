import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import PwaUpdateToast from './components/PwaUpdateToast.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { ThemeProvider } from './context/ThemeContext.jsx'
import AppRouter from './routes/AppRouter.jsx'

function App() {
  const { i18n } = useTranslation()

  useEffect(() => {
    document.documentElement.lang = i18n.language
  }, [i18n.language])

  return (
    <ThemeProvider>
      <AuthProvider>
        <AppRouter />
        <PwaUpdateToast />
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
