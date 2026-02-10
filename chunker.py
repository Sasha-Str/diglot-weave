import re
import ebooklib
import json
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path

def chunk_epub_for_api(epub_path, max_chars=4000):
    """
    Reads an EPUB, extracts text from chapters, and chunks it.
    Returns a list of dicts: {'file_name': 'chap1.xhtml', 'text': '...'}
    """
    book = epub.read_epub(epub_path)
    all_chunks_for_api = []

    # 1. Iterate through every file in the book
    for item in book.get_items():
        
        # We only care about HTML documents (Chapters)
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            
            # 2. Extract raw HTML
            raw_html = item.get_content().decode('utf-8')
            soup = BeautifulSoup(raw_html, 'html.parser')
            
            # 3. Find specific story text
            # (Adjust tags if your specific ebook uses divs instead of p)
            paragraphs = soup.find_all(['p', 'h1', 'h2', 'blockquote'])
            
            # --- START CHUNKING LOGIC (Per Chapter) ---
            current_chunk = []
            current_length = 0
            
            for tag in paragraphs:
                text = tag.get_text().strip()
                if not text: continue
                
                para_len = len(text)
                
                # Check limit
                if current_length + para_len > max_chars:
                    # Save current chunk with metadata
                    all_chunks_for_api.append({
                        'file_name': item.get_name(),  # CRITICAL: Remembers "chapter1.html"
                        'text': "\n\n".join(current_chunk)
                    })
                    # Reset
                    current_chunk = [text]
                    current_length = para_len
                else:
                    current_chunk.append(text)
                    current_length += para_len
            
            # Don't forget the leftovers in this chapter
            if current_chunk:
                all_chunks_for_api.append({
                    'file_name': item.get_name(),
                    'text': "\n\n".join(current_chunk)
                })
                
    return all_chunks_for_api

# This will only allow for recombining into one huge text file, no chapters or similar
def chunk_txt_safely(text, max_chars=10000):
    """
    Splits text into chunks strictly by paragraph to preserve context.
    max_chars: Soft limit. We only break it if a SINGLE paragraph is huge.
    """
    
    # 1. Split by double newlines (standard paragraph break)
    # This creates a list of strings, where each string is one paragraph.
    paragraphs = text.split('\n\n')
    
    current_chunk = []
    current_length = 0
    chunks = []
    
    for paragraph in paragraphs:
        # Clean up whitespace
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # Estimated length of this paragraph (chars)
        para_len = len(paragraph)
        
        # 2. Check: Will adding this paragraph overflow the limit?
        if current_length + para_len > max_chars:
            # YES: The bucket is full.
            
            # A. Save the current bucket as a chunk
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
            
            # B. Start a new bucket with the current paragraph
            current_chunk = [paragraph]
            current_length = para_len
        else:
            # NO: The bucket has room. Add it.
            current_chunk.append(paragraph)
            current_length += para_len
            
    # 3. Don't forget the last bucket!
    if current_chunk:
        chunks.append("\n\n".join(current_chunk))
        
    return chunks

def save_chunks(chunks, save_path):
    job_data = []
    for i, chunk in enumerate(all_chunks):
        job_item = {
            "id": i,
            "source_file": chunk['file_name'],
            "original_text": chunk['text'],
            "translated_text": None,  # Empty for now
            "status": "pending"       # Mark as ready to do
        }
        job_data.append(job_item)

    # 3. Save the Job File
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(job_data, f, indent=2)


def chunker(
    source_folder = "user",
    book_name = "Dante - The Divine Comedy",
    file_name = "Dante - The Divine Comedy.epub"
):
    
    path = Path(source_folder) / file_name

    all_chunks = chunk_epub_for_api(path)
    print(f"Total chunks found: {len(all_chunks)}\n")

    new_path = Path(source_folder) / f"chunked_{book_name}.json"
    save_chunks(all_chunks, new_path)

def main():
    
    chunker()


if __name__ == "__main__":
    main()