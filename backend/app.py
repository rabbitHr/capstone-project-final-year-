import os
import tempfile
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, Farmer, Labour, Job, Prediction, ChatHistory
from ai_services import (
    chat_with_ai,
    predict_crop_yield,
    recommend_crop,
    match_government_schemes,
    transcribe_audio,
    text_to_speech_sarvam,
)

load_dotenv()

app = Flask(__name__, static_folder=None)
CORS(app)

# Config
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///khetra_mitra.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-me")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

db.init_app(app)
jwt = JWTManager(app)

with app.app_context():
    db.create_all()

# ── Serve frontend ──────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..")


@app.route("/")
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, "capstone.html")


# ── Auth ────────────────────────────────────────────────────────
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")
    role = data.get("role", "farmer")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 409

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "username": username, "role": role}), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "username": user.username, "role": user.role})


# ── Farmer Registration ────────────────────────────────────────
@app.route("/api/farmer/register", methods=["POST"])
def register_farmer():
    data = request.get_json()
    farmer = Farmer(
        full_name=data.get("full_name", ""),
        village=data.get("village", ""),
        phone=data.get("phone", ""),
        land_size=data.get("land_size", 0),
    )
    db.session.add(farmer)
    db.session.commit()
    return jsonify({"message": "Farmer registered successfully", "id": farmer.id}), 201


# ── Labour Registration ────────────────────────────────────────
@app.route("/api/labour/register", methods=["POST"])
def register_labour():
    data = request.get_json()
    labour = Labour(
        full_name=data.get("full_name", ""),
        phone=data.get("phone", ""),
        work_type=data.get("work_type", ""),
        location=data.get("location", ""),
        experience=data.get("experience", 0),
    )
    db.session.add(labour)
    db.session.commit()
    return jsonify({"message": "Labour registered successfully", "id": labour.id}), 201


# ── Jobs ────────────────────────────────────────────────────────
@app.route("/api/jobs", methods=["POST"])
def post_job():
    data = request.get_json()
    job = Job(
        employer_name=data.get("employer_name", ""),
        district=data.get("district", ""),
        wage=data.get("wage", 0),
        experience_required=data.get("experience_required", ""),
        min_rating=data.get("min_rating", 1),
    )
    db.session.add(job)
    db.session.commit()
    return jsonify({"message": "Job posted successfully", "id": job.id}), 201


@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    district = request.args.get("district")
    query = Job.query.filter_by(status="open")
    if district:
        query = query.filter_by(district=district)
    jobs = query.order_by(Job.created_at.desc()).all()
    return jsonify([
        {
            "id": j.id,
            "employer_name": j.employer_name,
            "district": j.district,
            "wage": j.wage,
            "experience_required": j.experience_required,
            "min_rating": j.min_rating,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ])


# ── AI Crop Yield Prediction ───────────────────────────────────
@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json()
    crop_year = data.get("crop_year", 2024)
    area = data.get("area", 10)
    rainfall = data.get("rainfall", 800)
    fertilizer = data.get("fertilizer", 50)
    pesticide = data.get("pesticide", 20)
    language = data.get("language", "english")

    ai_result = predict_crop_yield(crop_year, area, rainfall, fertilizer, pesticide, language)

    prediction = Prediction(
        crop_year=crop_year,
        area=area,
        rainfall=rainfall,
        fertilizer=fertilizer,
        pesticide=pesticide,
        predicted_yield=ai_result[:500],
        ai_analysis=ai_result,
    )
    db.session.add(prediction)
    db.session.commit()

    return jsonify({"prediction": ai_result, "id": prediction.id})


# ── AI Chatbot ──────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")
    language = data.get("language", "english")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    ai_response = chat_with_ai(message, language)

    record = ChatHistory(
        user_message=message,
        ai_response=ai_response,
        language=language,
        was_voice=data.get("was_voice", False),
    )
    db.session.add(record)
    db.session.commit()

    # Generate TTS audio via Sarvam AI
    audio_base64 = None
    try:
        audio_base64 = text_to_speech_sarvam(ai_response, language)
    except Exception:
        pass  # TTS is optional, chat still works without it

    return jsonify({"response": ai_response, "audio": audio_base64})


# ── Voice Input (Whisper via Groq) ──────────────────────────────
@app.route("/api/voice", methods=["POST"])
def voice_input():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    language = request.form.get("language", "english")

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Step 1: Transcribe with Whisper
        transcription = transcribe_audio(tmp_path)

        # Step 2: Get AI response for the transcribed text
        ai_response = chat_with_ai(transcription, language)

        # Save to history
        record = ChatHistory(
            user_message=transcription,
            ai_response=ai_response,
            language=language,
            was_voice=True,
        )
        db.session.add(record)
        db.session.commit()

        # Generate TTS audio via Sarvam AI
        audio_base64 = None
        try:
            audio_base64 = text_to_speech_sarvam(ai_response, language)
        except Exception:
            pass

        return jsonify({
            "transcription": transcription,
            "response": ai_response,
            "audio": audio_base64,
        })
    finally:
        os.unlink(tmp_path)


# ── Text-to-Speech (Sarvam AI) ─────────────────────────────────
@app.route("/api/tts", methods=["POST"])
def tts():
    data = request.get_json()
    text = data.get("text", "")
    language = data.get("language", "english")

    if not text:
        return jsonify({"error": "Text is required"}), 400

    try:
        audio_base64 = text_to_speech_sarvam(text, language)
        if audio_base64:
            return jsonify({"audio": audio_base64})
        return jsonify({"error": "Sarvam API key not set or TTS failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Crop Recommendation ────────────────────────────────────────
@app.route("/api/recommend-crop", methods=["POST"])
def crop_recommendation():
    data = request.get_json()
    result = recommend_crop(
        district=data.get("district", "Ludhiana"),
        season=data.get("season", "Kharif"),
        soil_type=data.get("soil_type", "Alluvial"),
        land_size=data.get("land_size", 5),
    )
    return jsonify({"recommendation": result})


# ── Government Scheme Matcher ──────────────────────────────────
@app.route("/api/schemes", methods=["POST"])
def scheme_matcher():
    data = request.get_json()
    result = match_government_schemes(
        land_size=data.get("land_size", 5),
        crop_type=data.get("crop_type", "Wheat"),
        district=data.get("district", "Ludhiana"),
    )
    return jsonify({"schemes": result})


# ── Chat History ───────────────────────────────────────────────
@app.route("/api/chat/history", methods=["GET"])
def chat_history():
    chats = ChatHistory.query.order_by(ChatHistory.created_at.desc()).limit(50).all()
    return jsonify([
        {
            "id": c.id,
            "user_message": c.user_message,
            "ai_response": c.ai_response,
            "language": c.language,
            "was_voice": c.was_voice,
            "created_at": c.created_at.isoformat(),
        }
        for c in chats
    ])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
