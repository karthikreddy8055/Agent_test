import chromadb

class Memory:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection(name="agent_memory")

    def add(self, text, id):
        self.collection.add(
            documents=[text],
            ids=[id]
        )

    def search(self, query, n_results=2):
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results["documents"]