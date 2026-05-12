import os
from google import genai

def answer_code_question_with_gemini(question: str, context: dict):
    if not os.getenv("GEMINI_API_KEY"):
        return None, "None", "GEMINI_API_KEY not found"

    prompt = f"""
You are a code analysis assistant for a project called Code Cognitive System.

Use only the structured context below to answer the user's question.

Context:
{context}

User question:
{question}

Give a clear, useful answer. Mention function names when relevant.
Keep the answer concise and practical.
"""

    try:
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = getattr(response, "text", None)

        if text and text.strip():
            return text.strip(), "Gemini", None

        return None, "None", "Gemini returned empty response"

    except Exception as e:
        return None, "None", str(e)
