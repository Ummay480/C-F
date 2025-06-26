import os
import csv
import fitz  # PyMuPDF
import difflib
import json
from dotenv import load_dotenv
import chainlit as cl
from openai import AsyncOpenAI

# Load API key from .env
load_dotenv()

# Create upload folder
UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Gemini (OpenAI-compatible) client
client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# PDF text extraction
def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text.strip()

# Fuzzy HS Code matching
def match_hs_code(item_name):
    with open("hs_lookup.csv", "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        items = [row["Item"] for row in reader]

    matches = difflib.get_close_matches(item_name.strip().lower(), [i.lower() for i in items], n=1, cutoff=0.5)

    if matches:
        matched_name = matches[0]
        with open("hs_lookup.csv", "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Item"].strip().lower() == matched_name:
                    return f"{row['HS Code']} (matched with: {row['Item']})"

    return "❓ Not Found — Needs Manual Classification"

# Initial message
@cl.on_chat_start
async def start():
    await cl.Message("📦 Upload your Import Invoice PDF **or** paste invoice text below.").send()

# Handle both file or text
@cl.on_message
async def handle_input(message: cl.Message):
    # 🧾 For file uploads
    if message.elements:
        for element in message.elements:
            if isinstance(element, cl.File):
                path = os.path.join(UPLOAD_DIR, element.name)
                file_bytes = await element.get_content()  # ✅ Fix
                with open(path, "wb") as f:
                    f.write(file_bytes)  # ✅ Fix
                extracted_text = extract_text_from_pdf(path)

                # Optional: Filter lines to improve LLM result
                keywords = ["invoice", "date", "item", "quantity", "price", "value", "origin", "hs code", "incoterm", "description"]
                lines = extracted_text.splitlines()
                filtered_lines = [line for line in lines if any(k in line.lower() for k in keywords)]
                filtered_text = "\n".join(filtered_lines)

                await process_invoice(filtered_text)
                return


    # If no file uploaded, use text directly
    await process_invoice(message.content)

# Process the invoice text with Gemini
async def process_invoice(text):
    await cl.Message("🧠 Processing invoice using Gemini...").send()

    prompt = f"""
You're an AI assistant specialized in import invoice processing.

From the following raw invoice text, extract and return only these fields in **valid JSON** format:
- Invoice Number
- Invoice Date
- Item Description
- Quantity
- Unit Value
- Total Value
- Country of Origin
- Currency (if available)
- HS Code (if listed)
- Incoterm (if mentioned)

Text:
{text}
"""

    response = await client.chat.completions.create(
        model="gemini-1.5-flash",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    extracted = response.choices[0].message.content

    # Debug: Show Gemini’s raw response if needed
    print("🔍 Gemini raw output:\n", extracted)

    try:
        data = json.loads(extracted)
    except Exception:
        await cl.Message("⚠️ Gemini returned an invalid JSON. Here is the raw response:\n```\n" + extracted + "\n```").send()
        return

    # Add fallback for missing Incoterm
    if not data.get("Incoterm"):
        data["Incoterm"] = "⚠️ Not specified — please add manually"

    # Add HS code from local lookup if missing
    item_name = data.get("Item") or data.get("Item Description") or ""
    if not data.get("HS Code") or "not found" in str(data.get("HS Code")).lower():
        data["HS Code"] = match_hs_code(item_name)

    # Return JSON
    await cl.Message(f"✅ Extracted Invoice:\n```json\n{json.dumps(data, indent=2)}\n```").send()
