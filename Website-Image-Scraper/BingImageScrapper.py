# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 13:01:02 2020

@author: OHyic
"""
#import selenium drivers
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException       

#import helper libraries
import time
import urllib.request
import os
import requests
import io
from PIL import Image

#custom patch libraries
import patch 

class BingImageScraper():
    def __init__(self,webdriver_path,image_path, search_key="cat",number_of_images=1,headless=False,min_resolution=(0,0),max_resolution=(1920,1080)):
        #check parameter types
        image_path = os.path.join(image_path, search_key)
        if (type(number_of_images)!=int):
            print("[Error] Number of images must be integer value.")
            return
        if not os.path.exists(image_path):
            print("[INFO] Image path not found. Creating a new folder.")
            os.makedirs(image_path)
        #check if chromedriver is updated
        while(True):
            try:
                #try going to www.Bing.com
                options = Options()
                if(headless):
                    options.add_argument('--headless')
                driver = webdriver.Chrome(webdriver_path, chrome_options=options)
                driver.set_window_size(1400,1050)
                driver.get("https://www.Bing.com")
                break
            except:
                #patch chromedriver if not available or outdated
                try:
                    driver
                except NameError:
                    is_patched = patch.download_lastest_chromedriver()
                else:
                    is_patched = patch.download_lastest_chromedriver(driver.capabilities['version'])
                if (not is_patched): 
                    exit("[ERR] Please update the chromedriver.exe in the webdriver folder according to your chrome version:https://chromedriver.chromium.org/downloads")
                    
        self.driver = driver
        self.search_key = search_key
        self.number_of_images = number_of_images
        self.webdriver_path = webdriver_path
        self.image_path = image_path
        # self.url = "https://www.Bing.com/search?q=%s&source=lnms&tbm=isch&sa=X&ved=2ahUKEwie44_AnqLpAhUhBWMBHUFGD90Q_AUoAXoECBUQAw&biw=1920&bih=947"%(search_key)
        self.url = "https://www.bing.com/images/search?view=detailV2&insightstoken=bcid_S8T7-Bc3-0IE7g*ccid_xPv4Fzf7&form=SBIVSP&iss=SBIUPLOADGET&sbisrc=ImgDropper&idpbck=1&sbifsz=4000+x+3000+%c2%b7+35.99+kB+%c2%b7+png&sbifnm=MicrosoftTeams-image.png&thw=4000&thh=3000&ptime=998&dlen=49132&expw=692&exph=519&selectedindex=0&id=-1431471340&ccid=xPv4Fzf7&vt=2&sim=1"
        self.headless=headless
        self.min_resolution = min_resolution
        self.max_resolution = max_resolution
        
    def find_image_urls(self):
        """
            This function search and return a list of image urls based on the search key.
            Example:
                Bing_image_scraper = BingImageScraper("webdriver_path","image_path","search_key",number_of_photos)
                image_urls = Bing_image_scraper.find_image_urls()
                
        """
        print("[INFO] Scraping for image link... Please wait.")
        image_urls=[]
        count = 0
        missed_count = 0
        self.driver.get(self.url)
        time.sleep(3)
        indx = 1
        while self.number_of_images > count:
            try:
                #find and click image
                print("[INFO] Getting img src link")
                imgurl = self.driver.find_element_by_xpath('//*[@class="tab-content vsi"]/ul[1]/li[1]/div[1]/div[1]/div[1]/div[1]/div[1]/ul[1]/li[%s]/div[1]/div[1]/div[1]/div[1]/a[1]/img'%(str(indx)))
                src_link = imgurl.get_attribute('src')
                missed_count = 0 
            except Exception:
                print("[-] Unable to get src_link for this photo.")
                missed_count = missed_count + 1
                if (missed_count>10):
                    print("[INFO] No more photos.")
                    break
                 
            try:
                time.sleep(1)
                if(("http" in  src_link) and (not "encrypted" in src_link)):
                    print("[INFO] %d. %s"%(count,src_link))
                    image_urls.append(src_link)
                    count +=1
            except Exception:
                print("[INFO] Unable to go into src link")   
                
            try:
                #BUG: Does not really scroll down the page for more images
                #TODO: fix bug to scroll and load more images for scraping
                #scroll page to load next image
                if(count%4==0):
                    self.driver.execute_script("window.scrollTo(0, "+str(indx*60)+");")
                print("[INFO] Loading more photos")
                time.sleep(5)
            except Exception:  
                time.sleep(1)
            indx += 1

        
        self.driver.quit()
        print("[INFO] Bing search ended")
        return image_urls

    def save_images(self,image_urls):
        #save images into file directory
        """
            This function takes in an array of image urls and save it into the prescribed image path/directory.
            Example:
                Bing_image_scraper = BingImageScraper("webdriver_path","image_path","search_key",number_of_photos)
                image_urls=["https://example_1.jpg","https://example_2.jpg"]
                Bing_image_scraper.save_images(image_urls)
                
        """
        print("[INFO] Saving Image... Please wait...")
        for indx,image_url in enumerate(image_urls):
            try:
                print("[INFO] Image url:%s"%(image_url))
                search_string = ''.join(e for e in self.search_key if e.isalnum())
                image = requests.get(image_url,timeout=5)
                if image.status_code == 200:
                    with Image.open(io.BytesIO(image.content)) as image_from_web:
                        try:
                            # filename = "%s%s.%s"%(search_string,str(indx),image_from_web.format.lower())
                            filename = "%s%s.%s"%(search_string,str(indx),'png')
                            image_path = os.path.join(self.image_path, filename)
                            print("[INFO] %d .Image saved at: %s"%(indx,image_path))
                            image_from_web.save(image_path)
                        except OSError:
                            rgb_im = image_from_web.convert('RGB')
                            rgb_im.save(image_path)
                        image_resolution = image_from_web.size
                        if image_resolution != None:
                            if image_resolution[0]<self.min_resolution[0] or image_resolution[1]<self.min_resolution[1] or image_resolution[0]>self.max_resolution[0] or image_resolution[1]>self.max_resolution[1]:
                                image_from_web.close()
                                #print("BingImageScraper Notification: %s did not meet resolution requirements."%(image_url))
                                os.remove(image_path)

                        image_from_web.close()
            except Exception as e:
                print("[ERROR] Failed to be downloaded",e)
                pass
        print("[INFO] Download Completed. Please note that some photos are not downloaded as it is not in the right format (e.g. jpg, jpeg, png)")