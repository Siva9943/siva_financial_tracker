// Shared between Investments.jsx (create) and InvestmentDetail.jsx (edit): InvestmentFormModal
// collects the base investment fields plus optional deposit/withdrawal amounts in one form —
// this splits that combined payload into the base PATCH/POST body and the follow-up
// transaction call(s), so the "invested amount" the user typed goes through the same
// authoritative backend ledger (services.investment_service) as every other transaction.

const TRANSIENT_FIELDS = ['deposit_amount', 'withdrawal_amount', 'transaction_date']

export function extractBaseInvestmentPayload(values) {
  const base = { ...values }
  TRANSIENT_FIELDS.forEach((field) => delete base[field])
  return base
}

export async function applyInvestedAmountAdjustments(investmentApi, investmentId, values) {
  const depositAmount = Number(values.deposit_amount)
  const withdrawalAmount = Number(values.withdrawal_amount)
  const transactionDate = values.transaction_date || new Date().toISOString().slice(0, 10)

  if (depositAmount > 0) {
    await investmentApi.recordInvestmentTransaction(investmentId, {
      transaction_type: 'DEPOSIT',
      transaction_date: transactionDate,
      amount: depositAmount,
    })
  }

  if (withdrawalAmount > 0) {
    await investmentApi.recordInvestmentTransaction(investmentId, {
      transaction_type: 'WITHDRAWAL',
      transaction_date: transactionDate,
      amount: withdrawalAmount,
    })
  }
}
