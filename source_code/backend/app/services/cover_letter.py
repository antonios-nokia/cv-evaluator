from app.services import ollama_client

CL_SYSTEM = (
    "You are an expert career coach and professional writer. "
    "You write compelling, tailored cover letters."
)

CL_PROMPT_TEMPLATE = """Write a professional cover letter for the following CV and job description.

CV:
{cv_text}

---

Job Description:
{job_description}

---

Requirements:
- 3-4 paragraphs
- Professional tone
- Highlight top 3 matching qualifications
- Show enthusiasm for the role
- End with a call to action
- Do NOT include date or address fields — only the body text

Output only the cover letter body text, no preamble."""


async def generate_cover_letter(cv_text: str, job_description: str) -> str:
    prompt = CL_PROMPT_TEMPLATE.format(
        cv_text=cv_text[:8000],
        job_description=job_description[:4000],
    )
    return await ollama_client.complete(prompt, system=CL_SYSTEM)
