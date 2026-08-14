"""
Découpage des documents PDF, embedding et stockage mémoire avec FAISS
"""

import glob
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# --- PARSING ---

# Initialisation de la liste qui va contenir tous les documents chargés
documents = []

# On parcourt tous les PDF du dossier pour les charger un par un
for file in glob.glob("data/DIC/*.pdf"):
    try:
        # On utilise PyMuPDFLoader en priorité car PyPDFLoader à une mauvaise gestion des accents et carcatères spéciaux
        loader = PyMuPDFLoader(file)  # Retourne une liste de documents (un par page)
        documents += loader.load()
    except Exception:
        # PyPDFLoader en secours
        try:
            loader = PyPDFLoader(file)
            documents += loader.load()
        except Exception as e:
            # On n'affiche une erreur que si les deux loaders ont échoué
            print(f"Erreur survenue pour le fichier '{file}' : {e}")

print(f"{len(documents)} pages chargées au total.")
# print(documents[9].page_content[:500])


# --- CHUNKING ---

# Initialisation du séparateur de texte avec des paramètres spécifiques pour diviser le texte
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,  # Taille maximale des morceaux de texte
    chunk_overlap=60,  # Chevauchement entre les morceaux pour garder le contexte
    length_function=len,  # Fonction pour calculer la longueur des morceaux
    separators=["\n\n", "\n"]  # Séparateurs utilisés pour diviser le texte en morceaux
)

# Division du document en morceaux (chunks)
chunks = text_splitter.split_documents(documents=documents)

# Affichage du nombre de morceaux créés à partir du document PDF
print(f"{len(chunks)} chunks ont été créés par le splitter à partir du document PDF.")
# print(chunks[0].page_content)


# --- EMBEDDING ---

# Charger le modèle d'encodage de texte paraphrase-multilingual-mpnet-base-v2 de HuggingFace qui supporte le français avec de bons résultats :
embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    encode_kwargs={"normalize_embeddings": True}
)

# --- Stockage FAISS ---

# Création du Vector Store FAISS et vectorisation des chunks...
vector_store = FAISS.from_documents(
    documents=chunks,
    embedding=embedding
)

# Sauvegarde locale
vectorstore_dir = Path("vectorstore")
vectorstore_dir.mkdir(exist_ok=True)
vector_store.save_local(str(vectorstore_dir))