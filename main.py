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

import openpyxl
import time


def scrapeData(driver, url):
    # print(driver, url)
    driver.get(url)
    time.sleep(5)
    container = driver.find_element(By.CLASS_NAME, "_1h1mqh3")
    questions = container.find_elements(By.CLASS_NAME, "clearfix")

    res = []
    print(container)
    print(questions)
    for quest in questions:
        data = []

        quest = quest.find_element(By.XPATH, "*")
        items = quest.find_elements(By.XPATH, "*")

        title = scrapeQuestionTitle(items[0])
        data.append(title)

        q_and_a = scrapeQuestionDetails(items[1])
        # print(q_and_a)
        data.extend(q_and_a)

        solution = scrapeSolution(items[2])
        data.append(solution)

        res.append(data)

    return res


def scrapeQuestionTitle(parentTag: WebElement):
    h4 = parentTag.find_element(By.TAG_NAME, "h4")
    text = h4.get_attribute("innerHTML").split(" | ")
    return text[1]


def scrapeSolution(parentTag: WebElement):
    aTag = parentTag.find_element(By.TAG_NAME, "a")
    aTag.click()
    solutionDivTag = parentTag.find_element(By.CLASS_NAME, "_1bm00l4r")
    res = []
    try:
        res.append(solutionDivTag.find_element(By.TAG_NAME, "strong").get_attribute("innerHTML"))
    except:
        sols = solutionDivTag.find_elements(By.TAG_NAME, "mjx-assistive-mml")

        for mjx_mml in sols:
            res.append(__scrape_mjx_assistive_mml(mjx_mml))

    return ", ".join(res)


def scrapeQuestionDetails(parentTag: WebElement):
    parentTag = (parentTag.find_element(By.CLASS_NAME, "perseus-graded-group").
                 find_element(By.XPATH, "*"))
    paragraphs = parentTag.find_elements(By.XPATH, "*")

    # exp = __scrapeExplanation(parentTag)
    options = __scrapeOptions(paragraphs[-1])
    if len(options) != 4:
        options = [""] * 4

    prompt = {"figure": [], "text": []}
    for para in paragraphs[:-1]:

        div = para.find_element(By.XPATH, "*")
        if div.tag_name == 'table':
            prompt['text'].append(__parseTable(div))

        elif "perseus-block-math" in div.get_attribute("class").strip():
            mjx_mml = div.find_element(By.TAG_NAME, "mjx-assistive-mml")
            prompt['text'].append(__scrape_mjx_assistive_mml(mjx_mml))

        else:
            try:
                fig = div.find_element(By.TAG_NAME, "figure")
                prompt['figure'].append(__scrapeFigure(fig))

            except:
                prompt['text'].append(__parseParagraph(div))

    # details = dict()
    # details['prompt'] = prompt
    # details['options'] = options
    res = []
    res.append("\n".join(prompt['text']).strip())
    res.extend(options)
    return res


def __scrapeOptions(parentTag: WebElement):
    try:
        res = []
        items = parentTag.find_elements(By.TAG_NAME, "li")
        for li in items:
            div = li.find_element(By.TAG_NAME, "button").find_element(By.CLASS_NAME, "perseus-renderer")
            try:
                table = div.find_element(By.TAG_NAME, "table")
                option = __parseTable(table)
            except:
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
    children = tag.find_elements(By.XPATH, "*")
    count = 0
    res = ""
    for c in soup.children:
        # I wonder whether I have to call mjx-assistive-mml func to span tags?
        if isinstance(c, Tag):
            if c.name == 'span':
                html_content = str(c.getText)
                # print(str(c.getText))
                elem = children[count].find_element(By.TAG_NAME, "mjx-assistive-mml")
                res += __scrape_mjx_assistive_mml(elem)
            elif c.name == 'br':
                res += "\n"
            else:
                for ch in c.text:
                    if ch.isascii():
                        res += ch

            count += 1

        elif isinstance(c, NavigableString):
            if c.isspace():
                continue
            for ch in c:
                if ch.isascii():
                    res += ch
        else:
            print("%%%%%%%%%%\tElement of unknown type identified. Review it!\t%%%%%%%%%%%")

    return res


def parseMSUP(tag: WebElement):
    sub_elem = tag.find_elements(By.XPATH, "*")
    vals = []
    for val in sub_elem:
        if val.tag_name == 'mrow':
            for e in val.find_elements(By.XPATH, "*"):
                if e.tag_name == 'mstyle':
                    vals.append(parseMSTYLE(e))
                else:
                    vals.append(e.get_attribute("innerHTML"))
        else:
            vals.append(val.get_attribute("innerHTML"))
    return "".join(vals[:-1]) + "^" + vals[-1]


def parseMSTYLE(tag: WebElement):
    try:
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
    except:
        return tag.text


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

                elif e.tag_name == 'mtable':  # WTF is this?
                    res += parseMTABLE(e)

                else:
                    res += e.get_attribute("innerHTML")
        # trouble over here
        if not row.isspace():
            res += row + "\n"

    return res


def __parseTable(tag: WebElement):
    res = ""
    thead = tag.find_element(By.TAG_NAME, "thead")
    tbody = tag.find_element(By.TAG_NAME, "tbody")
    for th in thead.find_elements(By.TAG_NAME, "th"):
        res += th.get_attribute('innerHTML') + ", "

    res += '\n'

    for tr in tbody.find_elements(By.TAG_NAME, "tr"):
        for td in tr.find_elements(By.TAG_NAME, "td"):
            try:
                mjx_mml = td.find_element(By.TAG_NAME, "mjx-assistive-mml")
                res += __scrape_mjx_assistive_mml(mjx_mml) + ", "
            except:
                res += td.text + ", "
        res += '\n'

    return res.strip()


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

        elif e.tag_name == 'mover':
            for elem in e.find_element(By.XPATH, "*").find_elements(By.XPATH, "*"):
                res += elem.get_attribute("innerHTML")

        elif e.tag_name == 'mrow':
            for ch in e.find_elements(By.XPATH, "*"):
                if ch.tag_name == 'mstyle':
                    res += parseMSTYLE(ch)
                else:
                    res += ch.get_attribute("innerHTML")

        elif e.tag_name == 'msqrt':
            res += "√" + e.find_element(By.XPATH, "*").get_attribute("innerHTML")

        else:
            res += e.get_attribute("innerHTML")

    return res


def __scrapeFigure(tag: WebElement):
    img = tag.find_element(By.TAG_NAME, "img")
    alt_text = img.get_attribute("alt")
    img_link = img.get_attribute("src")
    return [img_link, alt_text]


def writeData(file_path, data, test_name, module_name):
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active

    for row in data:
        sheet.append([test_name, module_name] + row)

    sheet.append([""] * 9)
    wb.save(file_path)


def scrapeAndWrite(path, links):
    t = links[0].split("/")[-2].split("-")
    test_name = t[0].upper() + t[2].split("-")[0]
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    driver.get(links[0])
    link_to_test_home = driver.find_element(By.CLASS_NAME, "_dwmetq").get_attribute("href")
    driver.get(link_to_test_home)
    items = driver.find_element(By.CLASS_NAME, "_37mhyh").find_elements(By.XPATH, "*")[3:]
    urls = []
    for i in range(len(items)):
        urls.append(items[i].find_element(By.TAG_NAME, 'a').get_attribute("href"))

    driver.get(links[1])
    link_to_test_home = driver.find_element(By.CLASS_NAME, "_dwmetq").get_attribute("href")

    driver.get(link_to_test_home)
    item = driver.find_element(By.CLASS_NAME, "_37mhyh").find_elements(By.XPATH, "*")[-1]
    urls.append(item.find_element(By.TAG_NAME, 'a').get_attribute("href"))
    [print(url) for url in urls]

    for i in range(len(urls)):
        data = scrapeData(driver, urls[i])
        print("$" * 50)
        print(data)
        print("&" * 50)
        writeData(file_path, data, test_name, f"M{i + 1}")

    driver.quit()


if __name__ == '__main__':
    # driver.set_window_size(640, 320)
    file_path = "output/Khan_academy.xlsx"
    links = [
        # ("https://www.khanacademy.org/test-prep/dsat--practice-test--01-11/",
        #  "https://www.khanacademy.org/test-prep/dsat--practice-test--01-12/"),
        # ("https://www.khanacademy.org/test-prep/dsat--practice-test--02-11/",
        #  "https://www.khanacademy.org/test-prep/dsat--practice-test--02-12/"),
        # ("https://www.khanacademy.org/test-prep/dsat--practice-test--03-11/",
        #  "https://www.khanacademy.org/test-prep/dsat--practice-test--03-12/"),
        # ("https://www.khanacademy.org/test-prep/dsat--practice-test--04-11/",
        #  "https://www.khanacademy.org/test-prep/dsat--practice-test--04-12/"),
        ("https://www.khanacademy.org/test-prep/dpsat-practice-test-01-11/",
         "https://www.khanacademy.org/test-prep/dpsat-practice-test-01-12/")
    ]

    for link_pair in links:
        scrapeAndWrite(file_path, link_pair)
