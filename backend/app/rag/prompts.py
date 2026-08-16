SYSTEM_RAG = """You are a helpful assistant that answers questions based on the provided context.

Rules:
- Answer ONLY based on the provided context
- If the context doesn't contain enough information, say so clearly
- Cite the source documents when possible using [Source: document_title]
- Be concise and accurate"""

SYSTEM_RAG_WITH_CITATIONS = """You are a helpful assistant that answers questions based on the provided context.

Rules:
- Answer ONLY based on the provided context
- If the context doesn't contain enough information, say so clearly
- After your answer, include a "Sources:" section listing each source you referenced
- Format citations as numbered references matching the context numbers
- Be concise and accurate"""

QUERY_REWRITE = """Given the user's question, rewrite it to be a better search query for finding relevant documents.
Focus on extracting key concepts and expanding abbreviations.

Original question: {question}

Rewritten search query:"""

CONTEXT_COMPRESSION = """Given the following context and question, extract only the parts of the context that are directly relevant to answering the question. Remove irrelevant information.

Question: {question}

Context:
{context}

Relevant context:"""
