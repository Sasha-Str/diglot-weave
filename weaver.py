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

def load_json(filename):
    path = Path(filename)
    if path.exists():
        with open(path,"r") as f:
            try:
                contents = json.load(f)
            
            #In case of an error, option to create new empty list. Otherwise exit the program
            except json.JSONDecodeError:
                y_n = input(f"Error reading the file {filename}, overwrite? (Y/N)\n")
                if y_n in ["y","Y"]:
                    contents = ["он"]
                else:
                    print("Please specify a valid file")
                    sys.exit()
    
    else:
        contents = ["он"]
    return contents




#Pull the list of models, not part of the program
def get_model_list():
    client = genai.Client()
    print("List of models that support text generation: \n")
    for m in client.models.list():
        for action in m.supported_actions:
            if action == "generateContent":
                print(m.name)



#Function to update (rewrite) a json file with new words
def update_known_words(filename, existing_words : list[str], new_words : list[str]):
    path = Path(filename)
    
    #1. Extend the list
    existing_words.extend(new_words)
    
    #2. Update (rewrite) the file
    with open(path,"w",encoding = "utf-8") as f:
        json.dump(existing_words, f, indent = 2, sort_keys = "True", ensure_ascii = "False")  #sort_keys ensures saving in alphabetical order?


#Saves text to a .txt document
def save_new_text(filename : str,text):
    path = Path(filename)
    
    with open(path,"w",encoding = "utf-8") as f:
        f.write(text)

#Saves key/footnote to file
def save_footnote(filename, footnotes):
    path = Path(filename)
    
    # Convert the object to a plain dictionary that can be saved as a json
    temp_dict = [item.model_dump() for item in footnotes]
    
    with open(path,"w",encoding = "utf-8") as f:
        json.dump(temp_dict, f, indent = 2, ensure_ascii = "False")



#GET DATA FROM THE FILES

def pull_data(text_filename,words_filename):

    print("Loading data...\n")
    
    text = Path(text_filename).read_text(encoding="utf-8")
    # rus_text = Path(rus_text_filename).read_text(encoding="utf-8")     #Not needed
    words = load_json(words_filename)
    return [text, words]


# CALL GEMINI TO PERFORM THE TRANSLATING AND WEAVING
# THIS IS WHERER THE LLM DOES ITS THING

# It is configured to output a json with two parts - the modified text and the new words

def call_ai(prompt, text, words):
    
    print("Generating new text...\n") 
    
    #Initialise the client
    client = genai.Client()
    
    
    response_raw = client.models.generate_content(
        model="gemini-flash-latest",                  # "gemini-flash-latest", "gemini-3-flash-preview"
        contents=[prompt, text, words],
        config = {
            "response_mime_type": "application/json",
            "response_schema": Output,
        }
    )
    response = response_raw.parsed
    return [response.modified_text, response.new_words]
    

def save_data(text_filename, words_filename, words, response_text, response_words):

    #SAVING OUTPUT
    print("saving output...\n")
    save_new_text(text_filename,response_text)
    update_known_words(words_filename, words, response_words)

    print("saving complete")









def weave():
    

    #Initialise variables 
    eng_text_filename = "eng_text.txt"
    # rus_text_filename = "rus_text.txt"                            # NOT USED
    known_words_filename = "known_words.json"
    eng_text = ""
    known_words = []
    en_ru_prompt = "The aim is to create a diglot weave based on a list of known words, then to slowly introduce new words (similar to Prismatext). An English text has been provided. Also a list of known Russian words (as lemmas) has been provided. Replace words or phrases from the text with their Russian equivalents. A literal or word-for word translation will not succeed, so when you notice that it is appropriate to add a Russian word, ALTER THE SENTENCE AS NEEDED to make it grammatically correct (or as close as possible) in both languages. FOR EXAMPLE, multiple words may be replaced by a single word in the target language or vice versa (e.g. 'a car' becomes 'машина', not 'a машина', 'have been' becomes 'были', 'to go' becomes 'идти', etc. All of these little grammatical rules that don't translate literally between the languages). If a word/lemma is known, it should appear in all appropriate instances, with correct inflection and conjugation (remember all 3 genders). Gradually (less than 1% of words) introduce new Russian words (EASIER, EVERYDAY WORDS COME FIRST). Ensure that grammar, punctuation and capitalisation are consistent with rules in both English and Russian. If/when a clause contains mostly words that are known, it should be structured like a Russian sentence (in terms of grammar, word order etc.) rather than retaining any of the original English structure. Return 2 objects. 1. The new text (which will be a hybrid of English and Russian), and include a double newline in between paragraphs. When introducing a Russian word, it MUST be in the format {{RussianWord|Lemma|Original Word(s)}} with no additional emphasis or all-caps for the Russian word and the lemma in lower-case. Beyond this, no additional formatting. No emphasising the Russian words with asterisks or all caps. And 2. Return the list of newly added Russian lemmas."
    output_text = ""
    output_words = []
    new_text_filename = "interwoven_text.txt"
    footnote_filename = "footnote.json"
    
    
    
    # Pull the data from file
    [eng_text,known_words] = pull_data(eng_text_filename,known_words_filename)
    # LLM does its thing
    [output_text,output_words] = call_ai(en_ru_prompt,eng_text,known_words)
    # Save the data to file 
    save_data(new_text_filename, known_words_filename, known_words, output_text, output_words)




def main():
    
    weave()
    # get_model_list()
    
    return



if __name__ == "__main__":
    main()

