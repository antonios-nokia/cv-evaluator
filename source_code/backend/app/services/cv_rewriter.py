from app.services import ollama_client

REWRITE_SYSTEM = (
    "You are an expert CV editor. You improve CVs by enhancing and adding to them — "
    "never by removing or shortening existing content."
)

REWRITE_PROMPT_TEMPLATE = """Edit the CV below to better match the job description.

STRICT RULES — follow these exactly:
1. Keep the EXACT same structure and sections as the original CV
2. Keep ALL existing content — do not remove, shorten, or paraphrase any existing bullet point
3. Only ADD new bullet points or ENHANCE existing ones using the candidate's confirmed additional context
4. Insert new information naturally into the most relevant existing section
5. Do not invent anything — only use information the candidate has explicitly confirmed
6. Maintain the exact same writing style, tone, and formatting as the original

Original CV (preserve this structure exactly):
{cv_text}

---

Job Description (use this to guide which skills to highlight):
{job_description}

---

Additional skills and experience confirmed by the candidate (incorporate these):
{chat_context}

---

Output the improved CV. Same structure, same sections, same existing content — only additions and enhancements. Output the CV text only, no preamble or commentary."""


async def rewrite_cv(
    cv_text: str,
    job_description: str,
    chat_history: list[dict],
) -> str:
    user_messages = [
        msg["content"]
        for msg in chat_history
        if msg.get("role") == "user"
    ]
    chat_context = "\n".join(f"- {m}" for m in user_messages) if user_messages else "None provided."

    prompt = REWRITE_PROMPT_TEMPLATE.format(
        cv_text=cv_text[:8000],
        job_description=job_description[:4000],
        chat_context=chat_context[:3000],
    )
    return await ollama_client.complete(prompt, system=REWRITE_SYSTEM)
