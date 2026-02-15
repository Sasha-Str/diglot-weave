from google import genai
from google.genai import types
from pydantic import BaseModel
from pathlib import Path
import json
import sys


class Output(BaseModel):
    modified_text: str
    new_words: list[str]



#Opens json file containing the known words
## NEED TO FIX ERROR WHEN FILE IS EMPTY/NON-EXISTENT

def load_json(filename,folder):
    path = Path(folder) / filename
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




#Pull the list of models, not part of the program
def get_model_list():
    client = genai.Client()
    print("List of models that support text generation: \n")
    for m in client.models.list():
        for action in m.supported_actions:
            if action == "generateContent":
                print(m.name)





#Saves text to a .txt document
def save_new_text(filename : str,text, folder):
    path = Path(folder) / filename
    
    with open(path,"w",encoding = "utf-8") as f:
        f.write(text)

#Function to update (rewrite) a json file with new words
def update_known_words(filename, existing_words : list[str], new_words : list[str], folder):
    path = Path(folder) / filename
    
    #1. Extend the list
    existing_words.extend(new_words)
    print(new_words)
    
    #2. Update (rewrite) the file
    with open(path,"w",encoding = "utf-8") as f:
        json.dump(existing_words, f, indent = 2, sort_keys = "True", ensure_ascii = "False")  #sort_keys ensures saving in alphabetical order?



#GET DATA FROM THE FILES

def pull_data(text_filename,words_filename,folder):

    print("Loading data...\n")
    path_temp = Path(folder) / text_filename
    
    text = path_temp.read_text(encoding="utf-8")
    # rus_text = Path(rus_text_filename).read_text(encoding="utf-8")     #Not needed
    words = load_json(words_filename,folder)
    return text, words


# CALL GEMINI TO PERFORM THE TRANSLATING AND WEAVING
# THIS IS WHERER THE LLM DOES ITS THING

# It is configured to output a json with two parts - the modified text and the new words

def call_ai(prompt, text, words):
    
    print("Generating new text...\n") 
    
    #Initialise the client
    client = genai.Client()
    
    
    response_raw = client.models.generate_content(
        model="gemini-3-flash-preview",                  # "gemini-flash-latest", "gemini-3-flash-preview"
        contents=[prompt, text, words],
        config = {
            "response_mime_type": "application/json",
            "response_schema": Output,
        }
    )
    response = response_raw.parsed
    return response.modified_text, response.new_words
    

def save_data(text_filename, words_filename, words, response_text, response_words, folder):

    #SAVING OUTPUT
    print("saving output...\n")
    save_new_text(text_filename,response_text, folder)
    update_known_words(words_filename, words, response_words, folder)

    print("saving complete")









def weave(
    source_folder = "user",
    en_text_filename = "eng_text.txt",
    target_lang = "Russian",
    known_words_filename = "known_words.json",
    en_text = ""
):
    

    #Initialise variables 
    known_words = []
    ai_prompt = f"The aim is to create a diglot weave based on a list of known words, and slowly introduce new words in the target language (similar to Prismatext). An English text has been provided. Also a list of known {target_lang} words (as lemmas) has been provided. Replace words or phrases from the text with their {target_lang} equivalents found in the list of known words. A literal or word-for word translation will not succeed, so when you notice that it is appropriate to add a {target_lang} word, ALTER THE SENTENCE STRUCTURE AS NEEDED to make it grammatically correct (or as close as possible) in both languages (e.g. adjectives coming after nouns in some European languages). Further, multiple words may be replaced by a single word in the target language or vice versa (e.g. in Russian 'a car' becomes 'машина', not 'a машина', 'have been' becomes 'были', 'to go' becomes 'идти', etc. All of these little grammatical rules that don't translate literally between the languages). If a word/lemma is known, it should appear in all appropriate instances, with correct inflection, conjugation, gender, and any other grammatical rules not found in English. Gradually (meaning at a rate of LESS THAN 1% OF ALL WORDS) introduce new {target_lang} words (EASIEST/SIMPLEST, MOST COMMON/EVERYDAY WORDS COME FIRST) into the text, and update the list of known words. Ensure that grammar, punctuation and capitalisation are consistent with rules in both English and {target_lang}. If/when a clause contains mostly words that are known, restructure it as a {target_lang} sentence (in terms of grammar, word order etc.) rather than retaining any of the original English structure. Return 2 objects. 1. The new text (which will be a hybrid of English and Russian). Retain input formatting and include a double newline in between paragraphs (if not already present). When introducing a {target_lang} word, it MUST be in the format {{{target_lang}Word|Lemma|Original Word(s)}} with no additional emphasis or all-caps for the Russian word and the lemma in lower-case. Beyond this, no additional formatting. No emphasising the {target_lang} words with asterisks or all caps. And 2. Return the list of newly added {target_lang} lemmas."
    output_text = ""
    output_words = []
    new_text_filename = f"woven_{en_text_filename}"
    footnote_filename = "footnote.json"
    
    
    
    # Pull the data from file
    if en_text == "":
        en_text, known_words = pull_data(en_text_filename,known_words_filename,source_folder)
    else:
        known_words = load_json(known_words_filename,source_folder)
    # LLM does its thing
    output_text, output_words = call_ai(ai_prompt,en_text,known_words)
    # Save the data to file 
    save_data(new_text_filename, known_words_filename, known_words, output_text, output_words, source_folder)
    return output_text




def main():
    
    weave()
    # get_model_list()
    
    return



if __name__ == "__main__":
    main()

