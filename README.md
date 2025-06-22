# Azure TTS Service

Servicio de Text-to-Speech usando Microsoft Azure Cognitive Services, configurado para ser consistente con otros servicios TTS del proyecto.

## 🚀 Configuración Rápida

### 1. Configurar Variables de Entorno

- Crear .env a partir de .env.example
- Editar .env con tus credenciales de Azure

### 2. Variables de Entorno Requeridas

```bash
# Credenciales Azure (OBLIGATORIAS)
AZURE_TTS_KEY=tu_clave_de_azure_aqui
AZURE_TTS_REGION=tu_region_de_azure_aqui

# Configuración del Contenedor
CONTAINER_NAME=azure-tts-service
HOST_PORT=5004
CONTAINER_PORT=5000

# Configuración del Servicio
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
DEFAULT_LANGUAGE=es-ES
DEFAULT_VOICE=Abril
DEBUG_AUDIO=true
```

### 3. Iniciar el Servicio

```bash
docker-compose up -d
```

## 📡 Endpoints Disponibles

### Health Check
```bash
GET http://localhost:5004/health
```

### Listar Voces
```bash
GET http://localhost:5004/voices
GET http://localhost:5004/voices?language=es-ES
```

### Síntesis de Audio (WAV)
```bash
POST http://localhost:5004/synthesize
Content-Type: application/json

{
  "text": "Hola, esto es una prueba de síntesis de voz",
  "language": "es-ES",
  "voice": "Abril",
  "speed": 1.0
}
```

### Síntesis con Metadata (JSON)
```bash
POST http://localhost:5004/synthesize_json
Content-Type: application/json

{
  "text": "Hola, esto es una prueba de síntesis de voz",
  "language": "es-ES",
  "voice": "Abril",
  "speed": 1.0,
  "gender_preference": "female"
}
```

### Debug Audio
```bash
GET http://localhost:5004/debug/audio
GET http://localhost:5004/debug/audio/nombre_archivo.wav
```

## 🎤 Voces Disponibles

### Español de España (es-ES)
- **Femeninas**: Abril, Elvira, Esperanza, Estrella, Irene, Laia, Lia, Lola, Mar, Nia, Sol, Tania, Vega, Vera
- **Masculinas**: Alvaro, Arnau, Dario, Elias, Nil, Saul

### Español de México (es-MX)
- **Femeninas**: Dalia, Renata
- **Masculinas**: Jorge, Liberto

### Español de Argentina (es-AR)
- **Femeninas**: Elena
- **Masculinas**: Tomas

### Español de Colombia (es-CO)
- **Femeninas**: Ximena
- **Masculinas**: Gonzalo

### Español de Chile (es-CL)
- **Femeninas**: Catalina
- **Masculinas**: Lorenzo

### Español de Perú (es-PE)
- **Femeninas**: Camila
- **Masculinas**: Alex

### Español de Venezuela (es-VE)
- **Femeninas**: Paola
- **Masculinas**: Sebastian

## 🔧 Configuración Avanzada

### Cambiar Puerto
```bash
# En .env
HOST_PORT=5005
```

### Cambiar Voz por Defecto
```bash
# En .env
DEFAULT_VOICE=Elvira
```

### Desactivar Debug
```bash
# En .env
DEBUG_AUDIO=false
```

## 📁 Estructura de Archivos

```
azure-tts/
├── app/
│   ├── app.py              # Servicio Flask
│   ├── requirements.txt    # Dependencias Python
│   └── Dockerfile         # Imagen Docker
├── audio_output/          # Audio generado (montado)
├── debug_audio/          # Audio de debug (montado)
├── docker-compose.yml    # Configuración Docker
├── .env.example          # Variables de entorno
├── setup_env.sh         # Script de configuración
└── README.md            # Este archivo
```

## 🔍 Logs y Debug

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ver logs del contenedor específico
docker logs azure-tts-service

# Acceder al contenedor
docker exec -it azure-tts-service bash
```
