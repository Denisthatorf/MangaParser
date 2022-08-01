from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException      
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.firefox.options import Options

from bs4 import BeautifulSoup
import pyautogui

import time
import os
import shutil

OUT_DIR = os.path.join(os.getcwd(), 'out')
LINKS_FILE = os.path.join(OUT_DIR, 'manga_links.txt')

PORT = 5050
SERVER = '127.0.0.1'
ADDR = (SERVER, PORT)
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
SITE_URL = 'https://mangalib.me'

def check_exists_by_xpath(xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True      

def select_tom_and_chapter(line):
    import re
    tom_and_chapter = re.findall(r'[\d\.]+',line)
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

def get_manga_links(url, chapter_start, chapter_finish):
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
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_UP)
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_UP)

    #Write links to file
    with open(LINKS_FILE, 'a') as file:
        for key, url in dict_of_links.items():
            file.write(url)
            file.write('\n')

    return dict_of_links

def get_manga_images(dict_of_links):
    isNotPrepared  = True

    for key, link in dict_of_links.items():
        try:
            driver.set_page_load_timeout(3)
            driver.get(url= f"{SITE_URL}{link}")
        except Exception:
            pass

        if isNotPrepared:
            eighten_plus_caution_continue()
            set_setting_to_vertical_mode()
            time.sleep(3)
            isNotPrepared = False

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

    driver = webdriver.Firefox(executable_path='/home/denis/Projects/Python/mangalibParser/drivers/geckodriver', options=options)

    try:
        driver.set_page_load_timeout(10)
        driver.get(url=url)    
    except:
        pass

    links = get_manga_links(url, 0, 100)
    sorted_links = {key: links[key] for key in sorted(links.keys(), key = lambda ele: int(ele[0]) * 100 + int(ele[1]))}
    get_manga_images(sorted_links)

except Exception as ex:
    print(ex)
finally:
    time.sleep(1)
    print('Disconnected')

    #driver.close()
    driver.quit()