

from typing import List
import re

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:

    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()

    if len(text) <= chunk_size:
        return [text]

    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_len = 0
    
    for sentence in sentences:
        s_len = len(sentence)
        
        if current_len + s_len > chunk_size and current_chunk:
            
            chunk_text_val = " ".join(current_chunk)
            chunks.append(chunk_text_val)

            overlap_text = chunk_text_val[-overlap:] if len(chunk_text_val) > overlap else chunk_text_val
            current_chunk = [overlap_text, sentence]
            current_len = len(overlap_text) + s_len
        else:
            current_chunk.append(sentence)
            current_len += s_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    chunks = [c for c in chunks if c.strip()]
    
    return chunks

if __name__ == "__main__":
    test = "Hello world. This is a test. " * 100
    result = chunk_text(test)
    print(f"input length: {len(test)}, chunks: {len(result)}")
    print(f"first chunk length: {len(result[0])}")
