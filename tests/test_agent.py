from agent.memory import Memory

mem = Memory()

mem.add("IFRS9 is used for expected credit loss", "1")
mem.add("ChromaDB is a vector database", "2")

print(mem.search("credit"))