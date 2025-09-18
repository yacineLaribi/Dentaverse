# app/services/gemini_service.py
import os, base64
from google import genai
from google.genai import types

client = genai.Client(api_key='AIzaSyA3l558qLO87babXA4li2X7mM03RRos3iQ')

def analyze_xray_with_gemini(image_path: str):
    prompt = """You are an expert dental radiologist AI assistant. Analyze this dental X-ray image and provide a detailed clinical assessment.
Return ONLY valid JSON with fields: detections[], recommendations[], overallAssessment, urgency."""

    # read file and base64 encode
    with open(image_path, "rb") as f:
        img_data = f.read()
    img_b64 = base64.b64encode(img_data).decode("utf-8")

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
                types.Part.from_inline_data(
                    mime_type="image/jpeg",  # or detect mimetype dynamically
                    data=img_b64,
                ),
            ],
        ),
    ]

    resp = client.models.generate_content(
        model="gemini-2.5-flash-image-preview",
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT"], # we only need JSON text back
        ),
    )

    # merge all text chunks
    text_out = ""
    for cand in resp.candidates:
        for part in cand.content.parts:
            if part.text:
                text_out += part.text

    return text_out
