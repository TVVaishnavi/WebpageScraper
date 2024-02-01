from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import NoSuchElementException
import time


def scrapeData(driver, url):
    driver.get(url)
    questions = driver.find_elements(By.CLASS_NAME, "clearfix")

    for quest in questions:
        quest = quest
        quest = quest.find_element(By.CLASS_NAME, "perseus-renderer")
        item1 = quest.find_element(By.XPATH, '//div[@data-perseus-paragraph-index="0"]')
        item2 = quest.find_element(By.XPATH, '//div[@data-perseus-paragraph-index="1"]')
        item3 = quest.find_element(By.XPATH, '//div[@data-perseus-paragraph-index="2"]')

        title = scrapeQuestionTitle(item1)
        choices = scrapeQuestionDetails(item2)
        print("%%" + "*" * 20 + "%%")
        print(quest.find_element(By.XPATH, '//div[@data-perseus-paragraph-index="0"]').find_element(By.TAG_NAME,
                                                                                                    "h4").text)
        # print(title)
        # print(choices)
        print("%%" + "*" * 20 + "%%\n")


def scrapeQuestionTitle(parentTag: WebElement):
    h4 = parentTag.find_element(By.TAG_NAME, "h4")
    text = h4.text.split(" | ")
    return text


def scrapeQuestionDetails(parentTag: WebElement):
    parentTag = parentTag.find_element(By.CLASS_NAME, "perseus-graded-group")
    c = 0
    sections = []
    tag = parentTag.find_element(By.XPATH, f"//div[@data-perseus-paragraph-index='{c}']")
    while tag:
        sections.append(tag)
        c += 1
        try:
            tag = parentTag.find_element(By.XPATH, f"//div[@data-perseus-paragraph-index='{c}']")
        except NoSuchElementException:
            break

    text = ""
    options = None
    figure = None
    res = []

    for tag in sections:
        try:
            child = tag.find_element(By.TAG_NAME, "fieldset")
            options = scrapeChoices(child)
            res.append(options)
        except NoSuchElementException:
            try:
                child = tag.find_element(By.TAG_NAME, "figure")
                figure = scrapeFigure(child)
                res.append(figure)
            except NoSuchElementException:
                text += scrapeText(tag)
                res.append(text)

    return res


def scrapeSolution():
    ...


def scrapeChoices(tag: WebElement):
    res = []
    items = tag.find_element(By.TAG_NAME, "ul").find_elements(By.TAG_NAME, "li")
    for item in items:
        res.append(item.find_element(By.TAG_NAME, "mjx-assistive-mml").text)

    return res


def scrapeFigure(tag: WebElement):
    img = tag.find_element(By.TAG_NAME, "img")
    alt_text = img.get_attribute("alt")
    img_link = img.get_attribute("src")
    return [img_link, alt_text]


def scrapeText(tag: WebElement):
    text = tag.text
    return text


if __name__ == '__main__':
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    url = ("https://www.khanacademy.org/test-prep/dpsat-practice-test-01-12/xf042e2c5bc6f4af4:dpsat-practice-test-01-12"
           "/xf042e2c5bc6f4af4:psat-test-sections/a/dpsat--pt1--math--m0")

    # scrapeData(driver, url)
    driver.get(url)
    e = driver.find_element(By.XPATH,
                            "/html/body/div/div[3]/div/div[2]/div/div/main/div[2]/div/div/div[1]/div/div/div/div[2]/div/div[1]/div/div[2]/div/div/div/div/div[2]/div")
    print(e.text)
    path = '/html/body/div/div[3]/div/div[2]/div/div/main/div[2]/div/div/div[1]/div/div/div/div[2]/div/div[1]/div/div[2]/div/div/div/div/div[3]/div/div/div/fieldset/ul/li[1]/div/div/button/div/span/div[2]/div/div/div/div/span/span/mjx-container/mjx-assistive-mml/math'
    f = driver.find_element(By.XPATH, path)
    print("%%%% " + f.text + " ****")
    # time.sleep(10)
    driver.quit()
