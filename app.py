import google.generativeai as genai
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
        st.info("Buscando modelo disponible y generando contenido...")
        try:
            genai.configure(api_key=gemini_api_key)

            # Autodetectar modelo activo disponible en la cuenta
            modelo_disponible = None
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    if "flash" in m.name or "pro" in m.name:
                        modelo_disponible = m.name
                        break

            if not modelo_disponible:
                for m in genai.list_models():
                    if "generateContent" in m.supported_generation_methods:
                        modelo_disponible = m.name
                        break

            if not modelo_disponible:
                st.error(
                    "No se encontró ningún modelo de texto disponible en esta"
                    " API Key."
                )
            else:
                model = genai.GenerativeModel(modelo_disponible)

                prompt_completo = (
                    "Eres un experto creador de contenido para Shorts de"
                    " YouTube y TikTok. Crea un guion estructurado de 30 a 50"
                    " segundos con un gancho inicial impactante, 3 puntos o"
                    " datos principales y una llamada a la acción para"
                    " suscribirse sobre el siguiente tema: "
                    f"{prompt_usuario}"
                )

                response = model.generate_content(prompt_completo)

                st.success("¡Guion listo!")
                st.markdown(response.text)
        except Exception as e:
            st.error(f"Ocurrió un error al conectar con Gemini: {e}")
            
