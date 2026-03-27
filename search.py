import faiss
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# 🔥 Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# 🔥 Load FAISS index (built from chunked dataset)
index = faiss.read_index("faiss_index.bin")

# 🔥 Load chunked metadata (used for search)
with open("metadata.pkl", "rb") as f:
    chunked_df = pickle.load(f)

# 🔥 Load full dataset (used for full description)
full_df = pd.read_csv("final_ready_dataset.csv")


def search(query, top_k=5):
    # 🔹 Step 1: Convert query to embedding
    query_embedding = model.encode([query], convert_to_numpy=True)

    # Normalize for cosine similarity
    faiss.normalize_L2(query_embedding)

    # 🔹 Step 2: Search in FAISS (get extra results to filter duplicates)
    scores, indices = index.search(query_embedding, top_k * 3)

    # 🔹 Step 3: Keep BEST result per section
    section_map = {}

    for i, idx in enumerate(indices[0]):
        row = chunked_df.iloc[idx]
        section = row["Section"]
        score = float(scores[0][i])

        title = row["Title"].lower()
        query_lower = query.lower()

        # boost if query word in title
        if title.strip() == query_lower:
            score += 0.15
        elif query_lower in title:
            score += 0.08

        # Keep highest score for each section
        if section not in section_map or score > section_map[section]["Score"]:
            section_map[section] = {
                "Section": section,
                "Title": row["Title"],
                "Score": score
            }

    # 🔹 Step 4: Sort by score
    results = sorted(section_map.values(), key=lambda x: x["Score"], reverse=True)

    # 🔹 Step 5: Take top_k unique sections
    results = results[:top_k]

    # 🔹 Step 6: Attach FULL description from clean dataset
    final_results = []

    for r in results:
        try:
            full_row = full_df[full_df["Section"] == r["Section"]].iloc[0]

            final_results.append({
                "section_no": int(r["Section"]),
                "offense": full_row["Title"],
                "description": full_row["Text"],
                "score": r["Score"]
            })

        except:
            # fallback if something missing
            final_results.append({
                "section_no": int(r["Section"]),
                "offense": r["Title"],
                "description": "Details not available",
                "score": r["Score"]
            })

    return final_results


# 🔥 TESTING
if __name__ == "__main__":
    query = input("Enter your query: ")

    results = search(query)

    for r in results:
        print("\n---")
        print(f"BNS Section {r['section_no']}")
        print("Title:", r["offense"])
        print("Score:", round(r["score"], 3))
        print("Description:", r["description"][:300])