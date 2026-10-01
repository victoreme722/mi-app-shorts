import os
from google import genai
import streamlit as st

st.set_page_config(page_title="Creador de Shorts", page_icon="🎬")

st.title("🎬 Generador de Guiones para Shorts")
st.write("Escribe una idea y genera la estructura para tu video corto.")

# Obtener clave desde los Secrets de Streamlit
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")

prompt_usuario = st.text_input("¿De qué quieres que trate el Short?")

if st.button("✨ Generar Guion"):
    if not prompt_usuario:
        st.warning("Por favor ingresa un tema primero.")
    elif not gemini_api_key:
        st.error("No se ha configurado la clave GEMINI_API_KEY en los Secrets.")
    else:
        st.info("Generando contenido con Gemini...")
        try:
            client = genai.Client(api_key=gemini_api_key)
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=(
                    "Eres un experto creador de contenido para Shorts de YouTube y TikTok. "
                    "Crea un guion estructurado de 30 a 50 segundos con gancho inicial, "
                    "3 puntos principales y llamada a la acción sobre el siguiente tema: "
                    f"{prompt_usuario}"
                ),
            )
            st.success("¡Guion listo!")
            st.markdown(response.text)
        except Exception as e:
            st.error(f"Ocurrió un error al conectar con Gemini: {e}")
            
