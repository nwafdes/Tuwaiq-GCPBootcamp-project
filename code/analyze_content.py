"""
Secrets analyzer powered by Gemini (Vertex AI).

Env:
  - GOOGLE_GENAI_USE_VERTEXAI=True
  - GOOGLE_CLOUD_PROJECT=<your-project-id>
  - GOOGLE_CLOUD_LOCATION=global
  - GEMINI_MODEL (optional, defaults to "gemini-2.5-flash")
"""

import os
import json
import logging
from typing import Any, Dict
from string import Template
from google import genai
from google.genai.types import HttpOptions, GenerateContentConfig

# Create one client up-front; reuse across invocations
CLIENT = genai.Client(http_options=HttpOptions(api_version="v1"))
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ---- Prompt: detect secrets in the content -----------------------------------
# This prompt is optimized for secret detection and *masked* output.

DETECTION_PROMPT_TEMPLATE = Template("""You are a security code reviewer. Analyze the provided file content and detect any potential secrets or sensitive data.

Your response MUST be:
- A single valid JSON object
- Strictly following the schema provided
- No Markdown formatting, no code fences, no extra text

Schema:
{
  "has_secrets": <true|false>,
  "findings": [
    {
      "type": "<api_key | password | private_key | token | oauth_client_secret | cloud_key | db_connection | jwt | certificate | pii | other>",
      "name": "<short label or provider if known, e.g., 'Stripe', 'AWS', 'GCP SA key'>",
      "masked_value": "<mask all characters except the last 4; preserve any obvious prefixes, e.g. 'sk_test_****abcd'>",
      "match_excerpt": "<short excerpt around the match, with sensitive parts masked the same way as masked_value>",
      "line": <approx line number if possible, else null>,
      "confidence": <0.0-1.0>,
      "reasoning": "<one sentence why this is likely a secret>"
    }
  ],
  "summary": {
    "count": <number of findings>,
    "suggested_actions": [
      "Revoke and rotate any exposed keys",
      "Remove secrets from source; use a secrets manager",
      "Add automated scanning to CI/CD"
    ]
  }
}

Rules:
- Absolutely DO NOT return Markdown code blocks, triple backticks, or escape characters like \\n or \\".
- If no secrets are found: has_secrets=false, findings=[], summary.count=0.
- Always mask properly: keep last 4 characters visible, everything else replaced with '*'.
- Be conservative: if unsure, set confidence around 0.4-0.6 and explain briefly.

=== FILE CONTENT START ===
${content}
=== FILE CONTENT END ===
""")

def _build_prompt(text: str) -> str:
    max_chars = int(os.getenv("SECRETS_ANALYZER_MAX_CHARS", "400000"))
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[TRUNCATED]"
    return DETECTION_PROMPT_TEMPLATE.substitute(content=text)

def analyze_with_gemini(text: str) -> Dict[str, Any]:
    """
    Runs Gemini with a secret-detection prompt and returns a Python dict.
    The model is instructed to return pure JSON.
    """
    prompt = _build_prompt(text)
    resp = CLIENT.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=1024,
        ),
    )
    raw = (resp.text or "").strip()

    # Best-effort: parse JSON; if it fails, wrap it
    try:
        return json.loads(raw)
    except Exception:
        logging.warning("Gemini did not return valid JSON; wrapping raw text.")
        return {"has_secrets": None, "findings": [], "summary": {"count": 0}, "raw": raw}

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Local test:
      python secrets_analyzer.py <path_to_file>
    """
    import sys
    if len(sys.argv) != 2:
        print("Usage: python secrets_analyzer.py <path_to_file>")
        raise SystemExit(2)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    result = analyze_with_gemini(content)
    # Pretty-print once, single-line per logging best practices
    print(json.dumps(result, ensure_ascii=False))
