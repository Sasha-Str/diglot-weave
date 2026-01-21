from pathlib import Path
import re
import html

# 1. Read your mixed text file
# Ensure encoding is utf-8 to handle the Russian correctly
text = Path("interwoven_text.txt").read_text(encoding="utf-8")


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
    r'([\u0400-\u04FF]+)', #finds (and remembers) strings of cyrillic letters
    r'<span class="ru">\1</span>', #replaces the string with the same string (the "1") and the wrapping
    html_body
)


# 5. Making it html
final_html = f"""
<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>My Book</title>
  <style>
    /* CSS for your book */
    body {{ font-family: serif; }}
    p {{ text-indent: 1.5em; margin-bottom: 0; margin-top: 0; }}
    
    /* 2. RUSSIAN WORD STYLING */
    .ru {{
        font-weight: bold;       /* Makes it thick */
        color: #3b5998;          /* A nice "Facebook Blue" - distinct but readable */
    }}
  </style>
</head>
<body>
{html_body}
</body>
</html>
"""


# 6. Save to file
Path("html_output.html").write_text(final_html, encoding="utf-8")