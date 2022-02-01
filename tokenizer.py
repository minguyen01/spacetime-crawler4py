from stopwords import get_stopwords

token_frequency = dict()
longest_page_words = 0
longest_page = ""

# Tokenizes the text into alphanumeric sequences that could also contain dashes and apostrophes
def tokenize(text, url):
    token_list = []
    tokens = 0
    token = ""
    for c in text:
        if c.isascii() and (c.isalnum() or c == "-" or c == "'"):
            token = token + c
        elif len(token) != 0:
            token_list.append(token.lower())
            tokens += 1
            token = ""
    global longest_page_words
    global longest_page
    if (tokens > longest_page_words):
        longest_page_words = tokens
        longest_page = url
    return token_list

# Add the frequencies of a word into the token_frequency dictionary
def compute_word_frequencies(tokenList):
    for token in tokenList:
        if token not in token_frequency:
            token_frequency[token] = 1
        else:
            token_frequency[token] = token_frequency.get(token) + 1

# Prints the top-50 (non-stop) words based on the frequency amount from the token_frequency dictionary
def print_top_50_words():
    counter = 0;
    getValue = lambda pair : pair[1]
    print("Word frequency:", end = " ")
    for token,frequency in sorted(token_frequency.items(), key = getValue, reverse = True):
        if (token not in get_stopwords() and len(token) > 2):
            print(token + ' => ' + str(frequency), end = " | ")
            counter += 1
            if (counter == 50):
                print("")
                break
                
# Prints the longest page with its word counts that was recorded by the global variables
def print_longest_page():
    print("Longest Page: " + longest_page + " " + "Words: " + str(longest_page_words))