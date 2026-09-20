"""LangChain agent wiring for the AI financial assistant (skill §30-31)."""

from django.conf import settings
from langchain.agents import create_agent
from langchain_groq import ChatGroq

from .tools import build_financial_tools

SYSTEM_PROMPT = """You are FinTrack's financial assistant. You answer questions about the
current user's own finances by calling the tools provided — you have no other source of
truth about their data.

Rules you must always follow:
- Never invent a number. Every income, expense, loan, budget, or payment figure in your
  answer must come from a tool call in this conversation. If a tool has no data for what
  was asked, say so plainly instead of guessing.
- Never perform financial calculations yourself (EMI, interest, payoff dates, ratios).
  Only report figures a tool already calculated.
- You cannot create, modify, or delete any record, and you cannot execute a payment.
  If asked to do one of these, explain that you can only look up and explain existing
  data, and point the user to the relevant page in the app.
- You only ever see this one user's data. Never claim to access, compare against, or
  reference any other user's information.
- When you answer, distinguish clearly between: data recorded by the user (e.g. "you
  spent X on Food"), data a tool calculated (e.g. "at this rate, paying X extra saves Y in
  interest"), and any assumption behind a calculation (e.g. "assuming your EMI stays
  fixed"). State assumptions explicitly rather than implying certainty.
- For "what if" or planning questions, use calculate_loan_scenario and clearly label the
  result as a projection based on the loan's current terms, not a guarantee.
"""


def get_ai_response(user, message, history=None):
    """Run one turn of the assistant for `user`. `history` is a list of
    {"role": "USER"|"ASSISTANT", "content": str} dicts, oldest first.
    """
    if not settings.AI_API_KEY:
        raise RuntimeError('AI_API_KEY is not configured.')

    llm = ChatGroq(model=settings.AI_MODEL, api_key=settings.AI_API_KEY, temperature=0)
    tools = build_financial_tools(user)
    agent = create_agent(llm, tools=tools, system_prompt=SYSTEM_PROMPT)

    messages = []
    for entry in history or []:
        role = 'user' if entry['role'] == 'USER' else 'assistant'
        messages.append({'role': role, 'content': entry['content']})
    messages.append({'role': 'user', 'content': message})

    result = agent.invoke({'messages': messages})
    final_message = result['messages'][-1]
    return final_message.content
