from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from bs4.element import Tag
from bs4.element import NavigableString

import time


def scrapeData(driver, url):
    driver.get(url)
    container = driver.find_element(By.ID, "page-container")
    questions = container.find_elements(By.CLASS_NAME, "clearfix")

    res = []

    for quest in questions:
        data = dict()

        quest = quest.find_element(By.XPATH, "*")
        items = quest.find_elements(By.XPATH, "*")

        title = scrapeQuestionTitle(items[0])
        data['title'] = title

        details = scrapeQuestionDetails(items[1])
        data['details'] = details

        solution = scrapeSolution(items[2])
        data['solution'] = solution

        [print(key, data[key]) for key in data]
        res.append(data)

    return res


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
    parentTag = (parentTag.find_element(By.CLASS_NAME, "perseus-graded-group").
                 find_element(By.XPATH, "*"))
    paragraphs = parentTag.find_elements(By.XPATH, "*")

    # exp = __scrapeExplanation(parentTag)
    options = __scrapeOptions(paragraphs[-1])
    prompt = {"figure": [], "text": []}
    for para in paragraphs[:-1]:

        div = para.find_element(By.XPATH, "*")
        if "perseus-block-math" in div.get_attribute("class").strip():
            mjx_mml = div.find_element(By.TAG_NAME, "mjx-assistive-mml")
            prompt['text'].append(__scrape_mjx_assistive_mml(mjx_mml))

        else:
            try:
                fig = div.find_element(By.TAG_NAME, "figure")
                prompt['figure'].append(__scrapeFigure(fig))

            except:
                prompt['text'].append(__parseParagraph(div))

    details = dict()
    details['prompt'] = prompt
    details['options'] = options

    return details


def __scrapeOptions(parentTag: WebElement):
    try:
        res = []
        items = parentTag.find_elements(By.TAG_NAME, "li")
        for li in items:
            div = li.find_element(By.TAG_NAME, "button").find_element(By.CLASS_NAME, "perseus-renderer")
            try:
                block_math = div.find_element(By.CLASS_NAME, "perseus-block-math")
                option = __parseMathBlock(block_math)
            except:
                para = div.find_element(By.CLASS_NAME, "paragraph").find_element(By.CLASS_NAME, "paragraph")
                option = __parseParagraph(para)

            res.append(option)

        return res

    except:
        # Not an objective type question
        return []


def __scrapeExplanation(tag: WebElement):
    button = tag.find_element(By.CLASS_NAME, "_oak3yy")
    button.click()
    divTag = (tag.find_elements(By.XPATH, "*")[-1]
              .find_element(By.TAG_NAME, "div"))
    # print(divTag.get_attribute("outerHTML"))
    divs = divTag.find_elements(By.XPATH, "*")
    res = []

    for div in divs:
        # res.append(div.text)
        print(div.find_element(By.CLASS_NAME, "paragraph").get_attribute("innerHTML"))
    print(res)
    return res


def __parseMathBlock(tag: WebElement):
    mjx = tag.find_element(By.TAG_NAME, "mjx-assistive-mml")
    res = __scrape_mjx_assistive_mml(mjx)

    return res


def __parseParagraph(tag: WebElement):
    content = tag.get_attribute("innerHTML")
    soup = BeautifulSoup(content, "html.parser")
    res = ""
    for c in soup.children:
        if isinstance(c, Tag):
            for ch in c.text:
                if ch.isascii():
                    res += ch
        elif isinstance(c, NavigableString):
            for ch in c:
                if ch.isascii():
                    res += ch
        else:
            print("%%%%%%%%%%\tElement of unknown type identified. Review it!\t%%%%%%%%%%%")

    return res


def parseMSUP(tag: WebElement):
    sub_elem = tag.find_elements(By.XPATH, "*")
    vals = [val.get_attribute("innerHTML") for val in sub_elem]
    return "^".join(vals)


def parseMSTYLE(tag: WebElement):
    fraction_components = tag.find_element(By.TAG_NAME, "mfrac").find_elements(By.XPATH, "*")
    vals = []
    for comp in fraction_components:
        if comp.tag_name == 'mrow':
            val = ""
            for term in comp.find_elements(By.XPATH, "*"):
                val += term.get_attribute("innerHTML")
            vals.append("(" + val + ")")
        else:
            vals.append(comp.get_attribute("innerHTML"))

    return "/".join(vals)


def parseMTABLE(tag: WebElement):
    res = ""
    for mtr in tag.find_elements(By.TAG_NAME, "mtr"):
        row = ""
        for mtd in mtr.find_elements(By.TAG_NAME, "mtd"):
            for e in mtd.find_elements(By.XPATH, "*"):

                if e.tag_name == "msup":
                    res += parseMSUP(e)

                elif e.tag_name == 'mstyle':
                    res += parseMSTYLE(e)

                elif e.tag_name == 'mtable':
                    res += parseMTABLE(e)

                else:
                    res += e.get_attribute("innerHTML")
        res += row + "\n"

    return res


def __scrape_mjx_assistive_mml(tag: WebElement):
    res = ""
    elements = tag.find_element(By.TAG_NAME, "math").find_elements(By.XPATH, "*")
    for e in elements:
        if e.tag_name == "msup":
            res += parseMSUP(e)

        elif e.tag_name == 'mstyle':
            res += parseMSTYLE(e)

        elif e.tag_name == 'mtable':
            res += parseMTABLE(e)

        else:
            res += e.get_attribute("innerHTML")

    return res


def __scrapeFigure(tag: WebElement):
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

    data = scrapeData(driver, url)
    driver.quit()
