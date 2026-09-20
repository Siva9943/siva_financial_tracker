import {
  AlarmClock,
  Bell,
  Bot,
  Calculator,
  FileText,
  Landmark,
  LayoutDashboard,
  LineChart,
  Map,
  PiggyBank,
  Receipt,
  Target,
  TrendingDown,
  TrendingUp,
  Wallet,
} from 'lucide-react'

// Shared between the desktop mega menu and the mobile drawer.
export const NAV_GROUPS = [
  { type: 'link', to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard, end: true },
  {
    type: 'group',
    key: 'money',
    labelKey: 'nav.money',
    icon: Wallet,
    descriptionKey: 'megaMenu.moneyDescription',
    items: [
      { to: '/income', labelKey: 'nav.income', icon: TrendingUp },
      { to: '/expenses', labelKey: 'nav.expenses', icon: TrendingDown },
      { to: '/transactions', labelKey: 'nav.transactions', icon: Receipt },
      { to: '/budgets', labelKey: 'nav.budgets', icon: PiggyBank },
    ],
  },
  {
    type: 'group',
    key: 'loans',
    labelKey: 'nav.loansGroup',
    icon: Landmark,
    descriptionKey: 'megaMenu.loansDescription',
    items: [
      { to: '/loans', labelKey: 'nav.loans', icon: Landmark },
      { to: '/loan-simulator', labelKey: 'nav.loanSimulator', icon: Calculator },
      { to: '/repayment-planner', labelKey: 'nav.repaymentPlanner', icon: Map },
    ],
  },
  {
    type: 'group',
    key: 'investments',
    labelKey: 'nav.investmentsGroup',
    icon: LineChart,
    descriptionKey: 'megaMenu.investmentsDescription',
    items: [
      { to: '/investments', labelKey: 'nav.investments', icon: LineChart },
    ],
  },
  {
    type: 'group',
    key: 'planning',
    labelKey: 'nav.planning',
    icon: Target,
    descriptionKey: 'megaMenu.planningDescription',
    items: [
      { to: '/goals', labelKey: 'nav.goals', icon: Target },
      { to: '/reports', labelKey: 'nav.reports', icon: FileText },
    ],
  },
  {
    type: 'group',
    key: 'more',
    labelKey: 'nav.more',
    icon: AlarmClock,
    descriptionKey: 'megaMenu.moreDescription',
    items: [
      { to: '/reminders', labelKey: 'nav.reminders', icon: AlarmClock },
      { to: '/notifications', labelKey: 'nav.notifications', icon: Bell },
      { to: '/ai-assistant', labelKey: 'nav.aiAssistant', icon: Bot },
    ],
  },
]
