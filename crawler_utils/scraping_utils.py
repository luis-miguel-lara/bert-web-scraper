from urllib.parse import urlparse
import re
import os

current_dir = os.path.dirname(__file__)
os.chdir(current_dir)

with open("blacklist.txt", "r") as f_in:
    black_list = [l.strip().lower() for l in f_in.readlines()]


about_us_patterns =   [
                            r"about",
                            r"who",
                            r"why",
                            r"profile",
                            r"product",
                            r"brand",
                            r"merk",
                            r"over",
                            r"our",
                            r"this.is",
                            r"wie.*zijn",
                            r"wie.*is",
                            r"wat.we.doen",
                            r"what.we.do",
                            r"a.propos",
                            r"à.propos",
                            r"bedrijf",
                            r"company",
                            r"coöperatie",
                            r"organisatie",
                            r"corporate",
                            r"index",
                            r"home",
                            r"/(en|nl|fr|de)$",
                        ]




# for domians if href.count(".")>=2 (has to be >=2 and not ==2 because of .com.br/co.uk/.co.id/etc this examples should be skipped also) and "www" not in href -> create an additional www.domain.com and at the end delete all duplicates

### skip if cloudfare found in text
### /// skip urls  class contains cookie
def clean_url(url: str):
    """
    Keeps scheme (protocol) and domain of URL
    """
    scheme = urlparse(url).scheme
    domain = urlparse(url).netloc
    return f"{scheme}://{domain}"

def get_domain(url: str):
    return urlparse(url).netloc.replace("/", "")

def shorten_path(href):
    """
    shorten href
        /en/hello/abc -> /en/hello/
        /ewq/eqwe -> /ewq
    """
    pass

def fix_href(domain: str, href: str):
    """
    IMPORTANT:
        Skipping depeer than children url. be sure that first scraper (from DuckGoGo) only takes clean domain scheme
        ## wrong it can be domain.com/en/... need to work more here
    """
    href = re.sub(r"[()]", "", href)
    if href.startswith("/"):
        return domain + href
    elif href.lower().startswith("http"):
        return href
    return f"{domain}/{href}"
    #if href.startswith("/"):
    #    return domain + href if href.count("/") <= 2 else False
    #elif href.lower().startswith("http"):
    #    return href if href.count("/") <= 3 else False
    #return f"{domain}/{href}" if href.count("/") == 0 else False

def check_blacklist(href: str):
    """
    True if blacklisted, false otherwise
    """
    if any([True if re.search(pattern, href.lower()) is not None else False for pattern in black_list]):#This should be to delete the duckduckgo blacklist urls
        return True
    return False

def regex_find_urls(html):
    """
    Finding urls when the start page is javascript and the site body could not be (fully) rendered
    """
    regex_hrefs = re.findall(r"href=\".*?\"", html)
    regex_hrefs = [h.replace("href=", "").replace("\"", "") for h in regex_hrefs]
    other_urls  = [h for h in re.findall(r"http[^\" ]+", html) if h not in regex_hrefs]
    total_urls = [re.sub(r"[()]", "", h).strip() for h in regex_hrefs + other_urls]
    total_urls = [h for h in total_urls if len(h.replace("/", "").strip()) > 0]
    return total_urls

def similar_urls(url1: str, url2: str) -> str:
    """
    Asserting that two urls are different (to fix issue with https://www.afga.com containing similar url (https://www.afga.com/) at its landing page)
    """
    url1 = re.sub(r"https?://", "", url1).strip().lower()
    url1 = re.sub(r"/$", "", url1).strip()
    url2 = re.sub(r"https?://", "", url2).strip().lower()
    url2 = re.sub(r"/$", "", url2).strip()
    if url1 == url2:
        return True
    return False

def valid_url(domain: str, href:str) -> str :
    """
    This functions checks if the domain and href are.....

    Args:
        -
        -
    
    Returns:
        False if invalid URL
    """
    if not href.isalpha() and len(href) == 1: # to exclude hrefs like "/", "#", etc.
        return False
    if "#" in href or "?" in href: #returning False when "?" could be too strict
        return False 
    if check_blacklist(href):
        return False
    if similar_urls(domain, href):
        return False
    if href.startswith(domain) and len(href) - len(domain) < 2:
        return False
    if href.lower().startswith("http") and get_domain(domain.lower()) not in href.lower():
        return False
    if "javascript" in href.lower() and "http" not in href.lower() or  (href.lower().startswith("http") and "://" not in href) or href.startswith("#"):
        return False
    return fix_href(domain, href)


def get_about_us(domain, results):
    """
    """
    for r in results:
        print("r", r)
        if any([True if re.search(r, p) else False for p in about_us_patterns]):
            return valid_url(domain, r)
    return None #=> False


def reduce_results(results):
    """
    """
    if type(results) is not list or len(results) <= 100:
        return results
    results_dict = dict()
    for res in results:
        res_count = re.sub(r"https?://", "", res).count("/") # counting how many "/" excluding the http/https protocol slashes
        if res_count not in results_dict:
            results_dict[res_count] = [res]
        else:
            results_dict[res_count].append(res)
    new_results = list()
    for rc in results_dict:
        previous = len(new_results)
        if previous >= 100:
            break
        new_results.extend(results_dict[rc][:100-previous])  #adding only until 100
    return new_results
