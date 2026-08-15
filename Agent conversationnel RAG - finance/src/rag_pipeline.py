from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import hf_hub_download
from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain


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
    n_gpu_layers=-1, # Combien de couches de calcul doivent être exécutées sur le GPU plutôt que sur le CPU (-1 = toutes les couches possibles).
    temperature=0.1, # dégré d'aléatoire (déterministe 0 <-> 2 créatif, varié)
    verbose=False # logs internes
)

# --- Reformulation de la question à l'aide de l'historique ---
contextualize_prompt = ChatPromptTemplate.from_messages([
    ("system", "Reformule la dernière question de l'utilisateur en une question autonome et complète, "
                "compréhensible sans l'historique de conversation. Ne réponds pas à la question, "
                "reformule-la seulement. Si elle est déjà autonome, renvoie-la telle quelle."),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_prompt)

# --- Génération de la réponse, avec contexte + historique + source ---
qa_prompt = ChatPromptTemplate.from_messages([
    ("system", """Tu es un assistant destiné aux équipes ALM d'une entreprise d'assurance vie.
Tu réponds aux questions en te basant uniquement sur les extraits de DIC fournis ci-dessous.

Règles impératives :
- Réponds uniquement à partir des informations contenues dans le contexte fourni.
- Si l'information ne se trouve pas dans le contexte, dis-le clairement plutôt que d'inventer.
- Cite systématiquement la source (nom du fichier et page) de chaque information utilisée.
- Reste concis et factuel.

Contexte:
{context}"""),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)


# --- Conversation avec mémoire ---
chat_history = []

while True:
        question = input("Vous : ")
        if question.lower() in ("quit", "exit"):
             break

        response = rag_chain.invoke({"input": question, "chat_history": chat_history})

        print(f"\nAssistant : {response['answer']}\n")

        chat_history.append(HumanMessage(content=question))
        chat_history.append(AIMessage(content=response["answer"]))