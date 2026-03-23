import chromadb
import uuid


class Memory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection(name="agent_memory")

    def add(self, text, metadata=None):
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[str(uuid.uuid4())]
        )

    def search(self, query, n_results=3):
        return self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

    def get_all(self):
        return self.collection.get()

    
    def exists(self, text):
        results = self.collection.query(
            query_texts=[text],
            n_results=1
        )

        docs = results.get("documents", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not docs:
            return False

        # exact match
        if docs[0].strip().lower() == text.strip().lower():
            return True

        # stricter semantic similarity
        if distances and distances[0] < 0.15:
            return True

        return False