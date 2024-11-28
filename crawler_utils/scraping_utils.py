from urllib.parse import urlparse
from pathlib import Path
import os
import re

# Get the current file's path
current_path = Path(__file__).resolve()
parent_dir = current_path.parent

os.chdir(parent_dir)

with open("blacklist.txt", "r") as f_in:
    black_list = [l.lower().strip().lower() for l in f_in.readlines()]

with open("whitelist.txt", "r") as f_in:
    white_list = [l.lower().strip().lower() for l in f_in.readlines()]

def clean_url(url: str):
    """
    Keeps scheme (protocol) and domain of URL
    """
    url = re.sub(r":\d+$", "", url)
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
    if any([re.search(l, href.lower()) for l in black_list]):#This should  delete the duckduckgo blacklisted urls
        return True
    return False

def check_whitelist(href: str):
    """
    True if whitelisted, false otherwise
    there should´t be overlapping patterns since we will reduce to one per pattern maximum
    """
    if any([re.search(l, href.lower()) for l in white_list]):
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
        #print("-*-*-*black", href)
        return False
    elif href.lower().startswith("http") and get_domain(domain.lower()) not in href.lower():
        #print("-*-*-*error2", domain, href)
        return False
    elif "javascript" in href.lower() and "http" not in href.lower() or  (href.lower().startswith("http") and "://" not in href) or href.startswith("#"):
        #print("error3", href)
        return False
    return fix_href(domain, href)


def prune_urls(domain, anchors, max_len=25):
    """
    Pending
    """
    anchors_fixed = list()
    anchors_wl = list()
    anchors_to_validate = list()
    temp_wl = dict()
    temp_hrefs = set()

    for a in anchors:
        if not check_blacklist(href=a["href"]) and len(a["href"].split("?")[0]) > 0:
            a["href"] = fix_href(domain=domain, href=a["href"].split("?")[0])
            anchors_fixed.append(a)
    #make for loop for each white list and add to dict, if the same url is there, replace only if less / than curret value to whitelistk key
    #for wl in white_list:
    #    for a 
    for a in anchors_fixed:
        if a["href"] not in temp_hrefs and check_whitelist(href=a["href"]): ### FIX HERE TO REDUCE WHEN MULTIPLE OVER ONS or CONTACT
            temp_hrefs.add(a["href"])
            anchors_wl.append(a)
        elif a["href"] not in temp_hrefs:
            temp_hrefs.add(a["href"])
            anchors_to_validate.append(a)
    for wl in white_list:
        for a in anchors_wl:
            if wl not in temp_wl:
                temp_wl[wl] = a
            else:
                if temp_wl[wl]["href"].count("/") > a["href"].count("/"):
                    temp_wl[wl] = a #keeping lowest count of "/" per white list pattern
    anchors_final = list(temp_wl.values())
    for a in anchors_to_validate:
        if valid_url(domain, a["href"]) and len(anchors_final) < max_len:
            anchors_final.append(a)
        #else:
        #    print("failed to validate", domain, a["href"])
    return sorted(anchors_final, key=lambda a: a["href"].count("/"))[:max_len]