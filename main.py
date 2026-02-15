import re
import ebooklib
import json
from ebooklib import epub
from bs4 import BeautifulSoup
from pathlib import Path
from google import genai
from google.genai import types
from pydantic import BaseModel
import sys
import html
import chunker
import weaver
import footnoter
import time

# --- 1. CONFIGURATION ---
MIN_CHAPTER_LENGTH = 500  # If a file has fewer chars than this, it's likely front matter
LEGAL_KEYWORDS = ["project gutenberg license", "terms of use", "copyright"]
NAV_KEYWORDS = ["table of contents", "index", "contents"]

def should_skip_file(soup):
    """
    Analyzes the HTML content to decide if it's a story chapter or junk.
    Returns: True (SKIP) or False (PROCESS)
    """
    if not soup.body: return True
    
    text_content = soup.body.get_text().strip().lower()
    
    # RULE 1: Is it too short? (Title pages, empty spacers)
    if len(text_content) < MIN_CHAPTER_LENGTH:
        return True
        
    # RULE 2: Is it legal/copyright junk?
    for kw in LEGAL_KEYWORDS:
        if kw in text_content:
            return True
    # RULE 3: Is it a Table of Contents?
    for kw in NAV_KEYWORDS:
        # Check if the keyword appears in the first 200 chars (headers)
        if kw in text_content[:200]:
            return True

    # If it passes all tests, it's a real chapter!
    return False

def process_job(job_file="chunked_Dante - The Divine Comedy.json", folder = "user", max_calls = 5):
    # 1. Load the current state
    path = Path(folder) / job_file
    with open(path, "r", encoding="utf-8") as f:
        job_data = json.load(f)
    
    n = 0
    # 2. Find work to do
    for item in job_data:
        if item["status"] == "pending" and n < max_calls:
            print(f"Processing Chunk {item['id']} (from {item['source_file']})...")
            
            try:
                # --- CALL YOUR API HERE ---
                result_text = weaver.weave(target_lang = "Italian", en_text = item['original_text'])
                # Simulated result for testing:
                # result_text = f"Simulated translation of: {item['original_text'][:20]}..."
                
                # 3. Update the record in memory
                item["translated_text"] = result_text
                item["status"] = "completed"
                
                # 4. SAVE IMMEDIATELY (Checkpointing)
                # This ensures if you crash now, this chunk is saved.
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(job_data, f, indent=2)
                    
                print(f"Chunk {item['id']} saved.")
                
                n += 1
                # Be nice to the API
                time.sleep(8) 

            except Exception as e:
                print(f"Error on Chunk {item['id']}: {e}")
                break # Stop processing so you can fix the error

    print("Job finished or stopped.")

# To deal with a technical saving issue
def sanitize_book_ids(book):
    """
    Safely fixes missing IDs for all item types (Chapters, Covers, Images).
    """
    item_count = 1
    
    # 1. FIX ITEMS (Files in the book)
    for item in book.get_items():
        # Option A: Item uses 'uid' (Standard Chapters)
        if hasattr(item, 'uid'):
            if not item.uid:
                item.uid = f"item_{item_count}"
                item_count += 1
                
        # Option B: Item uses 'id' (Covers, Images, CSS)
        elif hasattr(item, 'id'):
            if not item.id:
                # Some objects require set_id(), others accept direct assignment
                try:
                    item.set_id(f"item_{item_count}")
                except AttributeError:
                    item.id = f"item_{item_count}"
                item_count += 1

    # 2. FIX TABLE OF CONTENTS (The Menu)
    # We use a mutable list [1] to keep the counter persisting through recursion
    def fix_toc_ids(toc_list, counter_wrapper):
        for item in toc_list:
            # Case A: Nested Section -> (Title, [children])
            if isinstance(item, tuple):
                _, children = item
                fix_toc_ids(children, counter_wrapper)
            
            # Case B: Link Object (Standard Chapter Link)
            elif hasattr(item, 'uid'):
                if not item.uid:
                    item.uid = f"nav_{counter_wrapper[0]}"
                    counter_wrapper[0] += 1
            
            # Case C: Fallback for objects using 'id'
            elif hasattr(item, 'id'):
                if not item.id:
                    item.id = f"nav_{counter_wrapper[0]}"
                    counter_wrapper[0] += 1

    # Start the recursive fix
    fix_toc_ids(book.toc, [1])


def compiler(
    original,
    json_file,
    output,
    source_folder = "user",
):
    original_epub = Path(source_folder) / original
    job_file = Path(source_folder) / json_file
    output_epub = Path(source_folder) / output
    
    # A. Load Data
    book = epub.read_epub(original_epub)
    with open(job_file, 'r', encoding='utf-8') as f:
        job_data = json.load(f)
    
    # B. Group chunks by filename
    # {'chap01.xhtml': "Full text...", 'chap02.xhtml': "Full text..."}
    chapter_map = {}
    for item in job_data:
        fname = item['source_file']
        text = item.get('translated_text') or item['original_text']
        
        if fname not in chapter_map:
            chapter_map[fname] = []
        chapter_map[fname].append(text)
    
    # C. Insert new text into the existing book
    print(f"Injecting translations into {len(chapter_map)} chapters...")
    
    for item in book.get_items():
        # Only process if we have translation data AND it's an XHTML file
        if item.get_name() in chapter_map and item.media_type == 'application/xhtml+xml':
            
            # 1. Parse FIRST to check content
            original_soup = BeautifulSoup(item.get_content(), 'html.parser')
            
            # 2. RUN THE FILTER
            if should_skip_file(original_soup):
                print(f"  - SKIPPING (Front Matter/Legal): {item.get_name()}")
                continue 

            print(f"  - Processing Story: {item.get_name()}")
            
            # 1. Join chunks
            full_text = "\n\n".join(chapter_map[item.get_name()])
            
            # 2. Format text and compile footnotes
            body_content, footnotes = footnoter.footnoter(input_text = full_text)
            
            # 3. Add newline for footnotes (formatting that no one will see)
            notes_content = "\n".join(footnotes)
            
            
            
            
            
            
            # --- START OF NEW STYLE TRANSPLANT LOGIC ---
            
            # 4. HEADER RESCUE (Critical for Gutenberg TOCs)
            original_headers = ""
            if original_soup.body:
                headers = original_soup.body.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                for h in headers:
                    original_headers += str(h) + "\n"

            # 5. STYLE TRANSPLANT
            new_head = original_soup.head
            if not new_head: new_head = original_soup.new_tag("head")

            # Inject CSS
            style_tag = original_soup.new_tag("style")
            style_tag.string = """
                a.ru { color: #2980b9; text-decoration: none; border-bottom: 1px dotted #2980b9; }
                aside.footnote-hidden { display: none; visibility: hidden; }
                section.footnotes { border-top: 1px solid #eee; margin-top: 2em; display: none; }
            """
            new_head.append(style_tag)
            
            if not new_head.find("meta", {"charset": "utf-8"}):
                new_head.insert(0, original_soup.new_tag("meta", charset="utf-8"))

            # 6. Build Page
            body_attrs = original_soup.body.attrs if original_soup.body else {}
            attr_str = "".join([f' {k}="{v}"' if isinstance(v, str) else f' {k}="{" ".join(v)}"' for k,v in body_attrs.items()])

            final_page = f"""<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en">
{new_head}
<body{attr_str}>
    {original_headers}
    
    {body_content}
    
    <section class="footnotes">
        {footnotes}
    </section>
</body>
</html>"""

            item.set_content(final_page.encode('utf-8'))
            
            # --- END OF NEW LOGIC ---
    
    # D. Ensure no saving errors
    print("Sanitizing IDs...")
    sanitize_book_ids(book)
    
    # E. Save the new Book
    epub.write_epub(output_epub, book, {})
    print(f"Success! Book saved to: {output_epub}")







# --- RUN IT ---
# process_job(max_calls = 5)

# Adjust filenames as needed

compiler("Dante - The Divine Comedy.epub", "chunked_Dante - The Divine Comedy.json", "Dante_weave.epub")







