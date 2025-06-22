#!/usr/bin/env python3
"""
Script oficial de prueba para Azure TTS Service
Prueba todas las funcionalidades del servicio de síntesis de voz de Azure
Versión: Azure Cognitive Services TTS
"""

import requests
import json
import time
import sys
import os
from datetime import datetime

# Configuración del servicio
SERVICE_URL = "http://localhost:5004"

def print_header(title):
    """Imprime un encabezado formateado"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_success(message):
    """Imprime mensaje de éxito"""
    print(f"✅ {message}")

def print_error(message):
    """Imprime mensaje de error"""
    print(f"❌ {message}")

def print_info(message):
    """Imprime mensaje informativo"""
    print(f"ℹ️  {message}")

def test_health_check():
    """Prueba el health check del servicio"""
    print_header("HEALTH CHECK")
    
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=10)
        response.raise_for_status()
        
        health_data = response.json()
        print_success("Servicio funcionando correctamente")
        print_info(f"Modelo: {health_data['model']}")
        print_info(f"Estado: {health_data['status']}")
        print_info(f"Región: {health_data['region']}")
        print_info(f"Azure disponible: {health_data['azure_available']}")
        print_info(f"Idioma por defecto: {health_data['default_language']}")
        print_info(f"Voz por defecto: {health_data['default_voice']}")
        
        return True
        
    except Exception as e:
        print_error(f"Error en health check: {e}")
        return False

def test_voices_list():
    """Prueba el listado de voces"""
    print_header("LISTADO DE VOCES")
    
    try:
        response = requests.get(f"{SERVICE_URL}/voices", timeout=10)
        response.raise_for_status()
        
        voices_data = response.json()
        print_success(f"Total de voces: {voices_data['total_voices']}")
        print_info(f"Modelo: {voices_data['model']}")
        print_info(f"Idioma por defecto: {voices_data['default_language']}")
        print_info(f"Voz por defecto: {voices_data['default_voice']}")
        
        voices_by_language = voices_data['voices_by_language']
        for language, voices in voices_by_language.items():
            female_count = len(voices.get('female', []))
            male_count = len(voices.get('male', []))
            default_voice = voices.get('default', 'N/A')
            
            print_info(f"{language}: {female_count + male_count} voces ({female_count}♀, {male_count}♂) - Default: {default_voice}")
            
            # Mostrar voces en español
            if language == 'es-ES':
                print_info(f"  Femeninas: {', '.join(voices.get('female', []))}")
                print_info(f"  Masculinas: {', '.join(voices.get('male', []))}")
        
        return True
        
    except Exception as e:
        print_error(f"Error obteniendo voces: {e}")
        return False

def test_spanish_voices():
    """Prueba las voces en español"""
    print_header("PRUEBA DE VOCES EN ESPAÑOL")
    
    spanish_voices = ['Abril', 'Elvira', 'Alvaro']
    test_text = "Hola, soy una voz sintetizada con Azure Cognitive Services Text-to-Speech."
    
    results = []
    
    for voice in spanish_voices:
        print_info(f"Probando voz: {voice}")
        
        try:
            start_time = time.time()
            
            payload = {
                "text": test_text,
                "language": "es-ES",
                "voice": voice,
                "speed": 1.0
            }
            
            response = requests.post(f"{SERVICE_URL}/synthesize_json", 
                                   json=payload, 
                                   timeout=30)
            response.raise_for_status()
            
            end_time = time.time()
            synthesis_time = end_time - start_time
            
            result = response.json()
            duration = result.get('audio_duration', 0)
            real_time_factor = synthesis_time / duration if duration > 0 else 0
            
            print_success(f"Voz {voice}: {duration:.2f}s audio, {synthesis_time:.2f}s síntesis (RTF: {real_time_factor:.2f}x)")
            results.append({
                'voice': voice,
                'success': True,
                'duration': duration,
                'synthesis_time': synthesis_time,
                'rtf': real_time_factor
            })
            
        except Exception as e:
            print_error(f"Error con voz {voice}: {e}")
            results.append({
                'voice': voice,
                'success': False,
                'error': str(e)
            })
    
    # Resumen
    successful = sum(1 for r in results if r['success'])
    print_info(f"Resultado: {successful}/{len(spanish_voices)} voces exitosas")
    
    if successful > 0:
        avg_rtf = sum(r['rtf'] for r in results if r['success']) / successful
        print_info(f"RTF promedio: {avg_rtf:.2f}x (menor es mejor)")
    
    return successful == len(spanish_voices)

def test_language_switching():
    """Prueba el cambio entre idiomas"""
    print_header("PRUEBA DE CAMBIO DE IDIOMAS")
    
    test_cases = [
        {"language": "es-ES", "text": "Hola, este es un mensaje en español de España", "voice": "Abril"},
        {"language": "es-MX", "text": "Hola, este es un mensaje en español de México", "voice": "Dalia"},
        {"language": "es-AR", "text": "Hola, este es un mensaje en español de Argentina", "voice": "Elena"},
        {"language": "es-CO", "text": "Hola, este es un mensaje en español de Colombia", "voice": "Gonzalo"}
    ]
    
    results = []
    
    for test_case in test_cases:
        lang = test_case['language']
        text = test_case['text']
        voice = test_case['voice']
        
        print_info(f"Probando idioma: {lang} con voz {voice}")
        
        try:
            payload = {
                "text": text,
                "language": lang,
                "voice": voice,
                "speed": 1.0
            }
            
            response = requests.post(f"{SERVICE_URL}/synthesize_json", 
                                   json=payload, 
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                duration = result.get('audio_duration', 0)
                print_success(f"Idioma {lang}: {duration:.2f}s audio generado")
                results.append(True)
            else:
                print_error(f"Error HTTP {response.status_code} con idioma {lang}")
                try:
                    error_data = response.json()
                    print_error(f"Detalles: {error_data.get('error', 'Sin detalles')}")
                except:
                    print_error(f"Respuesta: {response.text[:200]}")
                results.append(False)
            
        except requests.exceptions.RequestException as e:
            print_error(f"Error de conexión con idioma {lang}: {e}")
            results.append(False)
        except Exception as e:
            print_error(f"Error inesperado con idioma {lang}: {e}")
            results.append(False)
    
    successful = sum(results)
    print_info(f"Resultado: {successful}/{len(test_cases)} idiomas exitosos")
    
    return successful == len(test_cases)

def test_voice_recommendations():
    """Prueba las recomendaciones de voces por género"""
    print_header("PRUEBA DE RECOMENDACIONES DE VOCES")
    
    test_cases = [
        {"language": "es-ES", "gender_preference": "female", "expected_type": "female"},
        {"language": "es-ES", "gender_preference": "male", "expected_type": "male"},
        {"language": "es-MX", "gender_preference": "female", "expected_type": "female"},
        {"language": "es-MX", "gender_preference": "male", "expected_type": "male"}
    ]
    
    results = []
    
    for test_case in test_cases:
        lang = test_case['language']
        gender = test_case['gender_preference']
        
        print_info(f"Probando recomendación: {lang} {gender}")
        
        try:
            payload = {
                "text": "Prueba de recomendación de voz",
                "language": lang,
                "gender_preference": gender,
                "speed": 1.0
            }
            
            response = requests.post(f"{SERVICE_URL}/synthesize_json", 
                                   json=payload, 
                                   timeout=30)
            response.raise_for_status()
            
            result = response.json()
            voice_used = result.get('voice', '')
            
            print_success(f"Idioma {lang} {gender}: voz seleccionada {voice_used}")
            results.append(True)
            
        except Exception as e:
            print_error(f"Error con {lang} {gender}: {e}")
            results.append(False)
    
    successful = sum(results)
    print_info(f"Resultado: {successful}/{len(test_cases)} recomendaciones exitosas")
    
    return successful == len(test_cases)

def test_speed_variations():
    """Prueba diferentes velocidades de síntesis"""
    print_header("PRUEBA DE VARIACIONES DE VELOCIDAD")
    
    speeds = [0.5, 1.0, 1.5, 2.0]
    test_text = "Esta es una prueba de velocidad de síntesis de voz."
    
    results = []
    
    for speed in speeds:
        print_info(f"Probando velocidad: {speed}x")
        
        try:
            start_time = time.time()
            
            payload = {
                "text": test_text,
                "language": "es-ES",
                "voice": "Abril",
                "speed": speed
            }
            
            response = requests.post(f"{SERVICE_URL}/synthesize_json", 
                                   json=payload, 
                                   timeout=30)
            response.raise_for_status()
            
            end_time = time.time()
            synthesis_time = end_time - start_time
            
            result = response.json()
            duration = result.get('audio_duration', 0)
            actual_speed = result.get('speed', speed)
            
            print_success(f"Velocidad {speed}x: {duration:.2f}s audio, velocidad real: {actual_speed}")
            results.append(True)
            
        except Exception as e:
            print_error(f"Error con velocidad {speed}x: {e}")
            results.append(False)
    
    successful = sum(results)
    print_info(f"Resultado: {successful}/{len(speeds)} velocidades exitosas")
    
    return successful == len(speeds)

def test_debug_audio():
    """Prueba la funcionalidad de debug de audio"""
    print_header("PRUEBA DE DEBUG DE AUDIO")
    
    try:
        # Primero hacer una síntesis para generar audio de debug
        payload = {
            "text": "Prueba de audio de debug",
            "language": "es-ES",
            "voice": "Abril"
        }
        
        response = requests.post(f"{SERVICE_URL}/synthesize_json", 
                               json=payload, 
                               timeout=30)
        response.raise_for_status()
        
        result = response.json()
        debug_file = result.get('debug_audio_file')
        
        if debug_file:
            print_success(f"Archivo de debug generado: {debug_file}")
            
            # Listar archivos de debug
            debug_response = requests.get(f"{SERVICE_URL}/debug/audio", timeout=10)
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                print_info(f"Total archivos debug: {debug_data.get('total', 0)}")
                print_info(f"Debug habilitado: {debug_data.get('debug_enabled', False)}")
                
                if debug_data.get('debug_files'):
                    latest_file = debug_data['debug_files'][0]
                    print_info(f"Último archivo: {latest_file['filename']} ({latest_file['size']} bytes)")
            
            return True
        else:
            print_info("Debug de audio no está habilitado")
            return True
            
    except Exception as e:
        print_error(f"Error en debug de audio: {e}")
        return False

def test_voice_availability():
    """Prueba la disponibilidad de voces específicas problemáticas"""
    print_header("PRUEBA DE DISPONIBILIDAD DE VOCES")
    
    # Voces que podrían tener problemas
    problematic_voices = [
        {"language": "es-CO", "voice": "Gonzalo", "name": "Gonzalo (Colombia)"},
        {"language": "es-MX", "voice": "Dalia", "name": "Dalia (México)"},
        {"language": "es-AR", "voice": "Elena", "name": "Elena (Argentina)"},
        {"language": "es-CL", "voice": "Catalina", "name": "Catalina (Chile)"}
    ]
    
    results = []
    
    for voice_test in problematic_voices:
        lang = voice_test['language']
        voice = voice_test['voice']
        name = voice_test['name']
        
        print_info(f"Probando disponibilidad: {name}")
        
        try:
            payload = {
                "text": f"Prueba de disponibilidad para {name}",
                "language": lang,
                "voice": voice,
                "speed": 1.0
            }
            
            response = requests.post(f"{SERVICE_URL}/synthesize_json", 
                                   json=payload, 
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                duration = result.get('audio_duration', 0)
                print_success(f"{name}: ✅ Disponible ({duration:.2f}s)")
                results.append(True)
            else:
                print_error(f"{name}: ❌ Error {response.status_code}")
                try:
                    error_data = response.json()
                    print_error(f"  Detalles: {error_data.get('error', 'Sin detalles')}")
                except:
                    print_error(f"  Respuesta: {response.text[:100]}")
                results.append(False)
                
        except Exception as e:
            print_error(f"{name}: ❌ Error: {e}")
            results.append(False)
    
    successful = sum(results)
    print_info(f"Resultado: {successful}/{len(problematic_voices)} voces disponibles")
    
    return successful == len(problematic_voices)

def run_all_tests():
    """Ejecuta todas las pruebas"""
    print_header("AZURE TTS SERVICE - SUITE DE PRUEBAS")
    print_info(f"Iniciando pruebas en {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Listado de Voces", test_voices_list),
        ("Disponibilidad de Voces", test_voice_availability),
        ("Voces en Español", test_spanish_voices),
        ("Cambio de Idiomas", test_language_switching),
        ("Recomendaciones de Voces", test_voice_recommendations),
        ("Variaciones de Velocidad", test_speed_variations),
        ("Debug de Audio", test_debug_audio)
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        print_info(f"Ejecutando: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Error inesperado en {test_name}: {e}")
            results.append((test_name, False))
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Resumen final
    print_header("RESUMEN DE RESULTADOS")
    
    passed = 0
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASÓ")
            passed += 1
        else:
            print_error(f"{test_name}: FALLÓ")
    
    print_info(f"Pruebas completadas en {total_time:.2f} segundos")
    print_info(f"Resultado final: {passed}/{len(tests)} pruebas exitosas")
    
    if passed == len(tests):
        print_success("¡TODAS LAS PRUEBAS PASARON! 🎉")
        print_info("Azure TTS Service está funcionando perfectamente")
        return True
    else:
        print_error(f"Falló {len(tests) - passed} prueba(s)")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 