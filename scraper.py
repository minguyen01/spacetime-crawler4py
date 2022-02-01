import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from tokenizer import *

visited_URLS = set()
URL_queries = {}
robots_prohibited = {}
ics_subdomains = {}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

# Prints the number of unique URLs currently found
def print_num_unique_links():
    print("Unique Links: " + str(len(visited_URLS)))

# Adds an .ics.uci.edu subdomain to the ics_subdomain map if not currently in the map
# Increment the subdomain's associtiated value if currently in the map
def add_subdomain(url):
    if (not url.startswith("https")):
        url = url.replace("http","https")
    if (".ics.uci.edu" in url):
        if url not in ics_subdomains:
            ics_subdomains[url] = 1
        else:
            ics_subdomains[url] = ics_subdomains.get(url) + 1

# Checks the robots.txt given and adds the disallowed URLs to the prohibited list
def check_robots_txt(resp):
    prohibited_list = []
    try:
        text = resp.raw_response.content.decode()
        user_agent = False
        for line in text.splitlines():
            if (line.lower().startswith("user-agent: *")):
                user_agent = True
            elif ("Disallow:" in line and user_agent == True):
                prohibited_list.append(line.split(" ")[1].replace("*", ".*") + ".*")
            else:
                user_agent = False
    except:
        return prohibited_list
    return prohibited_list

# Transforms an HTML hyperlink that was obtained into a full URL link
def transform_link(currentURL, URL):
    newURL = URL

    if ('#' in URL):
        newURL = newURL[0:newURL.index("#")]
    if (URL.startswith("//")):
        newURL = urlparse(currentURL).scheme + ":" + newURL
    elif (URL.startswith("/")):
        newURL = urlparse(currentURL).scheme + "://" + urlparse(currentURL).netloc + newURL   
        
    return newURL
    
def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    # Printing for reporting purposes
    print("====================================================")
    print_num_unique_links()
    print_longest_page()
    
    
    links = set()
    schemeNetloc = urlparse(url).scheme + "://" + urlparse(url).netloc
    
    if (resp.status == 200):
        
        # If it is a robot.txt URL, call the check_robots_txt function to prohibit certain URLS
        # If it is not, then check whether it is a prohibited URL
        if ("robots.txt" in resp.url):
            robots_prohibited[schemeNetloc] = check_robots_txt(resp)
        else:
            if schemeNetloc in robots_prohibited:
                for prohibited in robots_prohibited[schemeNetloc]:
                    if (re.search(prohibited, url) != None):
                        return []
            try:
                # Add the URL to visited_URLS and find all the tags associated with 'a'
                visited_URLS.add(url)
                soup = BeautifulSoup(resp.raw_response.content.decode(), "html.parser")
                hyperlinkTags = soup.find_all('a')
                
                # Printing for reporting purposes
                compute_word_frequencies(tokenize(soup.get_text(), url))
                print_top_50_words()
                add_subdomain(schemeNetloc)
                print("ics_subdomains: " + str(ics_subdomains))

                # Add full URL links to the link set
                for tag in hyperlinkTags:
                    if (tag.get("href") is not None):
                        links.add(transform_link(url, tag.get("href")))
                        
                # If the current scheme + netLoc does not have an entry in the robots_prohibited map
                # Add a robots.txt URL to be searched through next
                if schemeNetloc not in robots_prohibited:
                    robots_prohibited[schemeNetloc] = []
                    return sorted(list(links)) + [schemeNetloc + "/robots.txt"]
            except:
                return []
            
    return sorted(list(links))

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        schemeNetloc = parsed.scheme + "://" + parsed.netloc
        domainPath = parsed.netloc + parsed.path
        
        if parsed.scheme not in set(["http", "https"]):
            return False
        if url in visited_URLS:
            return False
        if "share=" in parsed.query:
            return False
        if ((re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}", url) != None) or (re.search("[0-9]{4}-[0-9]{2}", url) != None)):
            return False
        if re.search("sort", parsed.query) != None:
            return False
        if (".ics.uci.edu" not in domainPath and
            ".cs.uci.edu" not in domainPath and
            ".informatics.uci.edu" not in domainPath and
            ".stat.uci.edu" not in domainPath and
            "today.uci.edu/department/information_computer_sciences" not in domainPath):
            return False
        if len(parsed.query) != 0:
            if (domainPath not in URL_queries):
                URL_queries[domainPath] = 1
            elif ((domainPath in URL_queries) and (URL_queries[domainPath] < 5)):
                URL_queries[domainPath] = URL_queries.get(domainPath) + 1
            else:
                return False
        if schemeNetloc in robots_prohibited:
            for prohibited in robots_prohibited[schemeNetloc]:
                if (re.search(prohibited, url) != None):
                    return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz"
            + r"|py|r|sh|cpp|java|sql)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
