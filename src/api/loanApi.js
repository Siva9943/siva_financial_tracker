import apiClient from './client'

export const listLoans = (params) => apiClient.get('/loans/', { params }).then((res) => res.data)

export const getLoan = (id) => apiClient.get(`/loans/${id}/`).then((res) => res.data)

export const createLoan = (payload) => apiClient.post('/loans/', payload).then((res) => res.data)

export const updateLoan = (id, payload) => apiClient.patch(`/loans/${id}/`, payload).then((res) => res.data)

export const deleteLoan = (id) => apiClient.delete(`/loans/${id}/`)

export const getLoanSummary = () => apiClient.get('/loans/summary/').then((res) => res.data)

export const getLoanAmortization = (id) => apiClient.get(`/loans/${id}/amortization/`).then((res) => res.data)

export const listLoanPayments = (id) => apiClient.get(`/loans/${id}/payments/`).then((res) => res.data)

export const recordLoanPayment = (id, payload) =>
  apiClient.post(`/loans/${id}/payments/`, payload).then((res) => res.data)

export const getLoanPriority = (strategy) =>
  apiClient.get('/loans/priority/', { params: { strategy } }).then((res) => res.data)

export const reorderLoans = (loanIds) =>
  apiClient.post('/loans/reorder/', { loan_ids: loanIds }).then((res) => res.data)

export const simulateLoan = (payload) => apiClient.post('/loan-simulator/', payload).then((res) => res.data)
