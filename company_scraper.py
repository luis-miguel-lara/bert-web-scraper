from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep

class Company:
    """
    This class has the goal to scrape company information
    """
    def __init__(self, name, region = "be-nl"):
        self.name = name
        self.region = region
    def search(self): 
        """
        The search function has the goal to find the results on the selected engine (by deafault DuckDuckGo)
        """
        # instance of Options class
        self.options = Options()
        # parameter change on options (headless) attribute
        self.options.add_argument("--headless")
        #
        self.options.add_argument("disable-infobars")
        self.options.add_argument("--disable-extensions")
        # creating an instance of Chrome webdriver
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
        self.search_results = {div.find("h2").text: div.find("h2").find("a")["href"] for div in self.div_urls}# if div.find("h2") is not None
        self.driver.quit()
        return self.search_results

if __name__ == "__main__":
    print(Company("pepsi").search())