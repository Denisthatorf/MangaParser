from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException      
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from bs4 import BeautifulSoup
import pyautogui

import time
import os
import shutil
import sys

OUT_DIR = os.path.join(os.getcwd(), 'out')
LINKS_FILE = os.path.join(OUT_DIR, 'manga_links.txt')
DRIVER_PATH = os.path.join(os.getcwd(), 'drivers/geckodriver')
SITE_URL = 'https://mangalib.me'

def check_exists_by_xpath(xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True      

def select_tom_and_chapter(line):
    import re
    tom_and_chapter = re.findall(r'\d+(?:\.\d+)?',line)
    
    for i in range(0, len(tom_and_chapter)):
        tom_and_chapter[i] = float(tom_and_chapter[i])

    return tuple(tom_and_chapter)

def click_uncklicable_item(item):
    action = webdriver.common.action_chains.ActionChains(driver)
    action.move_to_element_with_offset(item, 0.3, 0.3)
    action.click()
    action.perform()

def eighten_plus_caution_continue():
    try:
        checkbox = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//input[@class="control__input"]'))
        )
        click_uncklicable_item(checkbox)

        button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//button[@class="button button_md button_orange reader-caution-continue"]'))
        )
        button.click()
    except Exception as ex:
        pass

def set_setting_to_vertical_mode():
    settings = driver.find_element(By.XPATH, '//div[@class="reader-header__wrapper"]').find_element(By.XPATH, '//i[@class="fa fa-cog"]')
    click_uncklicable_item(settings)

    popup = driver.find_element(By.XPATH, '//div[@class="popup__content"]')

    horizontal_mod = popup.find_element( By.XPATH, './/label[contains(text(),"Вертикальный")]')
    horizontal_mod.click()

    close_pop_up_btn = popup.find_element(By.XPATH, './/div[@class="modal__close"]')
    click_uncklicable_item(close_pop_up_btn)

def prepareSiteForParsing(anyChapterLink):
    try:
        driver.set_page_load_timeout(3)
        driver.get(anyChapterLink)
    except Exception:
        pass

    eighten_plus_caution_continue()
    set_setting_to_vertical_mode()

    time.sleep(3)

def create_image (fullpath, img):
    with open(fullpath, 'wb') as file:
            shutil.copyfileobj(img.raw, file)
            print(f"Create image: {fullpath}")

#-----------------

def preStart():
    #Clear and create folder for outputed files
    if not os.path.isdir(OUT_DIR):
        os.mkdir(OUT_DIR)
    else:
        shutil.rmtree(OUT_DIR) 
        os.mkdir(OUT_DIR)

    #create file for manga links
    
    with open(LINKS_FILE, 'wb') as file:
        file.truncate(0)

def get_manga_links(url):
    #Go to all manga links tab
    chapters_tab = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//li[@data-key='chapters']"))
    )
    chapters_tab.click()

    driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
    
    dict_of_links = {}

    #Get all links
    while True:
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        chapter_items = soup.find_all('div', class_='vue-recycle-scroller__item-view')

        for item in chapter_items[::-1]:
            link = item.find('a', class_='link-default')
            tom_and_ch = select_tom_and_chapter(link.text)
            dict_of_links[tom_and_ch] = link.get('href')
        
        pos_y = driver.execute_script("return window.pageYOffset;")
        if pos_y == 0:
            break
        else:            
            action = ActionChains(driver)
            action.send_keys(Keys.PAGE_UP).perform();

    #Write links to file
    with open(LINKS_FILE, 'a') as file:
        for key, url in dict_of_links.items():
            file.write(url)
            file.write('\n')

    return dict_of_links

def get_manga_images(dict_of_links):
    
    for key, link in dict_of_links.items():
        prepareSiteForParsing(f"{SITE_URL}{link}")
        break

    for key, link in dict_of_links.items():
        try:
            driver.set_page_load_timeout(3)
            driver.get(url= f"{SITE_URL}{link}")
        except Exception:
            pass

        img_wraps = driver.find_elements(By.CLASS_NAME, 'reader-view__wrap')

        for count, img_wrap in enumerate(img_wraps):
            driver.execute_script("return arguments[0].scrollIntoView();", img_wrap)
            driver.execute_script("window.scrollBy(0 , 500);")

            save_img_action = ActionChains(driver)
            save_img_action.move_to_element(img_wrap).perform()
            save_img_action.context_click().perform()     

            for i in range(2):
                pyautogui.keyDown('down')
                pyautogui.keyUp('down')

            pyautogui.keyDown('return')
            pyautogui.keyUp('return')
            
            pyautogui.keyDown('return')
            pyautogui.keyUp('return')

            pyautogui.write(f"Tom {key[0]} Chapter {key[1]} - {count}")


url = input("Enter url to manga: ")    

# example:https://mangalib.me/tokkiwa-heugpyobeom-ui-gongsaeng-gwangye?section=chapters

try:
    preStart()

    options = Options()
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", OUT_DIR)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")


    driver = webdriver.Firefox(executable_path=DRIVER_PATH, options=options)

    driver.get(url=url)    
    links = get_manga_links(url)
    links = {key: links[key] for key in sorted(links.keys(), key = lambda ele: ele[0] * 100 + ele[1])}
    get_manga_images(links)

except Exception as ex:
    print(ex)

    #driver.close()
    driver.quit()