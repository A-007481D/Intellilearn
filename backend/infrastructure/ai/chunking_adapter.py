from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChunkingService:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_text(self, text):
        return self.splitter.split_text(text)
