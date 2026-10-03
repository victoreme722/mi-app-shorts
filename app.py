import asyncio
import os
import edge_tts
import google.generativeai as genai
from gtts import gTTS
import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

# Importaciones para MoviePy
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ColorClip, ImageClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip

st.set_page_config(
    page_title="Creador de Shorts de Comiquitas", page_icon="🧸", layout="centered"
)

st.title("🧸 Generador de Shorts Animados (Comiquitas)")
st.write(
    "Crea videos cortos estilo comiquita con voz infantil y subtítulos"
    " divertidos."
)

gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")

# Selector de Voces Infantiles
opcion_voz = st.selectbox(
    "🎙️ Elige la voz infantil:",
    options=[
        "👧 Niña Dalia (México - Voz Infantil/Alegre)",
        "👦 Niño Jorge (México - Voz Animada)",
        "👧 Niña Salomé (Colombia - Voz Infantil)",
        "👦 Niño Alonso (EE.UU. Latino - Voz Infantil)",
    ],
)

if "Dalia" in opcion_voz:
    voz_id = "es-MX-DaliaNeural"
elif "Jorge" in opcion_voz:
    voz_id = "es-MX-JorgeNeural"
elif "Alonso" in opcion_voz:
    voz_id = "es-US-AlonsoNeural"
else:
    voz_id = "es-CO-SalomeNeural"

prompt_usuario = st.text_input(
    "¿De qué quieres que trate el video de comiquita?",
    placeholder="Ej: Curiosidades de los dinosaurios, animales de la selva...",
)


# Función para generar la voz infantil con sistema de respaldo automático
async def generar_voz_segura(texto, voz_principal, archivo_salida):
    voces_prueba = [
        voz_principal,
        "es-MX-DaliaNeural",
        "es-MX-JorgeNeural",
        "es-ES-AlvaroNeural",
    ]

    for voz in voces_prueba:
        try:
            communicate = edge_tts.Communicate(texto, voz)
            await communicate.save(archivo_salida)
            if (
                os.path.exists(archivo_salida)
                and os.path.getsize(archivo_salida) > 0
            ):
                return
        except Exception:
            continue

    # Respaldo secundario con gTTS si los servidores de Edge están inaccesibles
    tts = gTTS(text=texto, lang="es", slow=False)
    tts.save(archivo_salida)


# Función para descargar e integrar video animado real
def obtener_video_comiquita(duracion_objetivo):
    url_video = "https://assets.mixkit.co/videos/preview/mixkit-cartoon-character-in-a-jungle-41555-large.mp4"
    archivo_fondo = "video_comiquita.mp4"

    if not os.path.exists(archivo_fondo):
        resp = requests.get(url_video, stream=True)
        with open(archivo_fondo, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    try:
        clip_fondo = VideoFileClip(archivo_fondo)

        if clip_fondo.duration < duracion_objetivo:
            clip_fondo = clip_fondo.loop(duration=duracion_objetivo)
        else:
            clip_fondo = clip_fondo.subclip(0, duracion_objetivo)

        clip_fondo = clip_fondo.resize(height=1920)
        if clip_fondo.w > 1080:
            clip_fondo = clip_fondo.crop(
                x_center=clip_fondo.w / 2, width=1080, height=1920
            )
        return clip_fondo
    except Exception:
        return ColorClip(
            size=(1080, 1920), color=(255, 182, 193), duration=duracion_objetivo
        )


# Función para generar subtítulos estilo comiquita
def crear_subtitulos_img(
    texto, ancho=1080, alto=1920, color_fondo=(0, 0, 0, 175)
):
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 54)
    except:
        font = ImageFont.load_default()

    palabras = texto.split()
    lineas = []
    linea_actual = []
    for p in palabras:
        linea_actual.append(p)
        if len(" ".join(linea_actual)) > 19:
            lineas.append(" ".join(linea_actual[:-1]))
            linea_actual = [p]
    if linea_actual:
        lineas.append(" ".join(linea_actual))

    texto_formateado = "\n".join(lineas)

    y_centro = int(alto * 0.70)
    bbox = draw.multiline_textbbox(
        (ancho // 2, y_centro),
        texto_formateado,
        font=font,
        anchor="mm",
        align="center",
    )
    padding = 30
    caja = [
        bbox[0] - padding,
        bbox[1] - padding,
        bbox[2] + padding,
        bbox[3] + padding,
    ]

    draw.rounded_rectangle(caja, radius=22, fill=color_fondo)
    draw.multiline_text(
        (ancho // 2, y_centro),
        texto_formateado,
        font=font,
        fill=(255, 235, 59, 255),
        anchor="mm",
        align="center",
    )

    img_path = "subtitulos_overlay.png"
    img.save(img_path)
    return img_path


if st.button("✨ Generar Short de Comiquita"):
    if not prompt_usuario:
        st.warning("Por favor ingresa un tema primero.")
    elif not gemini_api_key:
        st.error("No se ha configurado GEMINI_API_KEY en los Secrets.")
    else:
        # 1. Guion infantil corto
        with st.spinner("1/3 Redactando historia infantil con Gemini..."):
            try:
                genai.configure(api_key=gemini_api_key)
                modelos = [
                    m.name
                    for m in genai.list_models()
                    if "generateContent" in m.supported_generation_methods
                ]
                modelos.sort(
                    key=lambda name: (
                        0 if "flash" in name else (1 if "pro" in name else 2)
                    )
                )

                guion_texto = ""
                for mod in modelos:
                    try:
                        m = genai.GenerativeModel(mod)
                        prompt = (
                            "Escribe la locución para un video animado infantil"
                            " sobre:"
                            f" {prompt_usuario}. Debe ser muy alegre,"
                            " divertido y fácil de entender para niños."
                            " Empieza con un saludo como '¡Hola amiguitos!' y"
                            " comparte 2 datos sorprendentes. Máximo 35"
                            " palabras. Sin acotaciones de escena."
                        )
                        res = m.generate_content(prompt)
                        if res and res.text:
                            guion_texto = res.text.strip()
                            break
                    except:
                        continue

                if not guion_texto:
                    st.error("No se pudo obtener el guion.")
                    st.stop()

                st.success("¡Guion listo!")
                st.write(f"**Locución:** *\"{guion_texto}\"*")

            except Exception as e:
                st.error(f"Error con Gemini: {e}")
                st.stop()

        # 2. Voz infantil con respaldo
        with st.spinner("2/3 Generando la voz infantil..."):
            audio_file = "locucion_infantil.mp3"
            asyncio.run(generar_voz_segura(guion_texto, voz_id, audio_file))

        # 3. Ensamblar Video Animado
        with st.spinner(
            "3/3 Descargando animación y renderizando el video final..."
        ):
            try:
                audio_clip = AudioFileClip(audio_file)
                duracion = audio_clip.duration

                fondo_animado = obtener_video_comiquita(duracion)

                img_sub = crear_subtitulos_img(
                    guion_texto, ancho=1080, alto=1920
                )
                txt_clip = ImageClip(img_sub).set_duration(duracion)

                video_final = CompositeVideoClip([fondo_animado, txt_clip])
                video_final = video_final.set_audio(audio_clip)

                output_video = "short_comiquita.mp4"
                video_final.write_videofile(
                    output_video,
                    fps=24,
                    codec="libx264",
                    audio_codec="aac",
                    logger=None,
                )

                audio_clip.close()
                fondo_animado.close()
                video_final.close()

                st.success("🎉 ¡Tu Video de Comiquita está listo!")

                st.video(output_video)

                with open(output_video, "rb") as file:
                    st.download_button(
                        label="⬇️ Descargar Video de Comiquita (.mp4)",
                        data=file,
                        file_name="short_comiquita_infantil.mp4",
                        mime="video/mp4",
                    )

            except Exception as e:
                st.error(f"Error al renderizar el video: {e}")
                
