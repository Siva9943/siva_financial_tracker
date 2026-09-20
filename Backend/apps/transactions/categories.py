"""Default category choices offered by the UI, per transaction type.

These are suggestions, not a hard DB constraint — the Transaction model
stores `category` as free text so a user is never blocked from recording
something outside the defaults.
"""

INCOME_CATEGORIES = [
    'Salary',
    'Freelance',
    'Business',
    'Investment',
    'Farming',
    'Other',
]

EXPENSE_CATEGORIES = [
    'Food',
    'Travel',
    'Rent',
    'Electricity',
    'Education',
    'Medical',
    'Shopping',
    'Entertainment',
    'Loan EMI',
    'Insurance',
    'Mobile',
    'Internet',
    'Groceries',
    'Other',
]
