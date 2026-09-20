import { lazy, Suspense } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import LoadingScreen from '../components/LoadingScreen.jsx'
import MainLayout from '../layouts/MainLayout.jsx'
import Login from '../pages/Login.jsx'
import Register from '../pages/Register.jsx'
import PageTransition from './PageTransition.jsx'
import ProtectedRoute from './ProtectedRoute.jsx'

const AIAssistant = lazy(() => import('../pages/AIAssistant.jsx'))
const Budgets = lazy(() => import('../pages/Budgets.jsx'))
const Dashboard = lazy(() => import('../pages/Dashboard.jsx'))
const Expenses = lazy(() => import('../pages/Expenses.jsx'))
const Goals = lazy(() => import('../pages/Goals.jsx'))
const Income = lazy(() => import('../pages/Income.jsx'))
const InvestmentDetail = lazy(() => import('../pages/InvestmentDetail.jsx'))
const Investments = lazy(() => import('../pages/Investments.jsx'))
const LoanDetail = lazy(() => import('../pages/LoanDetail.jsx'))
const Loans = lazy(() => import('../pages/Loans.jsx'))
const LoanSimulator = lazy(() => import('../pages/LoanSimulator.jsx'))
const NotFound = lazy(() => import('../pages/NotFound.jsx'))
const Notifications = lazy(() => import('../pages/Notifications.jsx'))
const Reminders = lazy(() => import('../pages/Reminders.jsx'))
const RepaymentPlanner = lazy(() => import('../pages/RepaymentPlanner.jsx'))
const Reports = lazy(() => import('../pages/Reports.jsx'))
const Settings = lazy(() => import('../pages/Settings.jsx'))
const Transactions = lazy(() => import('../pages/Transactions.jsx'))

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingScreen />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route element={<PageTransition />}>
                <Route path="/" element={<Dashboard />} />
                <Route path="/income" element={<Income />} />
                <Route path="/expenses" element={<Expenses />} />
                <Route path="/loans" element={<Loans />} />
                <Route path="/loans/:id" element={<LoanDetail />} />
                <Route path="/loan-simulator" element={<LoanSimulator />} />
                <Route path="/repayment-planner" element={<RepaymentPlanner />} />
                <Route path="/budgets" element={<Budgets />} />
                <Route path="/goals" element={<Goals />} />
                <Route path="/investments" element={<Investments />} />
                <Route path="/investments/:id" element={<InvestmentDetail />} />
                <Route path="/investments/:id/transactions" element={<InvestmentDetail initialTab="transactions" />} />
                <Route path="/investments/:id/performance" element={<InvestmentDetail initialTab="performance" />} />
                <Route path="/reminders" element={<Reminders />} />
                <Route path="/notifications" element={<Notifications />} />
                <Route path="/transactions" element={<Transactions />} />
                <Route path="/ai-assistant" element={<AIAssistant />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="*" element={<NotFound />} />
              </Route>
            </Route>
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
