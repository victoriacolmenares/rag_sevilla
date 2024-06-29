import streamlit as st
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


CHROMA_PATH = "chroma"
TEMPLATE = """
    ###INTRUCIONES:
    Eres un asistente de IA, dedicado a ayudar a los turistas a encontrar información relevante
    sobre actividades, ocios y gastronomía en documentos dedicado a la ciudad de Sevilla en España,
    para responder preguntas de manera util y eficiente'.

    En tu respuesta, TEN EN CUENTA SIEMPRE:
    (1) Se un lector atento a los detalles: lee la pregunta y el contexto y comprende ambos antes de responder.
    (2) Comienza la respuesta en un tono amigable y profesional, reiterando la pregunta
        para que el usuario sepa que la entendiste.
    (3) Debajo de tu respuesta, enumera todas las fuentes referenciadas que respalden tu respuesta.
    (4) Ahora que tienes tu respuesta, revisa que sea util y relevante para el usuario,
        y este formateada para ser facil de leer.
    (5) Siempre revisa la ortografia y gramatica antes de enviar tu respuesta, responde en idioma español.
    (6) IMPORTANTE: En la respuesta utiliza palabras Anzaluzas, especialmente de Sevilla para darle un toque
        local a tus respuestas.
        Para eso aquí tienes algunas palabras y expresiones típicas:
        Arfavo: Forma de decir "a favor".
        Chiquillo/a: Niño o niña, se usa mucho para referirse a cualquier persona joven.
        Miarma: Mi alma, amigo/a mío/a
        Pisha: Forma cariñosa de llamar a alguien, similar a "tío" o "chico".
        Quillo/a: Abreviatura de chiquillo/a.
        Sieso: Persona antipática o desagradable.
        Zalú: Abreviatura de "salud", usada como brindis o despedida.
        Acho: Expresión para llamar la atención, similar a "oye".
        Aro: Forma de decir "claro".
        Babucha: Zapato cómodo, tipo de zapatilla.
        Cachondeo: Broma, diversión.
        Chirimiri: Llovizna ligera.
        Jartible: Persona pesada o insistente.
        Manque: Aunque.
        Pechá: Gran cantidad de algo, "me he dado una pechá de reír".
        Pescaíto: Pez frito, típico de la gastronomía andaluza.
        Ponerse morao: Comer mucho.
        Rebujito: Bebida típica de la Feria de Abril, mezcla de manzanilla y refresco de lima-limón.
        Sieso: Persona antipática o aburrida.
        Tapear: Ir de tapas, actividad social muy común en Andalucía.
        Tos: Todos.
        Vamo a vé: Vamos a ver.
        Zafarrancho: Gran desorden.
        Jihome: Es un “sí, claro” irónico.
        A Jierro: Se utiliza para afirmar algo con mucho ahínco. Si te preguntasen si
        eres del Sevilla y así fuera dirías “del Sevilla a jierro”.
        Lavín: Pretende transmitir asombro, desagrado o sorpresa.
        Mucha calo: Hace mucho calor.
        Malafollá: Es una particular mezcla de un poco de mal humor, sorna y acidez.
    (7) El andaluz es un dialecto del español, que suele cortar palabras. Por ejemplo:
        Terminaciones de los verbos en -ido o -ado, quedan así: me he sentao y he comío.
        También algunas palabras suelen terminar en ico o ito. Por ejemplo: Que Bonico.

    PIENSA PASO POR PASO
    ###

    Responde a la siguiente pregunta utilizando el contexto proporcionado:
        ### Question: {question} ###
        ### Context: {context} ###
        ### Respuesta util con fuentes:
"""


def main():
    st.set_page_config(
        page_title="Conoce Sevilla",
        page_icon="💃",
    )

    rag_chain = create_rag_chain()

    st.title("Asistente de IA para turistas en Sevilla 💃")
    st.write(
        """
        Este asistente de IA te ayudará a encontrar información relevante sobre actividades,
        información y gastronomía en Sevilla.
        """
    )
    question = st.text_area(
        label="¿Que quieres saber de Sevilla?",
        height=20,
        max_chars=50,
    )

    if st.button("Enviar"):
        with st.spinner('Viajando a Sevilla...'):
            answer = get_answer(question, rag_chain)

        st.write(answer)


def create_rag_chain():
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=OpenAIEmbeddings())
    llm = ChatOpenAI(
        model='ft:gpt-3.5-turbo-1106:personal::9fRRutz3',
        temperature=0.7,
    )
    retriever = db.as_retriever()
    prompt = PromptTemplate.from_template(TEMPLATE)
    rag_chain = (
        {'context': retriever, 'question': RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain


def get_answer(question, rag_chain):
    return rag_chain.invoke(question)


if __name__ == "__main__":
    main()
