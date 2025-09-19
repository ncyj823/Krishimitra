from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import pipeline
from googletrans import Translator
from gtts import gTTS
import os
from fastapi.responses import FileResponse
import soundfile as sf
import wave
from vosk import Model, KaldiRecognizer

# Load a free Hugging Face conversational pipeline (DistilGPT-2)
translator = Translator()
chatbot = pipeline("text-generation", model="distilgpt2")

krishibot = FastAPI()

# Load Vosk model for STT (English)
vosk_model_path = "vosk-model-small-en-us-0.15"  # Download and place in project folder
if os.path.exists(vosk_model_path):
    vosk_model = Model(vosk_model_path)
else:
    vosk_model = None
@krishibot.post("/stt")
async def stt(audio: UploadFile = File(...)):
    """Speech-to-text endpoint. Accepts WAV audio file, returns recognized text."""
    if not vosk_model:
        return {"error": "Vosk model not found. Please download and place 'vosk-model-small-en-us-0.15' in the project folder."}
    # Save uploaded file
    audio_path = f"temp_{audio.filename}"
    with open(audio_path, "wb") as f:
        f.write(await audio.read())
    # Open audio file for Vosk
    wf = wave.open(audio_path, "rb")
    rec = KaldiRecognizer(vosk_model, wf.getframerate())
    rec.SetWords(True)
    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            results.append(rec.Result())
    final_result = rec.FinalResult()
    os.remove(audio_path)
    return {"text": final_result}
@krishibot.post("/tts")
async def tts(text: str, language: str = "en"):
    """Text-to-speech endpoint. Accepts text and language, returns MP3 audio file."""
    tts = gTTS(text=text, lang=language)
    audio_path = "output.mp3"
    tts.save(audio_path)
    return FileResponse(audio_path, media_type="audio/mpeg", filename="output.mp3")

# Allow Flutter to connect
krishibot.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@krishibot.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message.lower()
    try:
        # Detect language (Hindi, Punjabi, Odia, English)
        lang = "en"
        if any(word in user_message for word in ["hindi", "हिंदी", "हिन्दी"]):
            lang = "hi"
        elif any(word in user_message for word in ["punjabi", "ਪੰਜਾਬੀ"]):
            lang = "pa"
        elif any(word in user_message for word in ["odia", "ଓଡ଼ିଆ"]):
            lang = "or"

        # Crop advice by month
        if "september" in user_message:
            reply = "In September, you can grow crops like paddy, maize, soybean, and groundnut depending on your region."
        elif "october" in user_message:
            reply = "In October, consider sowing wheat, barley, chickpea, and mustard."
        elif "november" in user_message:
            reply = "In November, wheat, lentil, and peas are good options."
        elif "december" in user_message:
            reply = "In December, focus on winter crops like wheat, mustard, and barley."
        # Fertilizer and pesticide guidance
        elif "fertilizer" in user_message or "pesticide" in user_message:
            reply = "Use fertilizers based on soil test results. For paddy, use urea and DAP. For pest control, use recommended pesticides and follow safety guidelines."
        # Government scheme info
        elif "scheme" in user_message or "government" in user_message:
            reply = "Check PM-KISAN, Soil Health Card, and Pradhan Mantri Fasal Bima Yojana for farmer benefits. Visit the official government agriculture portal for details."
        # Fallback to generic advice
        else:
            reply = "Please specify your query about crops, fertilizer, pesticide, or government schemes for more accurate advice."

        # Translate reply if needed
        if lang != "en":
            reply = translator.translate(reply, dest=lang).text
        return {"reply": reply}
    except Exception as e:
        return {"error": str(e)}



