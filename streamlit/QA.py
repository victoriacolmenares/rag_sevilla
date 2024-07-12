import os
import streamlit as st
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from openai import OpenAI


client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
model_fine_tuned = 'ft:gpt-3.5-turbo-0125:personal::9ioWFa4G'
chroma_path = "./database/chroma"
template = """
    ###INSTRUCCIONES:
    Eres una asistente de IA dedicado a responder preguntas según el contexto proporcionado.
    Si no sabe la respuesta, simplemente diga que no la sabe. Sea lo más detallado posible en su respuesta..

    En tu respuesta, TEN EN CUENTA SIEMPRE:
    (1) Lee  detalladamente la pregunta y el contexto y comprende ambos antes de responder.
    (2) Debajo de tu respuesta, enumera todas las fuentes referenciadas que respalden tu respuesta.
    (4) Ahora que tienes tu respuesta, revisa que sea util y relevante para el usuario y este formateada para ser facil de leer.
    (5) Siempre revisa la ortografia y gramática antes de enviar tu respuesta, responde en idioma español y amigable.¡

    Responde a la siguiente pregunta utilizando el contexto proporcionado:
        ### Question: {question} ###
        ### Context: {context} ###
        ### Respuesta util con fuentes:
"""


def main():
    st.set_page_config(
        page_title="Sevilla QA",
        page_icon="💃",
    )

    rag_chain = create_rag_chain()

    st.title("Asistente de IA para turistas en Sevilla 💃")
    st.write(
        """
        Este asistente con IA te ayudará a encontrar información relevante sobre actividades,
        gastronomía y donde hospedarte en Sevilla.
        """
    )
    question = st.text_area(
        label="¡Pregúntame lo que quieras!",
        height=20,
        max_chars=150,
    )

    if st.button("Enviar"):
        with st.spinner(''):
            answer = get_answer(question, rag_chain)

        st.write(answer)


def create_rag_chain():
    db = Chroma(persist_directory=chroma_path, embedding_function=OpenAIEmbeddings())
    llm = ChatOpenAI(
        model=model_fine_tuned,
        temperature=0.7,
    )
    retriever = db.as_retriever()
    prompt = PromptTemplate.from_template(template)
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
        | adjust_to_andalusian
    )
    return rag_chain


def format_docs(docs):
    return "\n\n".join(
        f"{doc.page_content}\nFuente: {doc.metadata.get('source', 'N/A')}"
        for doc in docs
    )


def adjust_to_andalusian(text):
    response = client.chat.completions.create(
        model=model_fine_tuned,
        messages=[
            {
                "role": "system",
                "content": """
                    "Eres Martita, hablas con el mejor acento andaluz, por lo que siempre utilizas expresiones, frases y palabras típicas de Andalucía.\n"
                    "Eres un asistente virtual dedicado a reescribir textos para que tengan el acento Andaluz que tu hablas.\n"
                    "Recuerda mantener la personalidad de Martita al momento de reescribir el texto."
                """
            },
            {
                "role": "user",
                "content": f"Reescribe el siguiente texto utilizando acento sevillano:\n\n{text}",
            }
        ])
    adjusted_text = response.choices[0].message.content.strip()
    return adjusted_text


def get_answer(question, rag_chain):
    return rag_chain.invoke(question)


if __name__ == "__main__":
    main()
