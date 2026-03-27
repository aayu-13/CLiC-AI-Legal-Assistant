import pandas as pd
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer

# Load dataset
df = pd.read_csv("final_chunked_dataset.csv")

print("Dataset shape:", df.shape)

# Combine fields
df["Combined"] = df["Title"] + " " + df["Text"]

texts = df["Combined"].tolist()

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Generating embeddings...")

embeddings = model.encode(
    texts,
    batch_size=32,
    show_progress_bar=True,
    convert_to_numpy=True
)

# Normalize for cosine similarity
faiss.normalize_L2(embeddings)

# Create FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)

index.add(embeddings)

print("Index size:", index.ntotal)

# Save index
faiss.write_index(index, "faiss_index.bin")

# Save metadata
with open("metadata.pkl", "wb") as f:
    pickle.dump(df, f)

print("✅ Embeddings ready!")