from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.common.exceptions  import NoAlertPresentException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
#from crawler_utils.scraping_utils import clean_url, get_domain, fix_href, check_blacklist, regex_find_urls, valid_url
from scraping_utils import clean_url, get_domain, fix_href, check_blacklist, regex_find_urls, valid_url
#from crawler_utils.file_utils import clean_create_dir, clean_filename, delete_create_dir, html_filename
from file_utils import clean_create_dir, clean_filename, delete_create_dir, html_filename
from time import sleep
import os

cookies_xpath= ["reject all", "functional cookies", "weigeren", "fermer",  "decline",
                "ik begrijp het", "alles accepteren", "voorkeur opslaan", "alle cookies",
                "i accept", "all cookies", "allow all cookies", "allow all", "akkord en sluiten", "alle cookies",
                "cookies accepteren", "accepteren", "aanvaarden", "accept cookies", "accept all cookies",  "use necessary cookies", 
                "consent", "tout accepter", "understood"] #//tag[matches(@title,'empire burlesque','i')] # //td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'test account')] ## replace text with right parameter


class Crawler(Chrome):
    def __init__(self, search_string=str, region=None):
        """
        """
        self.search_string = search_string
        self.region = region
        self.get_urls(self.search_string)


    def start_driver(self, mode=None):
        """
        """
        # instance of Options class
        self.options = Options()
        self.options.add_argument("log-level=3")
        if mode == "headless":
            #if mode or other mode (headless for duckduckgo)
            # parameter change on options (headless) attribute
            self.options.add_argument("--headless")
            #self.options.add_argument("disable-infobars")##may this causes error 403
            #self.options.add_argument("--disable-extensions")
        super().__init__(service= ChromeService(ChromeDriverManager().install()),  options=self.options)
        #webdriver.Chrome(service = ChromeService(ChromeDriverManager().install()), options = self.options)


    def get_urls(self, name):
        """
        """
        self.start_driver(mode="headless")
        self.get("https://duckduckgo.com")
        if self.region is not None:
            if len(self.search_string.replace(" ", ""))<7 or len(self.search_string.split())==1:
                WebDriverWait(self, 10).until(EC.element_to_be_clickable((By.ID, "search_form_input_homepage"))).send_keys(f"{self.search_string} belgië bedrijf")
            else:
                WebDriverWait(self, 10).until(EC.element_to_be_clickable((By.ID, "search_form_input_homepage"))).send_keys(self.search_string)
            WebDriverWait(self, 10).until(EC.element_to_be_clickable((By.ID, "search_button_homepage"))).click()
            #WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//div[@class='dropdown--region']"))).click()
            self.find_element(By.CLASS_NAME, "search-filters-wrap").find_element(By.CLASS_NAME, "dropdown__button").click()
            WebDriverWait(self, 10).until(EC.element_to_be_clickable((By.XPATH, f"//a[@data-id='{self.region}']")))
            WebDriverWait(self, 10).until(EC.element_to_be_clickable((By.ID, "links")))
            ##first wait to change region to BE-NL (default)
            self.execute_script("arguments[0].click();", self.find_element(By.XPATH, f"//a[@data-id='{self.region}']"))
        ##second wait to have the actual results
        WebDriverWait(self, 10).until(EC.element_to_be_clickable((By.ID, "links"))) 
        self.soup = BeautifulSoup(self.page_source, "html.parser")
        self.div_urls = self.soup.find("div", {"id": "links"}).find_all(recursive=False)
        self.div_urls = [d for d in self.div_urls if d["class"][0] == "nrn-react-div"]
        temp_headers = [div.find("h2").text.strip()  for div in self.div_urls]
        temp_urls = [clean_url(div.find("h2").find("a")["href"])  for div in self.div_urls]
        self.search_results = {} 
        {self.search_results.update({clean_url(u): h}) for u, h in zip(temp_urls, temp_headers) if clean_url(u) not in self.search_results and check_blacklist(u) is False} 
        print(self.search_results)
        self.quit()
        return self.search_results

   
    def crawl_urls(self, output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "crawler_output")):
        """
        """
        self.start_driver()
        self.implicitly_wait(10)
        company_output_path = os.path.join(output_dir, self.search_string)
        delete_create_dir(company_output_path)
        for url in self.search_results:
            print("\n*+++++++", url)
            domain_ouput_path = os.path.join(company_output_path, get_domain(url))
            clean_create_dir(domain_ouput_path)
            try:
                self.get(url)
            except Exception as err:
                print("failed 1", url, "error:", err)
                continue
            try:
                self.switch_to.alert.dismiss()
            except NoAlertPresentException:
                print('No alert present')
            with open(os.path.join(domain_ouput_path, "index.html"), "w", encoding = "utf-8") as f_in:
                current_html = self.execute_script("return document.body.innerHTML")
                f_in.write(current_html)
                #f_in.write(self.driver.page_source)
            current_html = self.execute_script("return document.body.innerHTML")
            #soup = BeautifulSoup(self.driver.page_source, "html.parser")
            soup = BeautifulSoup(current_html, "html.parser")
            if soup.find("body") is None:
                anchors = [{"href": u} for u in regex_find_urls(current_html) if valid_url(url, u)]
                #anchors = [{"href": u} for u in regex_find_urls(self.driver.page_source) if valid_url(url, u)]
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
                    self.get(valid_url(url ,anchor["href"]))
                except:
                    print("failed anchor:", url, anchor["href"])
                    break
                if self.page_source.startswith("<?xml") or self.page_source.startswith("<svg"):
                        continue
                try:
                    current_html = self.execute_script("return document.body.innerHTML")
                except:
                    continue
                with open(os.path.join(domain_ouput_path, html_filename(anchor.text if "text" in dir(anchor) else anchor["href"])), "w", encoding = "utf-8") as f_in:
                    f_in.write(current_html)
                if "404" in self.current_url and "404" not in url: #after the file creation to leave the 404.html as proof of blockage
                    print("++404 in updated url:", self.current_url, "original:", url)
                    break
        self.quit()

if __name__ == "__main__":
    crawler = Crawler("burea van dijk", region="be-nl")
    crawler.crawl_urls()