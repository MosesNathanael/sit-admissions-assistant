import json
import logging
import httpx

from rag import ask_query, MAX_DISTANCE
from llm import ask_llm
from mcp_server import get_key_dates

logging.disable(logging.INFO)

SHOW_STEPS = True  


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_admissions_info",
            "description": "Search SIT admissions information from the knowledge base. Use for general questions about admissions, requirements, fees, scholarships, programmes, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or keywords to look up (e.g., 'entry requirements for nursing', 'tuition fees for engineering')"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Optional topic to narrow the search (e.g., 'scholarships', 'fees', 'requirements', 'programmes')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_key_dates",
            "description": "Get verified SIT admissions key dates from the official data. Use for questions about application deadlines, interview periods, result release dates, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "applies_to": {
                        "type": "string",
                        "description": "Optional filter for specific programmes or applicant groups (e.g., 'Engineering', 'Allied Health', 'Early Admissions'). Matches case-insensitively."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "submit_enquiry",
            "description": "Submit an enquiry to the SIT admissions team when the agent cannot answer the question. Requires user confirmation before submitting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "route": {
                        "type": "string",
                        "enum": ["admissions", "programme", "financial_aid", "scholarships", "other"],
                        "description": "Which team should handle the enquiry. Fee questions use 'financial_aid'."
                    },
                    "programme_interest": {
                        "type": "string",
                        "description": "The programme the user is interested in (e.g., 'Nursing', 'Computer Science', 'Engineering'), or 'General'"
                    },
                    "question": {
                        "type": "string",
                        "description": "The user's question that couldn't be answered"
                    },
                    "contact_email": {
                        "type": "string",
                        "description": "User's email address for follow-up. Use demo@example.com unless the user gave one."
                    }
                },
                "required": ["route", "programme_interest", "question", "contact_email"]
            }
        }
    }
]


AGENT_SYSTEM_PROMPT = """You are the SIT Admissions Assistant, an AI agent that helps prospective applicants with admission-related questions.

You have access to the following tools:
1. search_admissions_info - Search the admissions knowledge base for general information
2. get_key_dates - Get verified key dates for admissions events
3. submit_enquiry - Submit an enquiry to the admissions team (requires user confirmation)

Rules:
- Use tools to answer questions. Maximum 4 tool calls per question.
- For general questions: use search_admissions_info
- For date-related questions: use get_key_dates
- Answer ONLY from tool results. Never use outside knowledge and never guess (for example, do not guess fees).
- If a search returns nothing relevant, do NOT repeat it with similar words. Offer to submit_enquiry instead.
- If you cannot answer after using tools: offer to submit_enquiry
- For submit_enquiry, use demo@example.com as contact_email unless the user gave an email
- Always show the draft enquiry and ask for user confirmation before calling submit_enquiry
- Cite sources when using search_admissions_info
- Remind users to verify dates and fees on the official SIT website
- Keep answers short and clear
- Never guarantee admission or eligibility"""

MAX_TOOL_CALLS = 4


def search_admissions_info(query: str, topic: str | None = None) -> list[dict]:
    """Search SIT admissions information and return relevant passages with sources."""
    full_query = f"{topic}: {query}" if topic else query
    chunks = ask_query(full_query, 5)
    return [
        {
            "text": c["text"],
            "title": c["title"],
            "source_url": c["url"],
            "ay": c["ay"],
            "distance": round(c["distance"], 4),
        }
        for c in chunks
        if c["distance"] <= MAX_DISTANCE
    ]


def submit_enquiry(route: str, programme_interest: str, question: str, contact_email: str) -> dict:
    """Submit an enquiry via the API endpoint."""
    api_url = "http://localhost:8000/enquiries"
    payload = {
        "route": route,
        "programme_interest": programme_interest,
        "question": question,
        "contact_email": contact_email,
        "status": "open"
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(api_url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        return {"error": f"Failed to connect to API: {e}"}
    except httpx.HTTPStatusError as e:
        return {"error": f"API error: {e.response.status_code} - {e.response.text}"}


def format_search_results(results: list[dict]) -> str:
    """Format search results for display."""
    if not results:
        return "No relevant information found."

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"[{i}] {r['title']} (AY: {r['ay']}) - Distance: {r['distance']}")
        lines.append(f"    Source: {r['source_url']}")
        lines.append(f"    Excerpt: {r['text'][:300]}...")
        lines.append("")
    return "\n".join(lines)


def format_key_dates(dates: list[dict]) -> str:
    """Format key dates for display."""
    if not dates:
        return "No key dates found for that filter."

    lines = []
    for d in dates:
        lines.append(f"• {d['event']}: {d['date']}")
        lines.append(f"  Applies to: {d['applies_to']} (AY: {d['ay']})")
        lines.append(f"  Source: {d['source_url']}")
        lines.append("")
    return "\n".join(lines)


def run_agent(user_question: str, conversation_history: list[dict] | None = None) -> str:
    """Run the agent tool-calling loop for a single question."""
    if conversation_history is None:
        conversation_history = []

   
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT}
    ]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_question})

    tool_calls_made = 0
    pending_enquiry = None

    while True:
        out_of_calls = tool_calls_made >= MAX_TOOL_CALLS

        if out_of_calls:
            finish = {
                "role": "user",
                "content": "You have used all your tool calls. Using only the information above, "
                           "give your final answer now. If it does not answer the question, say so and "
                           "offer to send an enquiry to the admissions team. Do not call any tools.",
            }
            response = ask_llm_with_tools(messages + [finish], [])
        else:
            response = ask_llm_with_tools(messages, TOOLS)

        if response.get("tool_calls") and not out_of_calls:
            for tool_call in response["tool_calls"]:
                if tool_calls_made >= MAX_TOOL_CALLS:
                    break

                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])

                if SHOW_STEPS:
                    print(f"\n[Tool Call {tool_calls_made + 1}/{MAX_TOOL_CALLS}] {tool_name}({tool_args})")

               
                if tool_name == "search_admissions_info":
                    results = search_admissions_info(**tool_args)
                    tool_result = format_search_results(results)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result
                    })

                elif tool_name == "get_key_dates":
                    results = get_key_dates(**tool_args)
                    tool_result = format_key_dates(results)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result
                    })

                elif tool_name == "submit_enquiry":
                    pending_enquiry = tool_args
                    tool_result = f"Draft enquiry prepared:\n- Route: {tool_args['route']}\n- Programme: {tool_args['programme_interest']}\n- Question: {tool_args['question']}\n- Email: {tool_args['contact_email']}\n\nPlease confirm: Should I submit this enquiry? (yes/no)"
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result
                    })

                tool_calls_made += 1

            continue

        assistant_message = response.get("content") or (
            "I couldn't find that in the SIT documents. Would you like me to send an enquiry "
            "to the admissions team?"
        )
        messages.append({"role": "assistant", "content": assistant_message})

        if pending_enquiry:
            print(f"\n{assistant_message}")
            confirmation = input("\nConfirm submission? (yes/no): ").strip().lower()

            if confirmation in ("yes", "y"):
                result = submit_enquiry(**pending_enquiry)
                if "id" in result:
                    assistant_message = f"Enquiry submitted successfully! Reference ID: {result['id']}"
                else:
                    assistant_message = f"Sorry, I couldn't save the enquiry. {result.get('error', '')}"
            else:
                assistant_message = "Enquiry cancelled. Is there anything else I can help with?"

            messages.append({"role": "assistant", "content": assistant_message})
            pending_enquiry = None

        return assistant_message, messages


def ask_llm_with_tools(messages: list[dict], tools: list[dict]) -> dict:
    """Call the LLM with tool support."""
    system_message = ""
    memory = []
    user_message = ""

    for msg in messages:
        if msg["role"] == "system":
            system_message = msg["content"]
        elif msg["role"] == "user":
            user_message = msg["content"]
        elif msg["role"] == "assistant":
            memory.append({"role": "assistant", "content": msg["content"]})
        elif msg["role"] == "tool":
            memory.append({"role": "assistant", "content": f"Tool result: {msg['content']}"})


    tool_descriptions = "\n".join([
        f"- {t['function']['name']}: {t['function']['description']}\n  Parameters: {json.dumps(t['function']['parameters'], indent=2)}"
        for t in tools
    ])

    history_lines = []
    for msg in messages:
        if msg["role"] == "user":
            history_lines.append(f"User: {msg['content']}")
        elif msg["role"] == "assistant":
            if msg["content"].startswith("Tool result: "):
                history_lines.append(f"Tool Result: {msg['content'][13:]}")
            else:
                history_lines.append(f"Assistant: {msg['content']}")

    conversation_context = "\n".join(history_lines) if history_lines else "(no previous conversation)"

    tool_prompt = f"""You have access to the following tools:

{tool_descriptions}

To call a tool, respond with a JSON object in this format:
{{
  "tool_calls": [
    {{
      "id": "call_1",
      "function": {{
        "name": "tool_name",
        "arguments": "{{\\"param\\": \\"value\\"}}"
      }}
    }}
  ]
}}

If you don't need to call a tool, respond normally with your answer.

Conversation so far:
{conversation_context}

Now respond to the latest user message or tool result. If you have enough information, provide a final answer. If you need more information, call a tool."""

    response_text = ask_llm(tool_prompt, system_message, memory)

    try:
        parsed = json.loads(response_text)
        if "tool_calls" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass

    return {"content": response_text}


