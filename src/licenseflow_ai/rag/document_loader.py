from pathlib import Path 

KNOWLEDGE_BASE_DIR = Path('knowledge_base')

def load_documents() -> dict[str, str]:
    documents = {}

    for path in KNOWLEDGE_BASE_DIR.glob('*.md'):
        documents[path.name] = path.read_text(encoding='utf-8')
    
    return documents

def chunk_document(
    filename: str,
    content: str,
) -> list[dict[str, str]]:
    chunks = []

    sections = content.split("\n## ")

    for index, section in enumerate(sections):
        section = section.strip()

        # タイトルだけなど、短すぎるchunkは除外
        if len(section.split()) < 8:
            continue

        chunks.append(
            {
                "source": filename,
                "chunk_id": f"{filename}:{index}",
                "content": section,
            }
        )

    return chunks

def load_chunks() -> list[dict[str, str]]:
    documents = load_documents()
    chunks = []

    for filename, content in documents.items():
        chunks.extend(
            chunk_document(
                filename=filename,
                content=content,
            )
        )

    return chunks