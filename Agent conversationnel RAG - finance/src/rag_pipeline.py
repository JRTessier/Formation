from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import hf_hub_download
from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

def build_rag_chain():
    # Charger le modèle d'encodage de texte paraphrase-multilingual-mpnet-base-v2 de HuggingFace qui supporte le français avec de bons résultats :
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        encode_kwargs={"normalize_embeddings": True}
    )

    # --- RETRIEVER ---
    vector_store = FAISS.load_local(
        Path("vectorstore"),
        embedding,
        allow_dangerous_deserialization=True
    )

    retriever = vector_store.as_retriever(search_kwargs={"k":8})

    # Charger le modèle LLM si absent
    MODEL_REPO = "bartowski/Mistral-7B-Instruct-v0.3-GGUF"
    MODEL_FILENAME = "Mistral-7B-Instruct-v0.3-Q4_K_M.gguf"
    MODEL_DIR = Path("models")

    model_path = MODEL_DIR / MODEL_FILENAME
    if not model_path.exists():
        print("Téléchargement du modèle...")
        hf_hub_download(repo_id=MODEL_REPO, filename=MODEL_FILENAME, local_dir=str(MODEL_DIR))
    else:
        print("Modèle déjà présent localement.")

    # --- LLM DE GENERATION ---
    llm = ChatLlamaCpp(
        model_path=str(model_path),
        n_ctx=4096, # nb de token max par fenêtre, à ajuster en fonction des résultats (texte coupé...)
        n_batch=512, # traite le prompt par blocs de 512 tokens plutôt que 8 --> gagne en rapidité
        n_gpu_layers=-1, # Combien de couches de calcul doivent être exécutées sur le GPU plutôt que sur le CPU (-1 = toutes les couches possibles).
        temperature=0.1, # dégré d'aléatoire (déterministe 0 <-> 2 créatif, varié)
        verbose=False # logs internes
    )

    # --- Reformulation de la question à l'aide de l'historique ---
    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("human", "Reformule la dernière question de l'utilisateur en une question autonome et complète compréhensible sans l'historique de conversation. Ne réponds pas à la question, reformule-la seulement. Si elle est déjà autonome, renvoie-la telle quelle."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_prompt)

    # --- Génération de la réponse, avec contexte + historique + source ---
    qa_prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder("chat_history"),
        ("human", """Tu es un assistant de chat destiné aux équipes du département ALM (gestion des actifs / passifs) d'une grande entreprise d'assurance vie.
            Ton rôle est d'aider les équipes à retrouver facilement des informations éparpillées dans l'ensemble des DIC (documents d'informations clé) à disposition.
            Tu réponds donc aux questions en te basant uniquement sur le contenu des DIC.

            Dans ce contexte, ALM signifie Asset Liability Management (gestion des actifs et des passifs), et DIC signifie Document d'Informations Clés, Ne confonds jamais ces sigles avec d'autres significations.

            Règles impératives :
            - Réponds uniquement à partir des informations contenues dans le contexte fourni.
            - N'utilise JAMAIS tes connaissances générales pour compléter ou remplacer le contexte.
            - Si le contexte ne permet pas de répondre à la question posée, réponds uniquement : "Cette information n'est pas disponible dans la base de données."
            - Cite systématiquement la source (nom du fichier et page) de chaque information utilisée.
            - Reste concis et factuel. Va à l'essentiel en délivrant mécaniquement l'information cherchée.
            - Ne débute jamais ta réponse en reprenant la question. Commence directement par l'information, avec un verbe à l'infinitif si la formulation d'y prête.

            Exemple de question et de réponse attendue :
            Question : "Quelle est la classification du fonds Federal Indiciel Japon ?"
            Réponse : "Actions internationales"

            Contexte:
            {context}

            Question : {input}"""
         ),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    return create_retrieval_chain(history_aware_retriever, question_answer_chain)


# --- Conversation avec mémoire ---
if __name__ == "__main__":
    rag_chain = build_rag_chain()
    chat_history = []

    print("Assistant DIC - tapez 'quit' pour quitter\n")

    while True:
            question = input("Vous : ")
            if question.lower() in ("quit", "exit"):
                break

            response = rag_chain.invoke({"input": question, "chat_history": chat_history})

            print(f"\nAssistant : {response['answer']}\n")

            chat_history.append(HumanMessage(content=question))
            chat_history.append(AIMessage(content=response["answer"]))