from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from huggingface_hub import hf_hub_download
from langchain_community.chat_models import ChatLlamaCpp
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


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

retriever = vector_store.as_retriever(search_kwargs={"k":4})

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

# --- Test rapide du LLM seul, sans RAG pour l'instant ---
#response = llm.invoke("Bonjour assitant !")
#print(response.content)

# --- Formatage du contexte récupéré, avec la source de chaque chunk ---
def format_docs(retrieved_docs):
    formatted = []
    for doc in retrieved_docs:
        source = doc.metadata.get("source", "source inconnue")
        page = doc.metadata.get("page", "?")
        formatted.append(f"[Source: {source}, page {page}]\n{doc.page_content}")
    return "\n\n".join(formatted)

# --- Prompt avec consigne de sourcing ---
prompt = ChatPromptTemplate.from_template(
    """Tu es un assistant de chat destiné aux équipes du département ALM d'une grande entreprise d'assurance vie.
    Tu réponds aux questions en te basant uniquement sur les documents d'informations clé (DIC) fournis.

    Règles à suivre :
    - Réponds uniquement à partir des informations contenues dans le contexte fourni.
    - Si l'information ne se trouve pas dans le contexte, dis simplement et sans détours que cette information n'est pas disponible dans la base de données. Ne substitue JAMAIS l'information d'un autre fonds.
    - Cite systématiquement la source (nom du fichier et page) de chaque information que tu utilises.
    - Fait des réponses courtes et factuelles qui vont à l'essentiel et donnent l'information recherchée.
    - Si la question mentionne un fonds ou un produit précis, vérifie que le contexte fourni concerne bien CE fonds précis (regarde le nom du fonds et la source) avant de répondre.
    
    Contexte:
    {context}

    Question: {question}

    Réponse:"""
)

# --- Assemblage de la chaîne RAG ---
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print("\n=== Chunks Allianz dans l'index ===")
all_docs = vector_store.docstore._dict.values()
allianz_chunks = [doc for doc in all_docs if "Allianz" in doc.metadata.get("source", "")]

print(f"{len(allianz_chunks)} chunks Allianz trouvés dans l'index.\n")

for i, doc in enumerate(allianz_chunks):
    print(f"--- Chunk Allianz {i} (page {doc.metadata.get('page')}) ---")
    print(doc.page_content)
    print()