from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from crawler_utils.scraping_utils import clean_url, check_blacklist, get_domain, fix_href, prune_urls, valid_url
from crawler_utils.file_utils import clean_create_dir, delete_create_dir, html_filename
from time import sleep
import os
from pathlib import Path
import re

# Get the current file's path
current_path = Path(__file__).resolve()
parent_dir = current_path.parent

os.chdir(parent_dir)
"""
Model:
give score based on:
- .be domain (not necessary but could give extra points)
- similarity between domain name to company name 
- content matching  in index.html: company name, data: phone, address, etc.   
- content availability
"""
class Company:
    """
    This class has the goal to scrape company information
    """
    def __init__(self, name, region = "Belgium (nl)"):
        self.name = name
        self.region = region
        # instance of Options class
        self.options = Options()
        self.options.add_argument("log-level=3")
        self.options.add_argument('--disable-browser-side-navigation')
        # parameter change on options (headless) attribute
        #self.options.add_argument("--headless")
        
        self.options.add_argument("--enable-automation")## 
        self.options.add_argument("disable-infobars")## this may causes error 403
        self.options.add_argument("--disable-extensions")
        
    def search(self): 
        """
        The search function has the goal to find the results on the selected engine (by deafault DuckDuckGo)
        """
        self.driver = webdriver.Chrome(options = self.options)
        self.driver.get("https://duckduckgo.com")
        if self.region is not None:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "searchbox_input"))).send_keys(self.name)
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Search' and @type='submit']"))).click()
            self.driver.find_element(By.XPATH, "//a[@data-testid='region-filter-label']").click()
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//span[text()='{self.region}']")))
            ##first wait to change region to BE-NL (default)
            self.driver.execute_script("arguments[0].click();", self.driver.find_element(By.XPATH, f"//span[text()='{self.region}']"))
        ##second wait to have the actual results
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@data-testid='result-extras-url-link']")))
        # Locate the button using XPath
        more_results = self.driver.find_element(By.XPATH, "//button[@id='more-results']")
        # Perform a JavaScript click on the button
        self.driver.execute_script("arguments[0].click();", more_results)
        # Wait for expanded results
        elements = WebDriverWait(self.driver, 10).until(
                                                    lambda d: len(d.find_elements(By.XPATH, "//a[@data-testid='result-extras-url-link']")) >= 12
                                                )
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
        self.div_urls = self.soup.find_all("article", {"data-testid": "result"})
        temp_headers = [div.find("h2").text.strip()  for div in self.div_urls]
        temp_urls = [clean_url(div.find("h2").find("a")["href"])  for div in self.div_urls]
        print("main urls before bl:", temp_urls)
        self.search_results = {} 
        {self.search_results.update({clean_url(u): h}) for u, h in zip(temp_urls, temp_headers) if clean_url(u) not in self.search_results and check_blacklist(u) is False} 
        self.driver.quit()
        return self.search_results

    def crawl_urls(self, output_dir = os.path.join(os.path.dirname(__file__), "crawler_output")):### MAJOR ISSUE WITH VAN MOSSEL MB BELGIUM website stuck in page_source
        #experiment: disabling javascript:
        self.options.add_experimental_option("prefs", {"profile.managed_default_content_settings.javascript": 2})
        print(output_dir)
        # creating an instance of Chrome webdriver
        self.driver = webdriver.Chrome(options = self.options)
        company_output_path = os.path.join(output_dir, self.name)
        delete_create_dir(company_output_path)
        for url in self.search_results:
            print("\n*+++++++", url)
            domain_ouput_path = os.path.join(company_output_path, get_domain(url))
            try:
                self.driver.get(url)
            except:
                print(f"URL failed {url} , skipping...")
                continue
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@href]")))
            except:
                print(f"No body or HREF found in {self.driver.current_url} (possibly prevented by a captcha)")
                continue
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            print(0, [x.name for x in soup.find("html").find_all(recursive=False)])
            if not soup.find("body"):
                print("No body found on", url, "skipping...")
                continue
            anchors = prune_urls(url, [u for u in soup.find("body").find_all(href=True)])#changed from soup.find("body").find_all("a", {"href": True}) due to some href being on <link> tags
            clean_create_dir(domain_ouput_path)
            with open(os.path.join(domain_ouput_path, "index.html"), "w", encoding = "utf-8") as f_in:
                f_in.write(self.driver.page_source)
            print("len anchors:", len(anchors))
            print([a["href"] for a in anchors])
            for anchor in anchors:
                print("**********", valid_url(url ,anchor["href"]), "*******\n")
                try:
                    self.driver.get(valid_url(url ,anchor["href"]))
                except:
                    print("failed to get sub url:", anchor["href"])
                    continue
                with open(os.path.join(domain_ouput_path, html_filename(anchor.text)), "w", encoding = "utf-8") as f_in:
                    f_in.write(self.driver.page_source )
        self.driver.quit()
            
if __name__ == "__main__":
    import pandas as pd
    df = pd.read_excel("2kfull.xlsx", sheet_name = "Results")
    companies = df["Company name Latin alphabet"].tolist()
    #
    companies = ["VAMIX"]
    print("hello world")
    companies = [re.sub(r"[^\w\s]", "-", c) for c in companies] # this should be in self.name
    for com in companies:## issue at 660 only works with javascript disabled
        print("Working with", com)
        company = Company(com.lower())
        sample = company.search()
        company.crawl_urls()

    #company = Company("josse locust")
    #sample = company.search()
    #company.crawl_urls()
    #for k, v in sample.items():
