# text chunking - splits documents into smaller pieces for embedding
# 
# tried a few approaches:
# 1. fixed size chunks - simple but cuts sentences in middle (bad)
# 2. sentence based - better but some sentences are very long  
# 3. this version - sentence based with overlap (seems to work best)
#
# chunk_size=1000 and overlap=200 worked best in my testing

from typing import List
import re


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    
    # clean up extra whitespace first
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    # if text is short enough just return as is
    if len(text) <= chunk_size:
        return [text]
    
    # split into sentences
    # this regex isnt perfect but handles most cases
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_len = 0
    
    for sentence in sentences:
        s_len = len(sentence)
        
        if current_len + s_len > chunk_size and current_chunk:
            # save current chunk
            chunk_text_val = " ".join(current_chunk)
            chunks.append(chunk_text_val)
            
            # keep last bit for overlap
            # this helps with context at chunk boundaries
            overlap_text = chunk_text_val[-overlap:] if len(chunk_text_val) > overlap else chunk_text_val
            current_chunk = [overlap_text, sentence]
            current_len = len(overlap_text) + s_len
        else:
            current_chunk.append(sentence)
            current_len += s_len
    
    # dont forget the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    # filter empty chunks
    chunks = [c for c in chunks if c.strip()]
    
    return chunks


# quick test
if __name__ == "__main__":
    test = "Hello world. This is a test. " * 100
    result = chunk_text(test)
    print(f"input length: {len(test)}, chunks: {len(result)}")
    print(f"first chunk length: {len(result[0])}")
