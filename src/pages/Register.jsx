import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import Button from '../components/Button.jsx'
import Input from '../components/Input.jsx'
import LanguageSwitcher from '../components/LanguageSwitcher.jsx'
import ThemeToggle from '../components/ThemeToggle.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { getErrorMessage } from '../utils/apiError.js'

export default function Register() {
  const { register: registerUser } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [formError, setFormError] = useState('')
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm()

  const onSubmit = async (values) => {
    setFormError('')
    try {
      await registerUser(values)
      navigate('/', { replace: true })
    } catch (error) {
      setFormError(getErrorMessage(error, 'Could not create your account.'))
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-800/60 px-4">
      <div className="w-full max-w-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <LanguageSwitcher />
          <ThemeToggle />
        </div>
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.register')}</h1>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit(onSubmit)} noValidate>
          <Input
            label="Username"
            autoComplete="username"
            error={errors.username?.message}
            {...register('username', { required: 'Username is required' })}
          />
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            error={errors.email?.message}
            {...register('email', { required: 'Email is required' })}
          />
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            error={errors.password?.message}
            {...register('password', {
              required: 'Password is required',
              minLength: { value: 8, message: 'Password must be at least 8 characters' },
            })}
          />
          <Input
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            error={errors.password2?.message}
            {...register('password2', {
              required: 'Please confirm your password',
              validate: (value) => value === watch('password') || 'Passwords do not match',
            })}
          />

          {formError && <p className="text-sm text-red-600">{formError}</p>}

          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-slate-500 dark:text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-600 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
