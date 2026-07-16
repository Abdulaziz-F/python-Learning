from io import BytesIO
from textwrap import wrap
import json
import re
import time

import requests
from google import genai
from google.genai import types
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# ---------------------------------
# Extract URLs from the email body
# ---------------------------------

def extract_urls(email_body: str) -> list[str]:
    """
    Extract all HTTP and HTTPS URLs from the email body.
    """

    pattern = r'https?://[^\s<>"\']+'
    urls = re.findall(pattern, email_body)

    cleaned_urls = []

    for url in urls:
        cleaned_url = url.rstrip(".,;:!?)]}")
        cleaned_urls.append(cleaned_url)

    return cleaned_urls


# ---------------------------------
# Submit a URL to VirusTotal
# ---------------------------------

def submit_url_to_virustotal(
    url: str,
    api_key: str
) -> str:
    """
    Submit a URL to VirusTotal and return the analysis ID.
    """

    headers = {
        "x-apikey": api_key
    }

    response = requests.post(
        "https://www.virustotal.com/api/v3/urls",
        headers=headers,
        data={"url": url},
        timeout=30
    )

    response.raise_for_status()

    response_data = response.json()

    return response_data["data"]["id"]


# ---------------------------------
# Get VirusTotal analysis results
# ---------------------------------

def get_virustotal_analysis(
    analysis_id: str,
    api_key: str,
    max_attempts: int = 20
) -> dict:
    """
    Wait for the VirusTotal analysis and return its statistics.
    """

    headers = {
        "x-apikey": api_key
    }

    analysis_url = (
        f"https://www.virustotal.com/api/v3/analyses/"
        f"{analysis_id}"
    )

    for _ in range(max_attempts):
        response = requests.get(
            analysis_url,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        attributes = response.json()["data"]["attributes"]
        status = attributes["status"]

        if status == "completed":
            return attributes["stats"]

        time.sleep(2)

    raise TimeoutError(
        "VirusTotal analysis did not finish in time."
    )


# ---------------------------------
# Scan all extracted URLs
# ---------------------------------

def scan_urls(
    urls: list[str],
    api_key: str
) -> list[dict]:
    """
    Scan every extracted URL using VirusTotal.
    """

    results = []

    for url in urls:
        try:
            analysis_id = submit_url_to_virustotal(
                url,
                api_key
            )

            stats = get_virustotal_analysis(
                analysis_id,
                api_key
            )

            results.append({
                "url": url,
                "status": "completed",
                "stats": {
                    "malicious": stats.get("malicious", 0),
                    "suspicious": stats.get("suspicious", 0),
                    "harmless": stats.get("harmless", 0),
                    "undetected": stats.get("undetected", 0),
                    "timeout": stats.get("timeout", 0)
                }
            })

        except TimeoutError:
            results.append({
                "url": url,
                "status": "pending",
                "error": (
                    "VirusTotal analysis is still in progress. "
                    "No final verdict is available."
                )
            })

        except requests.exceptions.RequestException as error:
            results.append({
                "url": url,
                "status": "failed",
                "error": str(error)
            })

    return results


# ---------------------------------
# Analyze the email with Gemini
# ---------------------------------

def analyze_email_with_gemini(
    sender: str,
    subject: str,
    email_body: str,
    vt_results: list[dict],
    gemini_api_key: str
) -> dict:
    """
    Send the email and VirusTotal results to Gemini.
    Return structured analysis data.
    """

    client = genai.Client(
        api_key=gemini_api_key
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",

        contents=f"""
You are a cybersecurity analyst specialized in phishing
email detection.

Analyze the email using:

1. The sender address.
2. The subject.
3. The email body.
4. The VirusTotal scan results, if available.

Return ONLY valid JSON using exactly this structure:

{{
  "summary": "short summary of the email",
  "classification": "Safe, Suspicious, or Phishing",
  "risk_score": 0,
  "confidence": 0,
  "threat_indicators": [
    "indicator 1",
    "indicator 2"
  ],
  "reasons": [
    "reason 1",
    "reason 2"
  ],
  "recommendation": "security recommendation"
}}

Rules:

- classification must be only:
  Safe, Suspicious, or Phishing.
- risk_score must be an integer from 0 to 100.
- confidence must be an integer from 0 to 100.
- Treat VirusTotal results as evidence, not absolute proof.
- If a VirusTotal scan is pending or failed, clearly state
  that the URL could not be verified.
- A pending or failed scan does not mean the URL is safe.
- Do not open or visit any URL.
- Base the assessment only on the supplied information.
- Do not use Markdown.
- Do not add explanations outside the JSON.

Sender:
{sender}

Subject:
{subject}

Email Body:
{email_body}

VirusTotal Results:
{json.dumps(vt_results, indent=2)}
""",

        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
    )

    raw_response = response.text.strip()

    try:
        return json.loads(raw_response)

    except json.JSONDecodeError as error:
        raise ValueError(
            "Gemini did not return valid JSON."
        ) from error


# ---------------------------------
# Complete analysis workflow
# ---------------------------------

def analyze_email(
    sender: str,
    subject: str,
    email_body: str,
    gemini_api_key: str,
    vt_api_key: str
) -> dict:
    """
    Run the complete phishing detection workflow.
    """

    urls = extract_urls(email_body)

    if urls:
        vt_results = scan_urls(
            urls,
            vt_api_key
        )
    else:
        vt_results = []

    analysis = analyze_email_with_gemini(
        sender=sender,
        subject=subject,
        email_body=email_body,
        vt_results=vt_results,
        gemini_api_key=gemini_api_key
    )

    return {
        "sender": sender,
        "subject": subject,
        "urls": urls,
        "virustotal_results": vt_results,
        "analysis": analysis
    }


# ---------------------------------
# Build a readable report
# ---------------------------------

def build_report(result: dict) -> str:
    """
    Convert the complete analysis result into a text report.
    """

    sender = result["sender"]
    subject = result["subject"]
    analysis = result["analysis"]
    vt_results = result["virustotal_results"]

    indicators_text = "\n".join(
        f"- {indicator}"
        for indicator in analysis["threat_indicators"]
    )

    reasons_text = "\n".join(
        f"- {reason}"
        for reason in analysis["reasons"]
    )

    vt_text_parts = []

    if vt_results:
        for item in vt_results:
            vt_text_parts.append(
                f"URL: {item['url']}"
            )

            vt_text_parts.append(
                f"Status: {item['status']}"
            )

            if "stats" in item:
                stats = item["stats"]

                vt_text_parts.append(
                    f"Malicious: {stats['malicious']}"
                )
                vt_text_parts.append(
                    f"Suspicious: {stats['suspicious']}"
                )
                vt_text_parts.append(
                    f"Harmless: {stats['harmless']}"
                )
                vt_text_parts.append(
                    f"Undetected: {stats['undetected']}"
                )
                vt_text_parts.append(
                    f"Timeout: {stats['timeout']}"
                )

            elif "error" in item:
                vt_text_parts.append(
                    f"Message: {item['error']}"
                )

            vt_text_parts.append("")

    else:
        vt_text_parts.append(
            "No URLs were found in the email."
        )

    vt_text = "\n".join(vt_text_parts)

    report = f"""
==================================================
              AI PHISHING EMAIL REPORT
==================================================

Sender:
{sender}

Subject:
{subject}

Email Summary:
{analysis["summary"]}

Classification:
{analysis["classification"]}

Risk Score:
{analysis["risk_score"]} / 100

Confidence:
{analysis["confidence"]}%

VirusTotal Results:
{vt_text}

Threat Indicators:
{indicators_text or "No threat indicators were identified."}

Reasons:
{reasons_text}

Recommendation:
{analysis["recommendation"]}

==================================================
"""

    return report.strip()


# ---------------------------------
# Create a TXT file in memory
# ---------------------------------

def create_txt_file(report: str) -> bytes:
    """
    Convert the report to TXT bytes for Streamlit download.
    """

    return report.encode("utf-8")


# ---------------------------------
# Create a PDF file in memory
# ---------------------------------

def create_pdf_file(report: str) -> bytes:
    """
    Create an A4 PDF in memory for Streamlit download.
    """

    pdf_buffer = BytesIO()

    pdf = canvas.Canvas(
        pdf_buffer,
        pagesize=A4
    )

    _, height = A4

    x = 50
    y = height - 50
    line_height = 18

    pdf.setFont(
        "Helvetica",
        11
    )

    for paragraph in report.split("\n"):
        if paragraph.strip() == "":
            y -= line_height
            continue

        wrapped_lines = wrap(
            paragraph,
            width=90
        )

        for line in wrapped_lines:
            if y < 50:
                pdf.showPage()
                pdf.setFont(
                    "Helvetica",
                    11
                )
                y = height - 50

            pdf.drawString(
                x,
                y,
                line
            )

            y -= line_height

    pdf.save()

    pdf_buffer.seek(0)

    return pdf_buffer.getvalue()