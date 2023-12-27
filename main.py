#Importar las bibliotecas necesarias
from openai import OpenAI
from dotenv import load_dotenv
import os
import uuid 
from openai import OpenAI
from fastapi.templating import Jinja2Templates
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import PlainTextResponse

#Cargar las variables de entorno desde el archivo .env
load_dotenv()

#Configurar la clave de la API de OpenAI
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


# Crear la aplicación FastAPI
app = FastAPI()


# Habilitar CORS para todos los orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar el directorio estático para archivos CSS y otros recursos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")


# Configurar las plantillas Jinja2
templates = Jinja2Templates(directory="templates")


# Función para transcribir un archivo de audio
def transcribe_audio(file_path):
    audio_file_path = file_path
    

    # Abrir el archivo de audio en modo binario
    with open(audio_file_path, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )

    # Imprimir la transcripción para fines de depuración
    print(transcript) 

    # Devolver la transcripción obtenida
    return transcript


# Ruta principal que renderiza la página inicial
@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "transcription": None})



# Ruta para manejar la transcripción de archivos de audio
@app.post("/transcribe")
async def transcribe_endpoint(request: Request, file: UploadFile = File(...)):
    try:
        # Generar nombres de archivo únicos
        unique_audio_filename = f"uploaded_audio_{uuid.uuid4()}.mp3"
        unique_transcription_filename = f"transcription_{uuid.uuid4()}.txt"

        # Guardar el archivo subido con el nombre de archivo de audio único
        with open(unique_audio_filename, 'wb') as audio_file:
            audio_file.write(file.file.read())

        # Realizar la transcripción del audio
        transcription = transcribe_audio(unique_audio_filename)

        # Guardar la transcripción en un archivo de texto con el nombre de archivo de transcripción único
        with open(unique_transcription_filename, 'w') as txt_file:
            txt_file.write(transcription)
        
        # Renderizar la plantilla con la transcripción y la ruta del archivo de transcripción
        return templates.TemplateResponse("index.html", {"request": request, "transcription": transcription, "transcription_file_path": unique_transcription_filename})

    except Exception as e:
        # Manejar errores y devolver una respuesta de error HTTP
        raise HTTPException(status_code=500, detail=str(e))
    


# Ruta para manejar la generación de respuestas basadas en la transcripción
@app.post("/generate-response")
async def generate_response(request: Request, transcription: str = Form(...)):
    try:
        # Paso adicional: Utilizar la API de OpenAI para generar una respuesta
        # Utilizar la API de OpenAI para generar una respuesta utilizando el modelo de Chat
        system_message = "You are a helpful assistant that is good at generating response to messages."
        user_message = f"The audio transcription is: {transcription}"

        messages = [{'role': 'system', 'content': system_message}, {'role': 'user', 'content': user_message}]

        generated_response = client.chat.completions.create(
             model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100,

        )

         # Extraer la respuesta generada del resultado de la API de OpenAI
        response_text = generated_response.choices[0].message.content

        # Guardar la respuesta en un archivo de texto
        response_filename = f"response_{uuid.uuid4()}.txt"
        with open(response_filename, 'w') as response_file:
            response_file.write(response_text)

        # Leer el contenido del archivo de respuesta
        with open(response_filename, 'r') as response_file:
            response_content = response_file.read()

        # Renderizar la plantilla con la transcripción y el contenido de la respuesta generada
        return templates.TemplateResponse("index.html", {"request": request, "transcription": transcription, "response_content": response_content})

    except Exception as e:
        # Manejar errores y devolver una respuesta de error HTTP
        raise HTTPException(status_code=500, detail=str(e))






# Iniciar la aplicación FastAPI utilizando el servidor Uvicorn
if __name__ == "__main__":
    import uvicorn
    # Ejecutar la aplicación en el host 127.0.0.1 y el puerto 8000
    uvicorn.run(app, host="127.0.0.1", port=8000)