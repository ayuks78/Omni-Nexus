import json
import hashlib
import re
import math
from typing import List, Dict
from pathlib import Path


class SimpleVectorStore:
    def __init__(self, storage_path="./data/rag_store.json"):
        self.storage_path = storage_path
        self.documents = []
        self._load()

    def _load(self):
        try:
            path = Path(self.storage_path)
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
        except:
            self.documents = []

    def _save(self):
        try:
            path = Path(self.storage_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[RAG] Save error: {e}")

    def _tokenize(self, text):
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        stopwords = {'a', 'o', 'e', 'de', 'do', 'da', 'em', 'um', 'uma', 'para', 'com', 'que', 'the', 'is', 'and', 'or', 'to', 'of'}
        return [t for t in tokens if t not in stopwords and len(t) > 1]

    def _compute_tf(self, tokens):
        tf = {}
        total = len(tokens)
        if total == 0:
            return tf
        for token in tokens:
            tf[token] = tf.get(token, 0) + 1
        for token in tf:
            tf[token] /= total
        return tf

    def _cosine_similarity(self, vec1, vec2):
        all_terms = set(vec1.keys()) | set(vec2.keys())
        dot_product = sum(vec1.get(t, 0) * vec2.get(t, 0) for t in all_terms)
        mag1 = math.sqrt(sum(v**2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v**2 for v in vec2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)

    def add_document(self, content, metadata=None):
        doc_id = hashlib.md5(content.encode()).hexdigest()[:12]
        chunks = self._chunk_text(content)
        for i, chunk in enumerate(chunks):
            tokens = self._tokenize(chunk)
            tf_vector = self._compute_tf(tokens)
            doc = {
                "id": f"{doc_id}_{i}",
                "parent_id": doc_id,
                "content": chunk,
                "tokens": tokens,
                "tf_vector": tf_vector,
                "metadata": metadata or {},
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            self.documents.append(doc)
        self._save()
        return doc_id

    def _chunk_text(self, text, chunk_size=512, overlap=50):
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = ' '.join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            start = end - overlap
        return chunks if chunks else [text]

    def search(self, query, top_k=5):
        query_tokens = self._tokenize(query)
        query_tf = self._compute_tf(query_tokens)
        results = []
        for doc in self.documents:
            similarity = self._cosine_similarity(query_tf, doc.get("tf_vector", {}))
            if similarity > 0.01:
                results.append({
                    "id": doc["id"],
                    "content": doc["content"],
                    "similarity": round(similarity, 4),
                    "metadata": doc.get("metadata", {})
                })
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def get_all_documents(self):
        seen = set()
        unique = []
        for doc in self.documents:
            parent = doc.get("parent_id", doc["id"])
            if parent not in seen:
                seen.add(parent)
                unique.append({
                    "id": parent,
                    "preview": doc["content"][:200],
                    "metadata": doc.get("metadata", {}),
                    "chunks": doc.get("total_chunks", 1)
                })
        return unique

    def delete_document(self, doc_id):
        initial = len(self.documents)
        self.documents = [d for d in self.documents if d.get("parent_id") != doc_id and d.get("id") != doc_id]
        if len(self.documents) < initial:
            self._save()
            return True
        return False

    def clear_all(self):
        self.documents.clear()
        self._save()


class RAGSystem:
    def __init__(self):
        self.vector_store = SimpleVectorStore()

    def ingest_text(self, text, source="manual", title="Untitled"):
        metadata = {"source": source, "title": title, "char_count": len(text), "word_count": len(text.split())}
        doc_id = self.vector_store.add_document(text, metadata)
        return {"status": "success", "doc_id": doc_id, "metadata": metadata}

    def query(self, question, top_k=3):
        results = self.vector_store.search(question, top_k)
        if not results:
            return ""
        parts = []
        for i, r in enumerate(results):
            parts.append(f"[Doc {i+1}] (Relevancia: {r['similarity']:.2%})\n{r['content']}")
        return "\n\n---\n\n".join(parts)

    def get_documents(self):
        return self.vector_store.get_all_documents()

    def delete_document(self, doc_id):
        return self.vector_store.delete_document(doc_id)

    def clear(self):
        self.vector_store.clear_all()
