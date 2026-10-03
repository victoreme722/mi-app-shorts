import asyncio
import os
import edge_tts
import google.generativeai as genai
from gtts import gTTS
import PIL.Image
import requests
import streamlit as st

# PARCHE DE COMPATIBILIDAD PARA MOVIEPY Y PILLOW RECIENTE
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = getattr(
        PIL.Image, "LANCZOS", getattr(PIL.Image, "BICUBIC", None)
    )

from PIL import ImageDraw, ImageFont

# Importaciones de MoviePy
try:
    from moviepy.editor import (
        AudioFileClip,
        ColorClip,
        CompositeVideoClip,
        ImageClip,
        VideoFileClip,
    )
    import moviepy.video.fx.all as vfx
except Exception:
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.video.VideoClip import ColorClip, ImageClip
    import moviepy.video.fx.all as vfx

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


# Procesamiento seguro y compatible de video
def obtener_video_animado_optimizado(duracion_objetivo):
    extensiones = (".mp4", ".mov", ".avi", ".webm")
    video_local = None

    for f in os.listdir("."):
        if f.lower().endswith(extensiones) and not f.startswith(
            ("short_", "animacion_")
        ):
            video_local = f
            break

    if video_local:
        try:
            clip_fondo = VideoFileClip(video_local)

            # 1. Ajustar duración (Loop o Subclip)
            if clip_fondo.duration > duracion_objetivo:
                clip_fondo = clip_fondo.subclip(0, duracion_objetivo)
            else:
                try:
                    clip_fondo = clip_fondo.loop(duration=duracion_objetivo)
                except Exception:
                    clip_fondo = vfx.loop(clip_fondo, duration=duracion_objetivo)

            # 2. Redimensionar alto a 1920px
            try:
                clip_fondo = clip_fondo.resize(height=1920)
            except Exception:
                clip_fondo = vfx.resize(clip_fondo, height=1920)

            # 3. Recortar ancho a 1080px si es más ancho
            if clip_fondo.w > 1080:
                try:
                    clip_fondo = clip_fondo.crop(
                        x_center=clip_fondo.w / 2, width=1080, height=1920
                    )
                except Exception:
                    clip_fondo = vfx.crop(
                        clip_fondo,
                        x_center=clip_fondo.w / 2,
                        width=1080,
                        height=1920,
                    )

            return (
                clip_fondo,
                f"Video local procesado con éxito ('{video_local}')",
            )
        except Exception as e:
            st.warning(f"Error procesando {video_local}: {e}")

    # Respaldo de seguridad
    return (
        ColorClip(
            size=(1080, 1920), color=(25, 35, 60), duration=duracion_objetivo
        ),
        "Fondo plano de emergencia",
    )


# Generador de capas de subtítulos estilo infantil
def crear_subtitulos_img(
    texto, ancho=1080, alto=1920, color_fondo=(0, 0, 0, 180)
):
    img = PIL.Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 54)
    except Exception:
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
                    except Exception:
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

                # Obtener animación
                fondo_animado, fuente_usada = obtener_video_animado_optimizado(
                    duracion
                )
                st.info(f"ℹ️ {fuente_usada}")

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
                
