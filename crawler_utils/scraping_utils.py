from urllib.parse import urlparse

with open("crawler_utils/blacklist.txt", "r") as f_in:
    black_list = [l.strip().lower() for l in f_in.readlines()]

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
    if any([True if l in href.lower() else False for l in black_list]):#This should be to delete the duckduckgo blacklist urls
        return True
    return False

def valid_url(domain: str, href: str) -> str:
    """
    This functions checks if the domain and href are.....

    Args:
        -
        -
    
    Returns:
        False if invalid URL
    """
    if check_blacklist(href):
        return False
    elif href.lower().startswith("http") and get_domain(domain.lower()) not in href.lower():
        return False
    elif "javascript" in href.lower() and "http" not in href.lower() or  (href.lower().startswith("http") and "://" not in href) or href.startswith("#"):
        return False
    return fix_href(domain, href)