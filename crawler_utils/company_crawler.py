from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from crawler_utils.scraping_utils import clean_url, get_domain, fix_href, check_blacklist, regex_find_urls, valid_url
from crawler_utils.file_utils import clean_create_dir, clean_filename, delete_create_dir, html_filename
from time import sleep
import os


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
    def __init__(self, name, region = "be-nl"):
        self.name = clean_filename(name)
        self.region = region
        # instance of Options class
        self.options = Options()
        self.options.add_argument("log-level=3")
        # parameter change on options (headless) attribute
        #self.options.add_argument("--headless")
        #self.options.add_argument("disable-infobars")##may this causes error 403
        #self.options.add_argument("--disable-extensions")
        
    def search(self): 
        """
        The search function has the goal to find the results on the selected engine (by deafault DuckDuckGo)
        """
        self.driver = webdriver.Chrome(service = ChromeService(ChromeDriverManager().install()), options = self.options)
        self.driver.get("https://duckduckgo.com")
        if self.region is not None:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "search_form_input_homepage"))).send_keys(self.name)
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "search_button_homepage"))).click()
            #WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='dropdown--region']"))).click()
            self.driver.find_element(By.CLASS_NAME, "search-filters-wrap").find_element(By.CLASS_NAME, "dropdown__button").click()
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//a[@data-id='{self.region}']")))
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "links")))
            ##first wait to change region to BE-NL (default)
            self.driver.execute_script("arguments[0].click();", self.driver.find_element(By.XPATH, f"//a[@data-id='{self.region}']"))
        ##second wait to have the actual results
        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, "links"))) 
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
        self.div_urls = self.soup.find("div", {"id": "links"}).find_all(recursive=False)
        self.div_urls = [d for d in self.div_urls if d["class"][0] == "nrn-react-div"]
        temp_headers = [div.find("h2").text.strip()  for div in self.div_urls]
        temp_urls = [clean_url(div.find("h2").find("a")["href"])  for div in self.div_urls]
        self.search_results = {} 
        {self.search_results.update({clean_url(u): h}) for u, h in zip(temp_urls, temp_headers) if clean_url(u) not in self.search_results and check_blacklist(u) is False} 
        print(self.search_results)
        self.driver.quit()
        return self.search_results

    def crawl_urls(self, output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "crawler_output")):
        print(output_dir)
        # creating an instance of Chrome webdriver
        self.driver = webdriver.Chrome(service = ChromeService(ChromeDriverManager().install()), options = self.options)
        self.driver.implicitly_wait(10)
        company_output_path = os.path.join(output_dir, self.name)
        delete_create_dir(company_output_path)
        for url in self.search_results:
            print("\n*+++++++", url)
            domain_ouput_path = os.path.join(company_output_path, get_domain(url))
            clean_create_dir(domain_ouput_path)
            try:
                self.driver.get(url)
            except:
                print("failed 1")
                continue
            with open(os.path.join(domain_ouput_path, "index.html"), "w", encoding = "utf-8") as f_in:
                f_in.write(self.driver.page_source)
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            if soup.find("body") is None:
                anchors = [{"href": u} for u in regex_find_urls(self.driver.page_source) if valid_url(url, u)]
            else:
                anchors = [u for u in soup.find("body").find_all("a", {"href": True}) if valid_url(url, u["href"]) and len(u.text.strip())> 0]
            print("Total anchors:", len(anchors))
            #print([x["href"] for x in soup.find("body").find_all("a", {"href": True})])
            temp_hrefs = set()
            for i, anchor in enumerate(anchors):
                if anchor["href"] in temp_hrefs or "?" in anchor["href"]:
                    continue
                temp_hrefs.add(anchor["href"])
                print("**********", valid_url(url ,anchor["href"]), "*******\n")
                try:
                    self.driver.get(valid_url(url ,anchor["href"]))
                except:
                    print("failed 2")
                    break
                with open(os.path.join(domain_ouput_path, html_filename(anchor.text if "text" in dir(anchor) else anchor["href"])), "w", encoding = "utf-8") as f_in:
                    f_in.write(self.driver.page_source)
                if "404" in self.driver.current_url and "404" not in url: #after the file creation to leave the 404.html as proof of blockage
                    print("++", self.driver.current_url)
                    break
        self.driver.quit()

if __name__ == "__main__":
    import pandas as pd
    df = pd.read_excel("Export 21_02_2023 21_42.xlsx", sheet_name = "Results")
    companies = df["Company name Latin alphabet"].tolist()
    for com in companies[317:400]:#### code to add pages found in previous company ## A URL should belong at most to 1 company, no more ### #avoid get requests, urls that have ? ### click cookies/bot buttons I accept/refuse all/etc
        print("Working with", com)
        company = Company(com.lower())
        sample = company.search()
        company.crawl_urls()

    #company = Company("josse locust")
    #sample = company.search()
    #company.crawl_urls()
    #for k, v in sample.items():
    #    print(k, "\n", v, "\n*******")