import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are Khetra Mitra AI, a smart agriculture assistant for farmers in Punjab, India.
You help farmers with:
- Crop yield predictions and analysis
- Crop disease identification and treatment
- Best farming practices for Punjab region
- Government schemes (PM Kisan, PMFBY, eNAM)
- Soil health and fertilizer recommendations
- Weather impact on crops
- Market prices and best time to sell

Always be helpful, practical, and give actionable advice.
You can respond in English, Hindi, or Punjabi based on the language the farmer speaks.
Keep responses SHORT - maximum 2-3 sentences (under 50 words). Be direct and to the point. Only give longer answers if the farmer specifically asks for detailed explanation."""


def chat_with_ai(user_message, language="english"):
    """Send a message to Groq LLM and get farming advice."""
    lang_instruction = ""
    if language == "hindi":
        lang_instruction = " Respond in Hindi (Devanagari script)."
    elif language == "punjabi":
        lang_instruction = " Respond in Punjabi (Gurmukhi script)."

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT + lang_instruction},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def predict_crop_yield(crop_year, area, rainfall, fertilizer, pesticide, language="english"):
    """Use Groq LLM to predict crop yield with detailed analysis."""
    lang_instruction = ""
    if language == "hindi":
        lang_instruction = " Respond entirely in Hindi (Devanagari script)."
    elif language == "punjabi":
        lang_instruction = " Respond entirely in Punjabi (Gurmukhi script)."

    prompt = f"""As an agricultural AI expert, analyze these farm parameters for Punjab, India and predict the crop yield:

- Crop Year: {crop_year}
- Area: {area} hectares
- Annual Rainfall: {rainfall} mm
- Fertilizer Used: {fertilizer} kg
- Pesticide Used: {pesticide} kg

Provide:
1. Estimated yield in Quintals (give a specific number range)
2. Whether conditions are favorable, moderate, or poor
3. One key recommendation to improve yield
4. Risk factors based on these parameters

Keep your response under 150 words and be specific with numbers.{lang_instruction}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert agricultural scientist specializing in Punjab, India crop yields. Give precise, data-driven predictions."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
        max_tokens=512,
    )
    return response.choices[0].message.content


def recommend_crop(district, season, soil_type, land_size):
    """AI-powered crop recommendation based on location and conditions."""
    prompt = f"""Recommend the best crops for a farmer in Punjab with these conditions:
- District: {district}
- Season: {season}
- Soil Type: {soil_type}
- Land Size: {land_size} acres

List top 3 crops with expected yield per acre and why they're suitable. Keep it under 120 words."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.6,
        max_tokens=512,
    )
    return response.choices[0].message.content


def match_government_schemes(land_size, crop_type, district):
    """Match farmer profile to relevant government schemes."""
    prompt = f"""A farmer in Punjab has:
- Land: {land_size} acres in {district}
- Growing: {crop_type}

List the top 3 most relevant Indian government schemes they should apply for.
For each scheme include: name, benefit amount, eligibility, and how to apply.
Keep response under 150 words."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=512,
    )
    return response.choices[0].message.content


def transcribe_audio(audio_file_path):
    """Transcribe audio using Groq Whisper API."""
    with open(audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=("audio.webm", audio_file.read()),
            model="whisper-large-v3",
            response_format="text",
        )
    return transcription


# ── Sarvam AI Text-to-Speech ────────────────────────────────────

# Language code mapping for Sarvam AI
SARVAM_LANG_MAP = {
    "english": "en-IN",
    "hindi": "hi-IN",
    "punjabi": "pa-IN",
    "bengali": "bn-IN",
    "gujarati": "gu-IN",
    "kannada": "kn-IN",
    "malayalam": "ml-IN",
    "marathi": "mr-IN",
    "odia": "od-IN",
    "tamil": "ta-IN",
    "telugu": "te-IN",
}

# Voice mapping per language for natural sounding output
SARVAM_VOICE_MAP = {
    "en-IN": "amelia",
    "hi-IN": "anand",
    "pa-IN": "anand",
    "bn-IN": "anand",
    "gu-IN": "anand",
    "kn-IN": "anand",
    "ml-IN": "anand",
    "mr-IN": "anand",
    "od-IN": "anand",
    "ta-IN": "anand",
    "te-IN": "anand",
}


def text_to_speech_sarvam(text, language="english"):
    """Convert text to speech using Sarvam AI Bulbul v3 model.
    Returns base64-encoded audio string."""
    import httpx

    sarvam_key = os.getenv("SARVAM_API_KEY")
    if not sarvam_key:
        return None

    lang_code = SARVAM_LANG_MAP.get(language, "en-IN")
    speaker = SARVAM_VOICE_MAP.get(lang_code, "anand")

    # Truncate to Sarvam's 2500 char limit
    if len(text) > 2500:
        text = text[:2497] + "..."

    payload = {
        "text": text,
        "target_language_code": lang_code,
        "speaker": speaker,
        "model": "bulbul:v3",
        "pace": 1.0,
        "speech_sample_rate": "24000",
        "output_audio_codec": "mp3",
    }

    response = httpx.post(
        "https://api.sarvam.ai/text-to-speech",
        json=payload,
        headers={
            "api-subscription-key": sarvam_key,
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )
    response.raise_for_status()

    data = response.json()
    if data.get("audios") and len(data["audios"]) > 0:
        return data["audios"][0]
    return None
