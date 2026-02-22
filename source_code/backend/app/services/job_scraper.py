import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def scrape_job_from_url(url: str, timeout: int = 15) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    # Remove noise elements
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    # Try common job description containers first
    for selector in [
        "[class*='job-description']",
        "[class*='jobDescription']",
        "[class*='job_description']",
        "[id*='job-description']",
        "[id*='jobDescription']",
        "article",
        "main",
    ]:
        container = soup.select_one(selector)
        if container:
            text = container.get_text(separator="\n", strip=True)
            if len(text) > 200:
                return text

    # Fallback: entire body text
    return soup.get_text(separator="\n", strip=True)
