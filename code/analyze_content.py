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

from google import genai
from google.genai.types import HttpOptions, GenerateContentConfig

# Create one client up-front; reuse across invocations
CLIENT = genai.Client(http_options=HttpOptions(api_version="v1"))
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ---- Prompt: detect secrets in the content -----------------------------------
# This prompt is optimized for secret detection and *masked* output.
DETECTION_PROMPT_TEMPLATE = """\
You are a security code reviewer. Analyze the provided file content and detect any potential secrets or sensitive data.

Return ONLY valid JSON (no markdown, no prose). Use this schema:
{{
  "has_secrets": <true|false>,
  "findings": [
    {{
      "type": "<one of: api_key | password | private_key | token | oauth_client_secret | cloud_key | db_connection | jwt | certificate | pii | other>",
      "name": "<short label or provider if known, e.g., 'Stripe', 'AWS', 'GCP SA key'>",
      "masked_value": "<original value masked: keep only last 4 visible, others as *>", 
      "match_excerpt": "<short excerpt around the match, with sensitive parts masked>",
      "line": <approx line number if possible, else null>,
      "confidence": <0.0-1.0>,
      "reasoning": "<one sentence why this is likely a secret>"
    }}
  ],
  "summary": {{
    "count": <number of findings>,
    "suggested_actions": [
      "Revoke and rotate any exposed keys",
      "Remove secrets from source; use a secrets manager",
      "Add automated scanning to CI/CD"
    ]
  }}
}}

Rules:
- DO NOT print full secret values; mask all but the last 4 characters. Example: "sk_test_********************abcd".
- If no secrets are found, set "has_secrets": false and "findings": [] and still include "summary".
- Be conservative: if unsure, set confidence around 0.4-0.6 and explain briefly.
- Consider common patterns: API keys, passwords, tokens (JWT/Bearer), OAuth client secrets, private keys (PEM), cloud creds (AWS/GCP/Azure), DB URLs, certificates, PII (emails, phone numbers) only if clearly sensitive in context.

=== FILE CONTENT START ===
{content}
=== FILE CONTENT END ===
"""

def _build_prompt(text: str) -> str:
    # (Optional) guardrail: clip extremely large inputs
    max_chars = int(os.getenv("SECRETS_ANALYZER_MAX_CHARS", "400000"))
    if len(text) > max_chars:
        text = text[:max_chars] + "\n[TRUNCATED]"
    return DETECTION_PROMPT_TEMPLATE.format(content=text)

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
