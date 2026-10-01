import openai
import streamlit as st

st.set_page_config(page_title="Creador de Shorts", page_icon="🎬")

st.title("🎬 Generador de Guiones para Shorts")
st.write("Escribe una idea y genera la estructura para tu video corto.")

# Obtener clave de API desde los secretos de Streamlit
openai_api_key = st.secrets.get("OPENAI_API_KEY", "")

prompt_usuario = st.text_input("¿De qué quieres que trate el Short?")

if st.button("✨ Generar Guion"):
    if not prompt_usuario:
        st.warning("Por favor ingresa un tema primero.")
    elif not openai_api_key:
        st.error("No se ha configurado la API Key de OpenAI.")
    else:
        st.info("Generando contenido...")
        client = openai.OpenAI(api_key=openai_api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto creador de contenido para Shorts de YouTube.",
                },
                {
                    "role": "user",
                    "content": f"Crea un guion estructurado de 30 segundos sobre: {prompt_usuario}",
                },
            ],
        )

        guion = response.choices[0].message.content
        st.success("¡Guion listo!")
        st.markdown(guion)
      
