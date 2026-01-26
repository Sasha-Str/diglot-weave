from pathlib import Path
import re
import html
import json


class TagReplacer:
    def __init__(self):
        self.counter = 0
        self.footnotes = []  # Stores the definitions

    # This magic method runs when you "call" the class instance
    def __call__(self, match):
        self.counter += 1
        ref_id = f"ref_{self.counter}"
        
        # Split the braces to extract word, lemma and definition
        content = match.group(1)
        try:
            word, lemma, definition = content.split('|')
        except ValueError:
            return content
        
        # Create the footnote 
        note_html = f"""
        <aside id="{ref_id}" epub:type="footnote">
            <p><strong>{definition.strip()}</strong></p>
            <p><em>Base: {lemma.strip()}</em></p>
        </aside>
        """
        self.footnotes.append(note_html)
        
        # Return the link
        return f'<a href="#{ref_id}" epub:type="noteref" class="ru">{word.strip()}</a>'


def load_json(filename):
    path = Path(filename)
    if path.exists():
        with open(path,"r") as f:
            try:
                contents = json.load(f)
            
            #In case of an error, option to create new empty list. Otherwise exit the program
            except json.JSONDecodeError:
                print(f"Error reading the file {filename}")
                sys.exit()
    
    else:
        print("Invalid file path {path}")
        sys.exit()
    return contents

        # def create_footnote(word, count, dictionary, footnotes):
            # # 1. Increase counter so that each footnote has unique ID
            # count += 1
            # ref_id = f"ref_{count}"

            # # 2. Get the word found in the text
            # original_word = word.group(0)
            
            # # 3. Look up the lemma and definition of the matched word 
            # info = dictionary.pop(0)
            
            # # 4. Create the pop-up
            # popup_html = f'<a href="#{ref_id}" epub:type="noteref" class="ru">{original_word}</a>'
            
            # # 5. Create the footnote
            # note_html = f"""
            # <aside id="{ref_id}" epub:type="footnote">
                # <p><strong>{info['definition']}</strong></p>
                # <p><em>Base: {info['lemma']}</em></p>
            # </aside>
            # """
            
            # # 6. Save the footnote
            # footnotes.append(note_html)
            
            # return popup_html, count, dictionary, footnotes

# Initialise storage for footnotes/clickable words
footnotes_filename = "footnote.json"
# footnotes_html = []
# counter = 0


# 1. Read the mixed text file
# Ensure encoding is utf-8 to handle the Russian correctly
text = Path("interwoven_text.txt").read_text(encoding="utf-8")

replacer = TagReplacer()

# 2. Escape HTML special characters
# This ensures symbols like "&" don't break the ebook reader
safe_text = html.escape(text)


# 3. Create Paragraphs
# We split by double newline (\n\n) to find the paragraphs
paragraphs = safe_text.split('\n\n')

# Wrap them in <p> tags
html_body = ""
for p in paragraphs:
    if p.strip(): #to ignore empty lines
        html_body += f"<p>{p.strip()}<p>"


# 4. Find any Cyrillic character range (a Russian word) and wraps it in a <span class="ru">...</span>
# THIS WILL NEED TO BE MODIFIED FOR OTHER LANGUAGES
html_body = re.sub(
    r'\{\{(.*?)\}\}', 
    replacer, 
    html_body
)


# Combine footnotes into one block
all_footnotes = "\n".join(replacer.footnotes)

# 5. Making it html
# final_html = f"""
# <?xml version='1.0' encoding='utf-8'?>
# <!DOCTYPE html>
# <html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
# <head>
  # <title>My Book</title>
  # <style>
    # /* CSS for your book */
    # body {{ font-family: serif; }}
    # p {{ text-indent: 1.5em; margin-bottom: 0; margin-top: 0; }}
    
    # /* 2. RUSSIAN WORD STYLING */
    # a.ru {{
        # font-weight: bold;       /* Makes it thick */
        # color: #3b5998;          /* A nice "Facebook Blue" - distinct but readable */
    # }}
    
    # /* 3. Footnotes */
    # aside {{ display: none; }} /* Hides footnotes from main view */
    
  # </style>
# </head>
# <body>
# {html_body}
# </body>
# </html>
# """


# --- 4. FINAL HTML OUTPUT (TESTING VERSION) ---
final_html = f"""
<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>Test Mode</title>
  <style>
    body {{ 
        font-family: serif; 
        line-height: 1.6; 
        max-width: 800px; 
        margin: 0 auto; 
        padding: 20px; 
        padding-bottom: 200px; /* Space for the popup */
    }}
    p {{ text-indent: 1.5em; margin: 0; }}
    
    /* LINK STYLING */
    a.ru {{
        color: #3b5998;
        font-weight: bold;
        text-decoration: none;
        cursor: pointer;
        border-bottom: 1px dotted #3b5998; /* Visual hint it's clickable */
    }}
    a.ru:hover {{ background-color: #eaf2ff; }}

    /* HIDE FOOTNOTES (The data source) */
    aside {{ display: none; }}

    /* THE FAKE POPUP BOX (For testing only) */
    #test-popup {{
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 400px;
        background: white;
        border: 2px solid #3b5998;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        display: none; /* Hidden by default */
        z-index: 1000;
        font-family: sans-serif;
    }}
    #test-popup h3 {{ margin-top: 0; color: #3b5998; }}
  </style>
</head>
<body>

    {html_body}
    
    <section class="footnotes">
        {all_footnotes}
    </section>

    <div id="test-popup">
        <div id="popup-content"></div>
        <button onclick="document.getElementById('test-popup').style.display='none'" style="margin-top:10px;">Close</button>
    </div>

    <script>
        // Find all Russian links
        const links = document.querySelectorAll('a.ru');
        const popup = document.getElementById('test-popup');
        const popupContent = document.getElementById('popup-content');

        links.forEach(link => {{
            link.addEventListener('click', function(e) {{
                e.preventDefault(); // Stop the page from jumping
                
                // 1. Get the ID (e.g., "#ref_1" -> "ref_1")
                const targetId = this.getAttribute('href').substring(1);
                
                // 2. Find the hidden footnote with that ID
                const footnote = document.getElementById(targetId);
                
                if (footnote) {{
                    // 3. Copy text to our fake popup
                    popupContent.innerHTML = footnote.innerHTML;
                    popup.style.display = 'block';
                }}
            }});
        }});
    </script>

</body>
</html>
"""

# 6. Save to file
Path("html_output.html").write_text(final_html, encoding="utf-8")