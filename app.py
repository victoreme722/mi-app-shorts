import streamlit as st
from google import genai

st.set_page_config(page_title="Creador de Shorts IA", page_icon="🎬")

st.title("🎬 Generador de Guiones con Gemini")
st.write("Escribe una idea y genera la estructura para tu video corto de forma gratuita.")

# Obtener clave de API desde los secretos de Streamlit
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")

prompt_usuario = st.text_input("¿De qué quieres que trate el Short?")

if st.button("✨ Generar Guion"):
    if not prompt_usuario:
        st.warning("Por favor ingresa un tema primero.")
    elif not gemini_api_key:
        st.error("No se ha configurado la GEMINI_API_KEY en los Secrets.")
    else:
        st.info("Generando contenido con Google Gemini...")
        try:
            client = genai.Client(api_key=gemini_api_key)
            
            prompt_completo = f"""
            Eres un experto creador de contenido para YouTube Shorts.
            Crea un guion detallado y estructurado de 30 segundos sobre: {prompt_usuario}
            
            Incluye:
            1. Gancho inicial (primeros 3 segundos).
            2. Desarrollo visual y locución (puntos clave).
            3. Llamado a la acción final (CTA).
            """
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_completo,
            )
            
            st.success("¡Guion listo!")
            st.markdown(response.text)
        except Exception as e:
            st.error(f"Error al conectar con Gemini: {e}")
```
