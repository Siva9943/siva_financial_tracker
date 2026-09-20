import apiClient from './client'

export const listRepaymentPlans = (params) =>
  apiClient.get('/repayment-plan/', { params }).then((res) => res.data)

export const getRepaymentPlan = (id) => apiClient.get(`/repayment-plan/${id}/`).then((res) => res.data)

export const generateRepaymentPlan = (payload) =>
  apiClient.post('/repayment-plan/generate/', payload).then((res) => res.data)
