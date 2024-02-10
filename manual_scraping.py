import fitz
import re
from multi_column import column_boxes

doc = fitz.open("Article_02.pdf")

titre = doc.metadata['title']
authorList = doc.metadata['author'].split(", ")
keywords = doc.metadata['keywords'].split(", ")

keywords_list = ["Keywords: ","Keywords", "Key Word", "Keywords—", "Keywords:", "Key terms", "Main points","Keywords :","Key words:"]
keywords_stop_words=["1. ","I. Introduction", "Introduction","I. "]
text_start_keywords = ["I. Introduction","1. Introduction","I. Introduction", "Introduction"]
text_end_keywords = ["REFERENCES","REFERENCES "," REFERENCES", "References","references"," REFERENCES", " References"," references","REFERENCES:", "References:","references:","REFERENCES"]
reference_start_keywords = ["REFERENCES","REFERENCES", "References","references"," REFERENCES", " References"," references","REFERENCES:", "References:","references:","References "," References"," References ","References",]
reference_end_keywords = ["Appendix", "APPENDIX"]

abstract_stop_words = [
    "1 INTRODUCTION",
    "1. Introduction",
    "Keywords:",
    "I. INTRODUCTION",
    "I.  INTRODUCTION",
    "Keywords-",
    "Key words: ",
    "Categories and Subject Descriptors",
    "",  # Empty string
    "2 USE CASES",
    "CCS CONCEPTS",
    "Index Terms",
    "Keywords: ",
    "Introduction",
    "I. Introduction",
    "Keywords",
    "Key Word",
    "Keywords—",
    "Keywords:",
    "Key terms",
    "Main points",
    "Keywords :",
    "I.",
    "II.",
    "I.2.1 ",
    "General Terms",
    "KEYWORDS"
]

abstract_start_keywords = [
    "1 INTRODUCTION",
    "Abstract",
    "Abstract—",
    "Abstract—",
    "I. INTRODUCTION1",
    "Abstract. —",
    "Abstract. ",
    "Abstract.",
    "1 ABSTRACT",
    "1  ABSTRACT",
    "Abstract",
    "Abstract——",
    "Summary",
    "abstract",
    "ABSTRACT",
    "ABSTRACT.",
    " ABSTRACT_",
    " Abstract:",
    " Abstract:"
]


def extract_abstract(text, start_keywords, end_keywords):
    abstract_start = None
    abstract_end = None

    for keyword in start_keywords:
        start_index = text.find(keyword)
        print(f"start index : {start_index}")
        if start_index != -1:
            abstract_start = start_index + len(keyword)
            break

    if abstract_start:
        for keyword in end_keywords:
            end_index = text.find(keyword, abstract_start)
            print(f"end index : {end_index}")
            if end_index != -1:
                abstract_end = end_index
                break

    if abstract_start and abstract_end:
        return text[abstract_start:abstract_end].strip()

    return None


'''
def extract_abstract_v10(text, start_markers, end_markers):
    abstract_start = len(text)
    abstract_end = len(text)

    # Iterate through all start markers to find the earliest occurrence
    for start_marker in start_markers:
        match_start = re.search(start_marker, text, re.IGNORECASE)
        if match_start and match_start.start() < abstract_start:
            abstract_start = match_start.start()

    # Iterate through all end markers after the earliest start marker to find the earliest occurrence
    for end_marker in end_markers:
        match_end = re.search(end_marker, text[abstract_start:], re.IGNORECASE)
        if match_end and match_end.start() < abstract_end:
            abstract_end = match_end.start() + abstract_start
            break  # Stop at the first valid end marker found

    # Extract the abstract if valid start and end indices are found
    if abstract_start < abstract_end:
        return text[abstract_start:abstract_end].strip()

    return None

'''

def find_keywords(text, keywords_list):
    for keyword in keywords_list:
        match = re.search(fr"\s*{keyword}\s*:?\s*", text, flags=re.IGNORECASE)
        if match:
            keyword_start = match.start()
            for stop_word in keywords_stop_words:
                stop_index = text.find(stop_word, keyword_start)
                if stop_index != -1:
                    keywords_text = text[keyword_start:stop_index]
                    return keywords_text
            return text[keyword_start:]
    return None

abstract_found = False
keywords_found = False

def extract_text_between_markers(doc, start_keywords, end_keywords):
    # Combine start keywords into a regex pattern for finding the start marker
    start_pattern = "|".join(re.escape(keyword) for keyword in start_keywords)
    start_regex = re.compile(start_pattern, re.IGNORECASE)

    # Combine end keywords into a regex pattern for finding the end marker
    end_pattern = "|".join(fr'\b{re.escape(keyword)}\b' for keyword in end_keywords)
    end_regex = re.compile(end_pattern)

    # Join all the text from pages into a single string
    full_text = "\n".join(page.get_text() for page in doc)

    # Find the starting match
    start_match = start_regex.search(full_text)
    if start_match:
        start_index = start_match.start()
    else:
        return None  # Start marker not found

    # Find the ending match after the start index
    end_match = end_regex.search(full_text[start_index:])
    if end_match:
        end_index = end_match.start() + start_index
    else:
        return None  # End marker not found

    # Extract text between start and end indices
    extracted_text = full_text[start_index:end_index].strip()
    return extracted_text

def extract_references(doc, start_keywords, end_keywords):
    references = []
    start_index = None
    end_found = False

    # Constructing exact case-sensitive patterns for start keywords
    start_pattern = "|".join(fr'\b{re.escape(keyword)}\b' for keyword in start_keywords)
    start_regex = re.compile(start_pattern)

    # Combine end keywords into a regex pattern for finding the end marker
    end_pattern = "|".join(fr'\b{re.escape(keyword)}\b' for keyword in end_keywords)
    end_regex = re.compile(end_pattern)

    # Find the starting index in the document
    for page in doc:
        text = page.get_text()
        for keyword in start_keywords:
            if re.search(fr'\b{re.escape(keyword)}\b', text):
                start_index = text.find(keyword)
                if start_index != -1:
                    break
        if start_index is not None and start_index != -1:
            break

    if start_index is None or start_index == -1:
        return None

    # Search for references within the defined section
    capturing = False
    for page in doc:
        text = page.get_text()
        if start_index >= 0:
            extracted_text = text[start_index:]

            lines = extracted_text.split('\n')
            reference = ''
            for line in lines:
                line = line.strip()

                # Check for the start of a reference
                if start_regex.search(line):
                    capturing = True

                # Check for reference pattern only if capturing is True
                if capturing:
                    if re.match(r'^\[\d+\]', line):
                        references.append(reference.strip())
                        reference = line
                    else:
                        reference += ' ' + line
                
                # Check for end keywords to stop capturing references
                if any(end_regex.search(line) for keyword in end_keywords):
                    capturing = False
                    break

            if capturing:
                references.append(reference.strip())
                break
    if references:
        references.pop(0)

    return references
