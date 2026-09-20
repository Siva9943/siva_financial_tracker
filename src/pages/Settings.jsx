import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useTranslation } from 'react-i18next'
import * as authApi from '../api/authApi'
import Button from '../components/Button.jsx'
import Input from '../components/Input.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { getErrorMessage } from '../utils/apiError.js'

function ProfileForm() {
  const { t } = useTranslation()
  const { user, refreshUser } = useAuth()
  const [status, setStatus] = useState({ type: null, message: '' })
  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm({
    defaultValues: {
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      phone_number: user.profile.phone_number,
      currency: user.profile.currency,
    },
  })

  const onSubmit = async (values) => {
    setStatus({ type: null, message: '' })
    try {
      await authApi.updateMe({
        first_name: values.first_name,
        last_name: values.last_name,
        email: values.email,
        profile: { phone_number: values.phone_number, currency: values.currency },
      })
      await refreshUser()
      setStatus({ type: 'success', message: t('settings.profileUpdated') })
    } catch (error) {
      setStatus({ type: 'error', message: getErrorMessage(error, t('settings.profileUpdateError')) })
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input label={t('settings.firstName')} {...register('first_name')} />
        <Input label={t('settings.lastName')} {...register('last_name')} />
      </div>
      <Input label={t('settings.email')} type="email" {...register('email', { required: true })} />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Input label={t('settings.phoneNumber')} {...register('phone_number')} />
        <label className="block">
          <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">{t('settings.currency')}</span>
          <select
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand-500"
            {...register('currency')}
          >
            <option value="INR">INR</option>
            <option value="USD">USD</option>
            <option value="EUR">EUR</option>
            <option value="GBP">GBP</option>
          </select>
        </label>
      </div>

      {status.message && (
        <p className={`text-sm ${status.type === 'error' ? 'text-red-600' : 'text-green-600'}`}>
          {status.message}
        </p>
      )}

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? t('settings.saving') : t('settings.saveChanges')}
      </Button>
    </form>
  )
}

function ChangePasswordForm() {
  const { t } = useTranslation()
  const [status, setStatus] = useState({ type: null, message: '' })
  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm()

  const onSubmit = async (values) => {
    setStatus({ type: null, message: '' })
    try {
      await authApi.changePassword(values)
      setStatus({ type: 'success', message: t('settings.passwordChanged') })
      reset()
    } catch (error) {
      setStatus({ type: 'error', message: getErrorMessage(error, t('settings.passwordChangeError')) })
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
      <Input
        label={t('settings.currentPassword')}
        type="password"
        error={errors.old_password?.message}
        {...register('old_password', { required: t('settings.currentPasswordRequired') })}
      />
      <Input
        label={t('settings.newPassword')}
        type="password"
        error={errors.new_password?.message}
        {...register('new_password', {
          required: t('settings.newPasswordRequired'),
          minLength: { value: 8, message: t('settings.passwordMinLength') },
        })}
      />
      <Input
        label={t('settings.confirmNewPassword')}
        type="password"
        error={errors.new_password2?.message}
        {...register('new_password2', {
          required: t('settings.confirmPasswordRequired'),
          validate: (value) => value === watch('new_password') || t('settings.passwordsDoNotMatch'),
        })}
      />

      {status.message && (
        <p className={`text-sm ${status.type === 'error' ? 'text-red-600' : 'text-green-600'}`}>
          {status.message}
        </p>
      )}

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? t('settings.updating') : t('settings.changePassword')}
      </Button>
    </form>
  )
}

export default function Settings() {
  const { t } = useTranslation()
  const { user } = useAuth()

  if (!user) return null

  return (
    <div className="max-w-2xl space-y-8">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{t('pages.settings')}</h1>

      <section className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6">
        <h2 className="mb-4 text-lg font-medium text-slate-900 dark:text-slate-100">{t('settings.profile')}</h2>
        <ProfileForm />
      </section>

      <section className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6">
        <h2 className="mb-4 text-lg font-medium text-slate-900 dark:text-slate-100">{t('settings.changePassword')}</h2>
        <ChangePasswordForm />
      </section>
    </div>
  )
}
