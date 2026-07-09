from google import genai
from google.genai import types
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import json


def save_txt(summary):
    with open("summarize.txt", "w", encoding="utf-8") as file:
        file.write(summary)
    print("Saved as summarize.txt")


def save_pdf(summary):
    pdf = canvas.Canvas("summary.pdf", pagesize=A4)
    width, height = A4

    x = 50
    y = height - 50

    pdf.setFont("Helvetica", 12)

    for line in summary.split("\n"):
        pdf.drawString(x, y, line)
        y -= 20

        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = height - 50

    pdf.save()
    print("Saved as summary.pdf")


client = genai.Client()

flag = "y"

while flag.lower() == "y":
    temp = float(input("Temperature: "))
    user_prompt = input("Enter your prompt: ")
    input_text = input("Enter the text: ")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"""
You are a professional summarization assistant.

Your tasks:

1. Read the user's request.
2. Summarize ONLY the text provided under the "Input Text" section.
3. Decide the output type:
   - If the user requests a PDF, set output_type to "pdf".
   - Otherwise set output_type to "txt".
4. Do NOT summarize the user's prompt.
5. Return ONLY valid JSON.
6. Do not add markdown formatting.
7. Do not use ```json.

Return exactly in this format:

{{
  "output_type": "pdf",
  "summary": "..."
}}

User Request:
{user_prompt}

Input Text:
{input_text}
""",
        config=types.GenerateContentConfig(temperature=temp)
    )

    raw = response.text.strip()

    raw = raw.replace("```json", "")
    raw = raw.replace("```", "")
    raw = raw.strip()

    try:
        data = json.loads(raw)

        output_type = data["output_type"]
        summary = data["summary"]

        print("Output type selected by LLM:", output_type)

        if output_type == "txt":
            save_txt(summary)

        elif output_type == "pdf":
            save_pdf(summary)

        else:
            print("Unknown output type:", output_type)

    except json.JSONDecodeError:
        print("The model did not return valid JSON.")
        print("Model response was:")
        print(raw)

    flag = input("Do you want to continue? (y/n): ")