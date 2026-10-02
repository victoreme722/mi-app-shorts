import os
import google.generativeai as genai
from gtts import gTTS
from moviepy.editor import AudioFileClip, ColorClip, TextClip, CompositeVideoClip
import streamlit as st

st.set_page_config(
    page_title="Creador de Shorts en Video", page_icon="🎬", layout="centered"
)

st.title("🎬 Generador de Shorts en Video")
st.write("Escribe tu idea para generar un guion y compilar el video con voz.")

# Obtener API Key
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")

prompt_usuario = st.text_input("¿De qué quieres que trate el Short?")

if st.button("✨ Generar Video Completo"):
    if not prompt_usuario:
        st.warning("Por favor ingresa un tema primero.")
    elif not gemini_api_key:
        st.error("No se ha configurado GEMINI_API_KEY en los Secrets.")
    else:
        with st.spinner("1/3 Generando guion con Gemini..."):
            try:
                genai.configure(api_key=gemini_api_key)

                # Obtener modelos disponibles
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
                            "Escribe un texto corto para la locución de un"
                            " video Short de TikTok/YouTube sobre:"
                            f" {prompt_usuario}. Debe ser directo, sin"
                            " acotaciones de escena, solo el texto que se va a"
                            " hablar. Máximo 40 palabras."
                        )
                        res = m.generate_content(prompt)
                        if res and res.text:
                            guion_texto = res.text.strip()
                            break
                    except:
                        continue

                if not guion_texto:
                    st.error("No se pudo obtener el guion de Gemini.")
                    st.stop()

                st.success("¡Guion generado!")
                st.write(f"**Locución:** *\"{guion_texto}\"*")

            except Exception as e:
                st.error(f"Error con Gemini: {e}")
                st.stop()

        # 2. Generar Audio (Voz)
        with st.spinner("2/3 Generando audio de locución (Voz)..."):
            audio_file = "locucion.mp3"
            tts = gTTS(text=guion_texto, lang="es", slow=False)
            tts.save(audio_file)

        # 3. Crear el Video MP4
        with st.spinner("3/3 Renderizando el video final MP4..."):
            try:
                audio_clip = AudioFileClip(audio_file)
                duracion = audio_clip.duration

                # Fondo azul vertical (1080x1920 para formato Short / Reels)
                fondo = ColorClip(
                    size=(1080, 1920), color=(20, 30, 60), duration=duracion
                )

                # Unir audio con fondo
                video_final = fondo.set_audio(audio_clip)

                output_video = "short_generado.mp4"
                video_final.write_videofile(
                    output_video,
                    fps=24,
                    codec="libx264",
                    audio_codec="aac",
                    logger=None,
                )

                # Liberar memoria
                audio_clip.close()
                video_final.close()

                st.success("🎉 ¡Video generado con éxito!")

                # Mostrar reproductor de video en Streamlit
                st.video(output_video)

                # Botón para descargar el archivo .mp4
                with open(output_video, "rb") as file:
                    st.download_button(
                        label="⬇️ Descargar Video (.mp4)",
                        data=file,
                        file_name="mi_short.mp4",
                        mime="video/mp4",
                    )

            except Exception as e:
                st.error(f"Error al renderizar el video: {e}")
                
