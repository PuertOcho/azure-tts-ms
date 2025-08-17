import os
import requests
import tempfile
import shutil
from datetime import datetime
import soundfile as sf
import numpy as np
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuración del servicio
AZURE_TTS_KEY = os.environ.get("AZURE_TTS_KEY")
AZURE_TTS_REGION = os.environ.get("AZURE_TTS_REGION")
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "es-ES")
DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "Abril")
DEBUG_AUDIO = os.getenv("DEBUG_AUDIO", "true").lower() == "true"

# Configuración del servidor Flask
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))

if not AZURE_TTS_KEY or not AZURE_TTS_REGION:
    raise Exception("Azure TTS credentials not found in environment variables.")

# Crear directorio para audio de debug
DEBUG_DIR = "/app/debug_audio"
if DEBUG_AUDIO and not os.path.exists(DEBUG_DIR):
    os.makedirs(DEBUG_DIR, exist_ok=True)

print(f"[*] Iniciando Azure TTS Service")
print(f"[*] Host: {FLASK_HOST}:{FLASK_PORT}")
print(f"[*] Región: {AZURE_TTS_REGION}")
print(f"[*] Idioma por defecto: {DEFAULT_LANGUAGE}")
print(f"[*] Voz por defecto: {DEFAULT_VOICE}")
print(f"[*] Debug de audio: {'ACTIVADO' if DEBUG_AUDIO else 'DESACTIVADO'}")
if DEBUG_AUDIO:
    print(f"[*] Directorio de debug: {DEBUG_DIR}")

# Configuración de voces disponibles en Azure TTS para español
AVAILABLE_VOICES = {
    'es-ES': {  # Español de España
        'female': ['Abril', 'Elvira', 'Esperanza', 'Estrella', 'Irene', 'Laia', 'Lia', 'Lola', 'Mar', 'Nia', 'Sol', 'Tania', 'Vega', 'Vera'],
        'male': ['Alvaro', 'Arnau', 'Dario', 'Elias', 'Nil', 'Saul'],
        'default': 'Abril'
    },
    'es-MX': {  # Español de México
        'female': ['Dalia', 'Renata'],
        'male': ['Jorge', 'Liberto'],
        'default': 'Dalia'
    },
    'es-AR': {  # Español de Argentina
        'female': ['Elena'],
        'male': ['Tomas'],
        'default': 'Elena'
    },
    'es-CO': {  # Español de Colombia
        'female': [],  # Ximena no está disponible
        'male': ['Gonzalo'],
        'default': 'Gonzalo'  # Cambiado de Ximena a Gonzalo
    },
    'es-CL': {  # Español de Chile
        'female': ['Catalina'],
        'male': ['Lorenzo'],
        'default': 'Catalina'
    },
    'es-PE': {  # Español de Perú
        'female': ['Camila'],
        'male': ['Alex'],
        'default': 'Camila'
    },
    'es-VE': {  # Español de Venezuela
        'female': ['Paola'],
        'male': ['Sebastian'],
        'default': 'Paola'
    }
}

# Mapeo de idiomas cortos a completos
LANGUAGE_MAP = {
    'es': 'es-ES',
    'es-es': 'es-ES',
    'es-mx': 'es-MX',
    'es-ar': 'es-AR',
    'es-co': 'es-CO',
    'es-cl': 'es-CL',
    'es-pe': 'es-PE',
    'es-ve': 'es-VE'
}

def get_optimal_voice_for_language(language, voice=None, gender_preference=None):
    """Selecciona la voz óptima según el idioma y preferencias"""
    
    # Normalizar idioma
    language = LANGUAGE_MAP.get(language.lower(), language)
    
    # Obtener voces disponibles para el idioma
    lang_voices = AVAILABLE_VOICES.get(language, AVAILABLE_VOICES['es-ES'])
    
    # Si se especifica una voz, validarla
    if voice:
        all_voices = lang_voices['female'] + lang_voices['male']
        if voice in all_voices:
            return voice
    
    # Si se especifica preferencia de género
    if gender_preference in ['female', 'male'] and gender_preference in lang_voices:
        recommended_voices = lang_voices[gender_preference]
        if recommended_voices:
            return recommended_voices[0]
    
    # Devolver la voz por defecto del idioma
    return lang_voices.get('default', DEFAULT_VOICE)

def synthesize_with_azure_tts(text, language="es-ES", voice="Abril", speed=1.0):
    """Sintetiza audio usando Azure TTS"""
    try:
        print(f"[DEBUG] Sintetizando con Azure TTS: lang={language}, voice={voice}, speed={speed}")
        
        tts_url = f"https://{AZURE_TTS_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"

        headers = {
            "Ocp-Apim-Subscription-Key": AZURE_TTS_KEY,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-24khz-160kbitrate-mono-mp3",
        }

        # Ajustar velocidad para SSML (0.5 a 2.0 es el rango válido)
        adjusted_speed = max(0.5, min(2.0, speed))
        
        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='{language}'>
            <voice name='{language}-{voice}Neural'>
                <prosody rate='{adjusted_speed}'>{text}</prosody>
            </voice>
        </speak>
        """

        response = requests.post(tts_url, headers=headers, data=ssml.encode('utf-8'))
        response.raise_for_status()

        # Guardar temporalmente como MP3 y convertir a WAV
        temp_mp3 = tempfile.mktemp(suffix=".mp3")
        with open(temp_mp3, "wb") as f:
            f.write(response.content)
        
        # Leer MP3 y convertir a arrays numpy
        import librosa
        audio_data, sample_rate = librosa.load(temp_mp3, sr=24000)
        os.unlink(temp_mp3)
        
        print(f"[DEBUG] Audio generado: {len(audio_data)} muestras a {sample_rate}Hz")
        
        return audio_data, sample_rate
        
    except Exception as e:
        print(f"[!] Error en Azure TTS: {e}")
        raise e

@app.route("/health", methods=["GET"])
def health():
    """Endpoint de salud"""
    try:
        # Verificar conectividad con Azure TTS
        test_url = f"https://{AZURE_TTS_REGION}.tts.speech.microsoft.com/cognitiveservices/voices/list"
        headers = {"Ocp-Apim-Subscription-Key": AZURE_TTS_KEY}
        response = requests.get(test_url, headers=headers, timeout=5)
        azure_available = response.status_code == 200
    except:
        azure_available = False
    
    return jsonify({
        'status': 'ok' if azure_available else 'degraded',
        'model': 'azure-tts',
        'region': AZURE_TTS_REGION,
        'azure_available': azure_available,
        'default_language': DEFAULT_LANGUAGE,
        'default_voice': DEFAULT_VOICE
    })

@app.route("/voices", methods=["GET"])
def get_voices():
    """Obtener voces disponibles"""
    language = request.args.get('language', 'all')
    
    if language == "all":
        return jsonify({
            "voices_by_language": AVAILABLE_VOICES,
            "language_map": LANGUAGE_MAP,
            "default_language": DEFAULT_LANGUAGE,
            "default_voice": DEFAULT_VOICE,
            "total_voices": sum(len(lang_data['female']) + len(lang_data['male']) 
                              for lang_data in AVAILABLE_VOICES.values()),
            "model": "azure-tts"
        })
    else:
        # Normalizar idioma
        normalized_lang = LANGUAGE_MAP.get(language.lower(), language)
        voices_data = AVAILABLE_VOICES.get(normalized_lang, {})
        
        return jsonify({
            "language": normalized_lang,
            "voices": voices_data,
            "total": len(voices_data.get('female', [])) + len(voices_data.get('male', [])),
            "model": "azure-tts"
        })

@app.route("/synthesize", methods=["POST"])
def synthesize():
    """Endpoint principal de síntesis - devuelve archivo WAV"""
    try:
        data = request.get_json()
        
        if not data or "text" not in data:
            return jsonify({"error": "No text provided"}), 400

        text = data.get("text", "").strip()
        if not text:
            return jsonify({"error": "Empty text"}), 400

        # Obtener parámetros
        language = data.get("language", DEFAULT_LANGUAGE)
        requested_voice = data.get("voice")
        speed = float(data.get("speed", 1.0))
        gender_preference = data.get("gender_preference")
        
        # Normalizar idioma
        language = LANGUAGE_MAP.get(language.lower(), language)
        
        # Seleccionar voz óptima
        voice = get_optimal_voice_for_language(language, requested_voice, gender_preference)
        
        print(f"[*] Sintetizando (Azure TTS): '{text[:50]}...' [Lang: {language}, Voz: {voice}, Speed: {speed}]")

        # Síntesis con Azure TTS
        audio_data, sample_rate = synthesize_with_azure_tts(text, language, voice, speed)
        
        # Crear archivo temporal WAV
        temp_path = tempfile.mktemp(suffix=".wav")
        sf.write(temp_path, audio_data, sample_rate)

        # Guardar audio para debug si está activado
        if DEBUG_AUDIO:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            debug_filename = f"azure_{voice}_{timestamp}.wav"
            debug_path = os.path.join(DEBUG_DIR, debug_filename)
            shutil.copy2(temp_path, debug_path)
            print(f"[DEBUG] Audio guardado: {debug_filename}")

        # Enviar el archivo de audio
        return send_file(temp_path, 
                        mimetype="audio/wav", 
                        as_attachment=True,
                        download_name=f"azure_{voice}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")

    except Exception as e:
        print(f"[!] Error en síntesis: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/synthesize_json", methods=["POST"])
def synthesize_json():
    """Endpoint de síntesis con respuesta JSON"""
    try:
        data = request.get_json()
        
        if not data or "text" not in data:
            return jsonify({"error": "No text provided"}), 400

        text = data.get("text", "").strip()
        if not text:
            return jsonify({"error": "Empty text"}), 400

        # Obtener parámetros
        language = data.get("language", DEFAULT_LANGUAGE)
        requested_voice = data.get("voice")
        speed = float(data.get("speed", 1.0))
        gender_preference = data.get("gender_preference")
        
        # Normalizar idioma
        language = LANGUAGE_MAP.get(language.lower(), language)
        
        # Seleccionar voz óptima
        voice = get_optimal_voice_for_language(language, requested_voice, gender_preference)
        
        print(f"[*] Sintetizando JSON (Azure TTS): '{text[:50]}...' [Lang: {language}, Voice: {voice}]")

        # Síntesis con Azure TTS
        audio_data, sample_rate = synthesize_with_azure_tts(text, language, voice, speed)
        
        # Calcular duración
        duration = len(audio_data) / sample_rate

        # Guardar audio para debug si está activado
        debug_filename = None
        if DEBUG_AUDIO:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            debug_filename = f"azure_{voice}_{timestamp}.wav"
            debug_path = os.path.join(DEBUG_DIR, debug_filename)
            sf.write(debug_path, audio_data, sample_rate)
            print(f"[DEBUG] Audio guardado: {debug_filename}")

        # Convertir audio a Base64 para incluir en la respuesta JSON
        import base64
        import io
        
        # Guardar audio en buffer de memoria
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, audio_data, sample_rate, format='WAV')
        audio_buffer.seek(0)
        
        # Convertir a Base64
        audio_base64 = base64.b64encode(audio_buffer.getvalue()).decode('utf-8')
        
        response_data = {
            "success": True,
            "text": text,
            "language": language,
            "voice": voice,
            "audio_duration": duration,
            "sample_rate": sample_rate,
            "model": "azure-tts",
            "speed": speed,
            "region": AZURE_TTS_REGION,
            "audio_data": audio_base64,  # Audio en Base64
            "audio_format": "wav",
            "audio_size_bytes": len(audio_buffer.getvalue())
        }
        
        if DEBUG_AUDIO and debug_filename:
            response_data["debug_audio_file"] = debug_filename
            response_data["debug_audio_url"] = f"/debug/audio/{debug_filename}"

        return jsonify(response_data)

    except Exception as e:
        print(f"[!] Error en síntesis JSON: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/debug/audio/<filename>", methods=["GET"])
def get_debug_audio(filename):
    """Servir archivos de audio de debug"""
    try:
        file_path = os.path.join(DEBUG_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "Debug audio file not found"}), 404
        
        return send_file(file_path, mimetype="audio/wav")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug/audio", methods=["GET"])
def list_debug_audio():
    """Listar archivos de audio de debug disponibles"""
    try:
        if not os.path.exists(DEBUG_DIR):
            return jsonify({"debug_files": []})
        
        files = []
        for filename in os.listdir(DEBUG_DIR):
            if filename.endswith('.wav'):
                file_path = os.path.join(DEBUG_DIR, filename)
                stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "url": f"/debug/audio/{filename}"
                })
        
        # Ordenar por fecha de creación (más reciente primero)
        files.sort(key=lambda x: x['created'], reverse=True)
        
        return jsonify({
            "debug_files": files,
            "total": len(files),
            "debug_enabled": DEBUG_AUDIO
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT) 