import json
import os
import sqlite3
import sys
import streamlit as st
import time
from io import BytesIO
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
from pathlib import Path

# Añadir el directorio raíz del proyecto al sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))
from database.sqlite.database import (  # noqa: E402
    initdb,
    insert_chat,
    update_chat_name,
    save_chat_history,
    get_all_chat,
    get_chat_history_by_chat_id,
)


client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
model_fine_tuned = 'ft:gpt-3.5-turbo-0125:personal::9ioWFa4G'
chroma_path = "./database/chroma"
LLM = ChatOpenAI(
    model=model_fine_tuned,
    temperature=0.7,
)


def main():
    initdb()
    st.title("Sevilla Chatbot 💃")
    st.session_state.user_question = ""
    rag_chain = create_rag_chain()

    if "audio2text" not in st.session_state:
        st.session_state.audio2text = ''

    if "chat_history_st" not in st.session_state:
        st.session_state.chat_history_st = []
        st.session_state.chat_history_llm = []

    if "chat_id" not in st.session_state:
        st.session_state.chat_id = None

    handle_sidebar()

    if st.session_state.chat_id:
        # Display chat messages from history on app rerun
        for message in st.session_state.chat_history_st:
            display_message(
                role=message["role"],
                avatar=message["avatar"],
                content=message["content"],
            )

        # User question by chat input or audio
        chat_input = st.chat_input(placeholder="Hazme una pregunta")
        st.session_state.user_question = chat_input or st.session_state.audio2text

        if st.session_state.user_question:
            st.session_state.chat_history_st.append({
                "role": "user",
                "avatar": "👦",
                "content": st.session_state.user_question,
            })
            with st.chat_message(name="user", avatar="👦"):
                st.markdown(st.session_state.user_question)

            # Response from LLM
            with st.chat_message("assistant", avatar="💃"):
                # response = rag_chain.invoke({
                #     "input": st.session_state.user_question,
                #     "chat_history": st.session_state.chat_history_llm,
                # })
                # andalusian_response = adjust_to_andalusian(response["answer"])
                andalusian_response = "Mi respuesta andaluza 🎉"

                # Append user question and LLM response to chat history
                st.session_state.chat_history_llm.extend([
                    HumanMessage(content=st.session_state.user_question),
                    AIMessage(content=andalusian_response),
                ])
                st.write_stream(stream_response(andalusian_response))

                st.session_state.chat_history_st.append({
                    "role": "assistant",
                    "avatar": "💃",
                    "content": andalusian_response,
                })

                update_chat_name(
                    chat_id=st.session_state.chat_id,
                    chat_name=f"{st.session_state.user_question[:30]}...",
                )
                save_chat_history(
                    user_question=st.session_state.user_question,
                    llm_response=andalusian_response,
                    chat_id=st.session_state.chat_id,
                )
                st.session_state.user_question = ""
    else:
        st.write("A ver chiquill@, crea un chat nuevo o le das a uno que ya tengas...")


def handle_sidebar():
    with st.sidebar:
        audio_recorder = mic_recorder(
            start_prompt="🎙️",
            stop_prompt="🛑",
            just_once=False,
            use_container_width=False,
            callback=None,
            args=(),
            kwargs={},
            key="recorder",
        )
        if audio_recorder:
            # audio_bio = BytesIO(audio_recorder['bytes'])
            # audio_bio.name = 'audio.mp3'
            # transcription = client.audio.transcriptions.create(
            #     model="whisper-1",
            #     file=audio_bio,
            #     response_format="text"
            # )
            st.session_state.audio2text = "transcription"

        if st.button("Crear un nuevo chat"):
            st.session_state.chat_history_st = []
            st.session_state.chat_history_llm = []
            st.session_state.audio2text = ""
            st.session_state.user_question = ""
            st.session_state.chat_id = insert_chat()

    for chat in get_all_chat():
        if st.sidebar.button(chat[1], key=chat[0]):
            st.session_state.chat_id = chat[0]
            load_chat_history(chat[0])


def load_chat_history(chat_id):
    chat_history = get_chat_history_by_chat_id(chat_id)
    st.session_state.chat_history_st = []
    for message in chat_history:
        user_question = message[1]
        st.session_state.chat_history_st.append({
            "role": "user",
            "content": user_question,
            "avatar": "👦",
        })

        llm_response = message[2]
        st.session_state.chat_history_st.append({
            "role": "assitant",
            "content": llm_response,
            "avatar": "💃",
        })

        st.session_state.chat_history_llm.extend([
            HumanMessage(content=user_question),
            AIMessage(content=llm_response),
        ])


def display_message(role, avatar, content):
    with st.chat_message(name=role, avatar=avatar):
        st.markdown(content)


def create_chat_history():
    contextualize_question_system_prompt = """
        Dado un historial de chat y la última pregunta del usuario
        que podría hacer referencia al contexto en el historial del chat,
        formula una pregunta independiente que se pueda entender
        sin la historia del chat. NO respondas a la pregunta,
        solo reformúlala si es necesario, de lo contrario devuélvela tal cual.
    """
    db = Chroma(
        persist_directory=chroma_path,
        embedding_function=OpenAIEmbeddings()
    )
    retriever = db.as_retriever()

    contextualize_question_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_question_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    history_aware_retriever = create_history_aware_retriever(
        LLM,
        retriever,
        contextualize_question_prompt,
    )
    return history_aware_retriever


def create_rag_chain():
    system_prompt = """
        ###INSTRUCCIONES:
        Eres Martita una asistente de IA andaluza, por lo que siempre utilizas expresiones, frases y palabras típicas
        de Andalucía. Tu función es responder preguntas de manera util y eficiente sobre Sevilla,
        utilizando palabras Andaluzas, para ayudar a los turistas a encontrar información relevante sobre actividades,
        ocios, gastronomía y planificación de viajes en documentos dedicados a la ciudad de Sevilla.

        En tu respuesta, TEN EN CUENTA SIEMPRE:
        (1) Lee muy bien la pregunta y el contexto y comprende ambos antes de responder.
        (2) Comienza la respuesta en un tono amigable con el ánimo que caracteriza a los Andaluces.
        (3) Debajo de tu respuesta, enumera todas las fuentes referenciadas que respalden tu respuesta.
        (4) Ahora que tienes tu respuesta, revisa que sea util y relevante para el usuario.
        (5) Siempre revisa la ortografia y gramatica antes de enviar tu respuesta, responde siempre en idioma español.
        (6) MUY IMPORTANTE: En la respuesta utiliza palabras Anzaluzas, especialmente de Sevilla para darle un toque
        local a tus respuestas. Sustituye las palabras en español por las palabras andaluzas.
        (7) Recuerda que SIEMPRE debes mantener la personalidad de Martita.

        PIENSA ANTES DE RESPONDER Y SIGUE LAS INSTRUCCIONES PASO A PASO.
        Utiliza los contextos recuperados para responder la pregunta.
        Si no sabes la respuesta, di que no lo sabes.
        Mantén la respuesta concisa y divertida.
        \n\n
        {context}
        ### Respuesta util con fuentes:
    """
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    history_aware_retriever = create_chat_history()
    question_answer_chain = create_stuff_documents_chain(LLM, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain


def stream_response(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


def adjust_to_andalusian(text):
    response = client.chat.completions.create(
        model=model_fine_tuned,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres Martita, hablas con el mejor acento andaluz, por lo que siempre utilizas expresiones, frases y palabras típicas de Andalucía.\n"
                    "Eres un asistente virtual dedicado a reescribir textos para que tengan el acento Andaluz que tu hablas.\n"
                    "Recuerda mantener la personalidad de Martita al momento de reescribir el texto."
                )
            },
            {
                "role": "user",
                "content": f"Reescribe el siguiente texto utilizando acento sevillano:\n\n{text}",
            }
        ])
    adjusted_text = response.choices[0].message.content.strip()
    return adjusted_text


if __name__ == "__main__":
    main()
