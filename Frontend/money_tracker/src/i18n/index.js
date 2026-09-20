import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import ta from './locales/ta.json'

const STORAGE_KEY = 'fintrack-language'

function getStoredLanguage() {
  try {
    return localStorage.getItem(STORAGE_KEY) || 'en'
  } catch {
    return 'en'
  }
}

export function setLanguage(language) {
  try {
    localStorage.setItem(STORAGE_KEY, language)
  } catch {
    // ignore write failures (private browsing, storage disabled, etc.)
  }
  i18n.changeLanguage(language)
}

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    ta: { translation: ta },
  },
  lng: getStoredLanguage(),
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

export default i18n
