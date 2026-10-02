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
        st.info("Buscando modelo activo en tu cuenta de Gemini...")
        try:
            genai.configure(api_key=gemini_api_key)

            # Consultar en tiempo real los modelos disponibles para tu API Key
            modelos_disponibles = [
                m.name
                for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods
            ]

            if not modelos_disponibles:
                st.error(
                    "No se encontraron modelos de generación disponibles para"
                    " esta API Key. Revisa tu clave en Google AI Studio."
                )
            else:
                # Priorizar modelos tipo 'flash' o 'pro'
                modelos_disponibles.sort(
                    key=lambda name: (
                        0 if "flash" in name else (1 if "pro" in name else 2)
                    )
                )

                exito = False
                error_ultimo = ""

                for nombre_modelo in modelos_disponibles:
                    try:
                        model = genai.GenerativeModel(nombre_modelo)
                        prompt_completo = (
                            "Eres un experto creador de contenido para Shorts de"
                            " YouTube y TikTok. Crea un guion estructurado de 30"
                            " a 50 segundos con un gancho inicial impactante, 3"
                            " puntos o datos principales y una llamada a la"
                            " acción para suscribirse sobre el siguiente tema: "
                            f"{prompt_usuario}"
                        )
                        response = model.generate_content(prompt_completo)
                        if response and response.text:
                            st.success("¡Guion listo!")
                            st.markdown(response.text)
                            exito = True
                            break
                    except Exception as err:
                        error_ultimo = str(err)
                        continue

                if not exito:
                    st.error(
                        "No se pudo generar respuesta con los modelos"
                        f" disponibles. Detalle: {error_ultimo}"
                    )

        except Exception as err:
            st.error(
                "Error de conexión con la API de Gemini. Revisa que tu"
                f" GEMINI_API_KEY sea correcta. Detalle: {err}"
            )
            
