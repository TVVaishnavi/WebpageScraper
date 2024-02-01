from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time


def scrapeData(driver, url):
    driver.get(url)
    container = driver.find_element(By.ID, "page-container")
    questions = container.find_elements(By.CLASS_NAME, "clearfix")

    for quest in questions:
        quest = quest.find_element(By.XPATH, "*")
        items = quest.find_elements(By.XPATH, "*")

        title = scrapeQuestionTitle(items[0])
        print(title)
        # choices = scrapeQuestionDetails(items[1])
        solution = scrapeSolution(items[2])

        # print(solution)


def scrapeQuestionTitle(parentTag: WebElement):
    h4 = parentTag.find_element(By.TAG_NAME, "h4")
    text = h4.get_attribute("innerHTML").split(" | ")
    return text


def scrapeSolution(parentTag: WebElement):
    aTag = parentTag.find_element(By.TAG_NAME, "a")
    aTag.click()
    solutionDivTag = parentTag.find_element(By.CLASS_NAME, "_1bm00l4r")
    res = []
    try:
        res.append(solutionDivTag.find_element(By.TAG_NAME, "strong").text)
    except:
        sols = solutionDivTag.find_elements(By.TAG_NAME, "mjx-assistive-mml")

        for mjx_mml in sols:
            res.append(__scrape_mjx_assistive_mml(mjx_mml))

    return res


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


def __scrape_mjx_assistive_mml(tag: WebElement):
    try:
        frac = tag.find_element(By.TAG_NAME, "mfrac")
        mns = frac.find_elements(By.TAG_NAME, "mn")
        return f"{mns[0].get_attribute('innerHTML')}/{mns[1].get_attribute('innerHTML')}"
    except:
        mn = tag.find_element(By.TAG_NAME, "mn")
        return mn.get_attribute("innerHTML")


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
    # driver.set_window_size(640, 320)
    url = ("https://www.khanacademy.org/test-prep/dpsat-practice-test-01-12/xf042e2c5bc6f4af4:dpsat-practice-test-01"
           "-12/xf042e2c5bc6f4af4:psat-test-sections/a/dpsat--pt1--math--m0")

    scrapeData(driver, url)
    time.sleep(30)
    driver.quit()
