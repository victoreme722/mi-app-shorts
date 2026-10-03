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


# Generación de voz con respaldo
async def generar_voz_segura(texto, voz_principal, archivo_salida):
    voces = [voz_principal, "es-MX-DaliaNeural", "es-MX-JorgeNeural"]
    for v in voces:
        try:
            communicate = edge_tts.Communicate(texto, v)
            await communicate.save(archivo_salida)
            if (
                os.path.exists(archivo_salida)
                and os.path.getsize(archivo_salida) > 0
            ):
                return
        except Exception:
            continue
    tts = gTTS(text=texto, lang="es", slow=False)
    tts.save(archivo_salida)


# Función con URL directa sin bloqueo de IP
def obtener_video_animado_real(duracion_objetivo):
    archivo_local = "fondo.mp4"

    # 1. Si subiste fondo.mp4 a GitHub, se usará localmente
    if os.path.exists(archivo_local) and os.path.getsize(archivo_local) > 1000:
        try:
            clip_fondo = VideoFileClip(archivo_local)
            if clip_fondo.duration < duracion_objetivo:
                clip_fondo = clip_fondo.loop(duration=duracion_objetivo)
            else:
                clip_fondo = clip_fondo.subclip(0, duracion_objetivo)

            clip_fondo = clip_fondo.resize(height=1920)
            if clip_fondo.w > 1080:
                clip_fondo = clip_fondo.crop(
                    x_center=clip_fondo.w / 2, width=1080, height=1920
                )
            return clip_fondo, "Video Local de GitHub (fondo.mp4)"
        except Exception as e:
            pass

    # 2. Enlace público CDN de muestra animada que no bloquea Streamlit Cloud
    urls_animacion = [
        "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/free-space-detection.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
    ]

    archivo_temp = "animacion_descargada.mp4"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
    }

    for url in urls_animacion:
        try:
            resp = requests.get(url, headers=headers, stream=True, timeout=15)
            if resp.status_code == 200:
                with open(archivo_temp, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)

                if (
                    os.path.exists(archivo_temp)
                    and os.path.getsize(archivo_temp) > 10000
                ):
                    clip_fondo = VideoFileClip(archivo_temp)
                    if clip_fondo.duration < duracion_objetivo:
                        clip_fondo = clip_fondo.loop(duration=duracion_objetivo)
                    else:
                        clip_fondo = clip_fondo.subclip(0, duracion_objetivo)

                    clip_fondo = clip_fondo.resize(height=1920)
                    if clip_fondo.w > 1080:
                        clip_fondo = clip_fondo.crop(
                            x_center=clip_fondo.w / 2, width=1080, height=1920
                        )
                    return clip_fondo, f"Video descargado de CDN ({url})"
        except Exception:
            continue

    # 3. Respaldo
    return (
        ColorClip(
            size=(1080, 1920), color=(25, 35, 60), duration=duracion_objetivo
        ),
        "Fondo Plano (Falló descarga)",
    )


# Generador de capas de subtítulos estilo infantil
def crear_subtitulos_img(
    texto, ancho=1080, alto=1920, color_fondo=(0, 0, 0, 180)
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
        if len(" ".join(linea_actual)) > 18:
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
        # 1. Guion infantil
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

        # 2. Voz infantil
        with st.spinner("2/3 Generando la voz infantil..."):
            audio_file = "locucion_infantil.mp3"
            asyncio.run(generar_voz_segura(guion_texto, voz_id, audio_file))

        # 3. Ensamblar Video Animado
        with st.spinner("3/3 Procesando video final..."):
            try:
                audio_clip = AudioFileClip(audio_file)
                duracion = audio_clip.duration

                # Obtener animación real y estado
                fondo_animado, fuente_usada = obtener_video_animado_real(
                    duracion
                )
                st.caption(f"ℹ️ Fuente de fondo utilizada: {fuente_usada}")

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
                
