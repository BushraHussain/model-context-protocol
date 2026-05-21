def store_memory(text: str):
    return {
        "status": "success",
        "message": "Memory received",
        "data": text
    }


def search_memory(query: str):
    return {
        "status": "success",
        "query": query,
        "results": []
    }