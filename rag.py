import os, faiss
from sentence_transformers import SentenceTransformer
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
client = InferenceClient(
    model="openai/gpt-oss-20b",
    token=os.environ.get("HF_TOKEN"),
)

with open("knowledge/tips.txt", encoding="utf-8") as f:
    docs = [l.strip() for l in f if l.strip()]

index = faiss.IndexFlatIP(384)
index.add(embedder.encode(docs, normalize_embeddings=True))


def retrieve(query, k=3):
    qv = embedder.encode([query], normalize_embeddings=True)
    _, ids = index.search(qv, k)
    return [docs[i] for i in ids[0]]


def coach(stats):
    if not os.environ.get("HF_TOKEN"):
        raise RuntimeError("HF_TOKEN is not set. Add it to the .env file.")

    query = (
        f"drowsy {stats['drowsy_pct']}% distracted {stats['distracted_pct']}% "
        f"best focus streak {stats['best_streak_min']} min"
    )
    context = "\n".join(retrieve(query))
    messages = [
        {
            "role": "system",
            "content": "You are a concise study coach. Use only the provided tips.",
        },
        {
            "role": "user",
            "content": f"Session stats: {stats}\n\nTips:\n{context}\n\nGive 3 short, actionable suggestions.",
        },
    ]
    r = client.chat_completion(messages=messages, max_tokens=250)
    return r.choices[0].message.content
