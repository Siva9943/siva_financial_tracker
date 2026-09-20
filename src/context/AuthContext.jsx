import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import * as authApi from '../api/authApi'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const loadUser = useCallback(async () => {
    if (!localStorage.getItem('accessToken')) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const me = await authApi.getMe()
      setUser(me)
    } catch {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    loadUser()
  }, [loadUser])

  const login = async (credentials) => {
    const { access, refresh } = await authApi.login(credentials)
    localStorage.setItem('accessToken', access)
    localStorage.setItem('refreshToken', refresh)
    const me = await authApi.getMe()
    setUser(me)
    return me
  }

  const register = async (payload) => {
    await authApi.register(payload)
    return login({ username: payload.username, password: payload.password })
  }

  const logout = async () => {
    const refresh = localStorage.getItem('refreshToken')
    try {
      if (refresh) await authApi.logout(refresh)
    } catch {
      // token may already be invalid/expired — proceed with local logout regardless
    }
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    setUser(null)
  }

  const refreshUser = async () => {
    const me = await authApi.getMe()
    setUser(me)
    return me
  }

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, isLoading, login, register, logout, refreshUser }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within an AuthProvider')
  return context
}
