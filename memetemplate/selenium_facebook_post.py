import time
import traceback
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import FB_EMAIL, FB_PASSWORD
from datetime import datetime
from selenium.webdriver.common.action_chains import ActionChains
import json
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import re
import gc 
import psutil


def print_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"Memory usage: {memory_info.rss / 1024 ** 2:.2f} MB")
    
def extract_number(text):
    """從文字中提取數字"""
    if not text:
        return 0
    match = re.search(r'(\d+)', text.replace(",", ""))  # 處理可能存在的逗號分隔
    return int(match.group(1)) if match else 0

def facebook_login(driver, email, password):
    """自動登入 Facebook"""
    try:
        email_field = driver.find_element(By.ID, "email")
        email_field.send_keys(email)
        password_field = driver.find_element(By.ID, "pass")
        password_field.send_keys(password)
        login_button = driver.find_element(By.NAME, "login")
        login_button.click()
        print("[INFO] 自動登入完成")
        time.sleep(30)
        return True
    except Exception as e:
        print(f"[ERROR] 登入失敗: {str(e)}")
        return False

def process_post(driver, post):
    """处理单个帖文"""
    try:
        # 提取標題
        try:
            title_element = WebDriverWait(post, 10).until(
                            EC.visibility_of_element_located((By.XPATH, ".//div[contains(@class, 'xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs x126k92a')]/div"))
                        )            
            title = title_element.get_attribute("innerText")
            time.sleep(1)
        except Exception:
            try:
                title_element = WebDriverWait(post, 10).until(
                            EC.visibility_of_element_located((By.XPATH, ".//div[contains(@class, 'x6s0dn4 x78zum5 xdt5ytf x5yr21d xl56j7k x10l6tqk x17qophe x13vifvy xh8yej3')]/div"))
                        )
                title = title_element.find_element(By.XPATH, ".//div[contains(@class, 'xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs')]").get_attribute("innerText")
                time.sleep(1)
            except Exception:
                print("[INFO] 無法提取標題，跳過該帖文")
                time.sleep(1)
                return None   
                              
        # 提取標題標籤
        try:
            hashtag_elements = WebDriverWait(post, 10).until(
                            EC.visibility_of_element_located((By.XPATH, ".//a[contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz x1sur9pj xkrqix3 x1fey0fg x1s688f')]"))
                        )
            title_hastag = " ".join([element.get_attribute("innerText") for element in hashtag_elements])
            time.sleep(1)
        except Exception:
            title_hastag = "(無法提取標籤)"
            time.sleep(1)
            
        # 提取帖文圖片
        try:
            picture_element = WebDriverWait(post, 10).until(
                            EC.visibility_of_element_located((By.XPATH, ".//img[contains(@class, 'x1ey2m1c xds687c x5yr21d x10l6tqk x17qophe x13vifvy xh8yej3 xl1xv1r')]"))
                        )
            picture_src = picture_element.get_attribute("src")
            time.sleep(1)
        except Exception:
            picture_src = "(無法提取圖片)"
            time.sleep(1)
            
        # 按讚數
        try:
            like_element = WebDriverWait(post, 10).until(
                            EC.visibility_of_element_located((By.XPATH, ".//span[contains(@class, 'xt0b8zv') and contains(@class, 'x1e558r4')]"))
                        )
            like_count = extract_number(like_element.text)
            time.sleep(1)
        except Exception:
            like_count = 0
            time.sleep(1)
        
        # 提取發文時間
        try:
            # 1. 先把滑鼠移動到指定的 div 元素
            hover_element = post.find_element(By.XPATH, ".//span[contains(@class, 'x1rg5ohu x6ikm8r x10wlt62 x16dsc37 xt0b8zv')]")
            actions = ActionChains(driver)
            actions.move_to_element(hover_element).perform()
            # 2. 等待 hover
            showing_time = WebDriverWait(driver, 5).until(
                            EC.visibility_of_element_located((By.XPATH,".//span[contains(@class, 'x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1nxh6w3 x1sibtaa xo1l8bm xzsf02u')]"))
                        )
            # 3. 把 span 的 innerText 取出來
            post_time = showing_time.get_attribute("innerText")
            print("發文時間:", post_time)
            time.sleep(1)
        except Exception as e:
            print("[ERROR] 發文時間無法提取:", e)
            time.sleep(1)   
        
        # 找到第一層的按讚區域
        try:
            all_like_element_path = post.find_element(By.XPATH, ".//span[contains(@class, 'xt0b8zv x1jx94hy xrbpyxo xl423tq')]")
            all_like_element_path.click()  # 點擊展開詳細按讚資訊
            time.sleep(3)

            # 定位到所有包含 aria-label 的讚數的元素
            like_tablelist_path = driver.find_elements(By.XPATH, "//div[contains(@class, 'x1i10hfl xe8uvvx xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz xjyslct xjbqb8w x18o3ruo x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1heor9g x1ypdohk xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg x1vjfegm x3nfvp2 xrbpyxo x1itg65n x16dsc37')]")
            like_counts = {
                "normal": "未找到讚",
                "love": "未找到大心",
                "haha": "未找到哈",
                "wa": "未找到哇",
                "sad": "未找到嗚",
                "angry": "未找到怒讚",
                "courage": "未找到加油"
            }
            
            # 遍歷找到的所有元素，提取包含特定文本的 aria-label
            for element in like_tablelist_path:
                time.sleep(1)
                aria_label = element.get_attribute("aria-label")
                if aria_label:
                    if "表示讚的用戶" in aria_label:
                        like_counts["normal"] = aria_label
                    elif "表示大心的用戶" in aria_label:
                        like_counts["love"] = aria_label
                    elif "表示哈的用戶" in aria_label:
                        like_counts["haha"] = aria_label
                    elif "表示哇的用戶" in aria_label:
                        like_counts["wa"] = aria_label
                    elif "表示嗚的用戶" in aria_label:
                        like_counts["sad"] = aria_label
                    elif "表示怒的用戶" in aria_label:
                        like_counts["angry"] = aria_label
                    elif "表示加油的用戶" in aria_label:
                        like_counts["courage"] = aria_label
            time.sleep(1)
            # 關閉按讚詳情
            close_path = driver.find_element(By.XPATH, ".//div[contains(@aria-label, '關閉')]")
            close_path.click()
            #print("[INFO] 已關閉按讚詳情")

        except Exception as e:
            time.sleep(1)
            print(f"[ERROR] 無法提取讚數")
            try:
                close_path = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.XPATH, ".//div[contains(@aria-label, '關閉')]"))
                            )
                close_path.click()
                print("[INFO] 已關閉按讚詳情（異常處理）")
                time.sleep(1)
            except Exception as close_error:
                print(f"[ERROR] 無法關閉按讚詳情")
                time.sleep(1)

        # 留言數和分享數
        try:
            # 查找主 div 元素
            all_comment_share_path = WebDriverWait(post, 10).until(
                                EC.visibility_of_element_located((By.XPATH, ".//div[contains(@class,'x9f619 x1ja2u2z x78zum5 x2lah0s x1n2onr6 x1qughib x1qjc9v5 xozqiw3 x1q0g3np xykv574 xbmpl8g x4cne27 xifccgj')]"))
                            )
            comment_count = 0
            share_count = 0           
            comment_share_elements = all_comment_share_path.find_elements(By.XPATH, ".//span[contains(@class, 'html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs xkrqix3 x1sur9pj')]")            
            for index, element in enumerate(comment_share_elements):
                text = element.get_attribute("innerText")
                if index == 0:
                    comment_count = text
                elif index == 1:
                    share_count = text
                    break
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] 無法提取留言數和分享數")
            comment_count = 0
            share_count = 0
            time.sleep(1)
        
        # 貼文內容
        try:
            text_element = WebDriverWait(post, 10).until(
                                EC.visibility_of_element_located((By.XPATH, ".//div[contains(@class, 'x6ikm8r x10wlt62 x9f619 x1lkfr7t x4vbgl9 x1rdy4ex xjkvuk6 x1iorvi4 xd183bf')]"))
                            )
            post_text = text_element.text
            time.sleep(1)
        except Exception:
            post_text = "(無法提取內容)"
            time.sleep(1)

        # 留言區
        try:
            try:
                check_more_comments = WebDriverWait(post, 10).until(
                                    EC.visibility_of_element_located((By.XPATH, ".//div[contains(@class, 'x1i10hfl xjbqb8w xjqpnuy xa49m3k xqeqjp1 x2hbi6w x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk xdl72j9 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r x2lwn1j xeuugli xexx8yu x18d9i69 xkhd6sd x1n2onr6 x16tdsg8 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x3nfvp2 x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xi81zsa x1q0g3np x1iyjqo2 xs83m0k xsyo7zv')]"))
                                )  
                check_more_comments.click()  
            except Exception:
                all_area_element = WebDriverWait(post, 10).until(
                                    EC.visibility_of_element_located((By.XPATH, ".//div[contains(@class, 'x9f619 x1ja2u2z x78zum5 x2lah0s x1n2onr6 x1qughib x1qjc9v5 xozqiw3 x1q0g3np xjkvuk6 x1iorvi4 xwrv7xz x8182xy x4cne27 xifccgj')]"))
                                )            
                # 2. 查找所有子元素
                all_area_path = all_area_element.find_elements(By.XPATH, ".//div[contains(@class, 'x9f619 x1n2onr6 x1ja2u2z x78zum5 xdt5ytf x193iq5w xeuugli x1r8uery x1iyjqo2 xs83m0k xg83lxy x1h0ha7o x10b6aqq x1yrsyyn')]")          
                comment_button = all_area_path[1]
                comment_button.click()
                           
            time.sleep(10)
                
            # 4. 查找并点击 list_button
            comment_list = []
            try:
                post_element = WebDriverWait(driver, 10).until(
                                EC.visibility_of_element_located((By.XPATH, ".//div[contains(@class, 'x1n2onr6 x1ja2u2z x1afcbsf xdt5ytf x1a2a7pz x71s49j x1qjc9v5 xrjkcco x58fqnu x1mh14rs xfkwgsy x78zum5 x1plvlek xryxfnj xcatxm7 xrgej4m xh8yej3')]"))
                            )    
                list_button = WebDriverWait(post_element, 10).until(
                                EC.visibility_of_element_located((By.XPATH, ".//div[contains(@class, 'x6s0dn4 x78zum5 xdj266r x11i5rnm xat24cr x1mh8g0r xe0p6wg')]"))
                            )   
                list_button.click()
                #print("找到並點擊 list_button")
                
                # 5. 点击第三个按钮
                all_comment_buttons = driver.find_elements(By.XPATH, ".//div[contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n xe8uvvx x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz xjyslct x9f619 x1ypdohk x78zum5 x1q0g3np x2lah0s x1i6fsjq xfvfia3 xnqzcj9 x1gh759c x10wwi4t x1x7e7qh x1344otq x1de53dj x1n2onr6 x16tdsg8 x1ja2u2z x6s0dn4')]")
                all_comment_buttons[2].click()
                #print("找到並點擊'所有留言'")
                time.sleep(5)
                
                # 6. 滚动指定的 div 元素，直到元素数量不再变化
                scroll_div = driver.find_element(By.XPATH, ".//div[contains(@class, 'html-div x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1gslohp')]")   
                bottom = scroll_div.find_element(By.XPATH, ".//div[contains(@class, 'html-div xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x78zum5 x13a6bvl')]")   
                actions = ActionChains(driver)
                actions.move_to_element(scroll_div).perform()
                #print("把滑鼠移到指定 div")
                time.sleep(5)         
                previous_count = 0     
                
                while True:
                    current_elements = scroll_div.find_elements(By.XPATH, ".//div[contains(@class, 'x16hk5td x12rz0ws')]")
                    current_count = len(current_elements)
                    print("當前留言數: ", current_count)
                    
                    # 檢查元素數量是否變化
                    if current_count > 200:
                        print("留言數量超過 200，停止滾動")
                        break
                    elif current_count > previous_count:
                        previous_count = current_count
                    else:
                        print("元素數量沒有變化，停止滾動")
                        break
                    
                    #print("往下滑")
                    actions.move_to_element(bottom).perform()
                    time.sleep(3)
                        
                print("滾動完成, 留言數量為: ", current_count)
                
                # 7. 提取用户的名字和留言
                person_comments = driver.find_elements(By.XPATH, ".//div[contains(@class, 'x16hk5td x12rz0ws')]")
                for comment in person_comments:
                    try:
                        # 提取用户名
                        user_name_element = comment.find_element(By.XPATH, ".//span[contains(@class, 'x193iq5w xeuugli x13faqbe x1vvkbs x1xmvt09 x1lliihq x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x x4zkp8e x676frb x1nxh6w3 x1sibtaa x1s688f xzsf02u')]")
                        user_name = user_name_element.text
                        
                        # 提取用户留言
                        user_comment_elements = comment.find_elements(By.XPATH, ".//div[contains(@class, 'xdj266r x11i5rnm xat24cr x1mh8g0r x1vvkbs')]//div[@dir='auto']")
                        user_comments = [elem.text for elem in user_comment_elements]
                        
                        # 组合用户名和留言
                        formatted_comment = f"{user_name} : {' '.join(user_comments)}"
                        comment_list.append(formatted_comment)
                    except Exception as e:
                        print(f"[INFO] 無法提取用戶信息: {str(e)}")
                        break
                # 8. 关闭留言区
                close_path = driver.find_element(By.XPATH, ".//div[contains(@aria-label, '關閉')]")
                close_path.click()                
            except Exception as e:
                print("[INFO] 沒展開")
                close_path = driver.find_element(By.XPATH, ".//div[contains(@aria-label, '關閉')]")
                close_path.click()            
                                           
        except Exception as e:
            print(f"[ERROR] 無法提取留言區")
            
        return {
            "Title": title,
            "Title Hastag": title_hastag,
            "Picture Src": picture_src,
            "Total likes": like_count,
            "Normal Likes": extract_number(like_counts["normal"]),
            "Love Likes": extract_number(like_counts["love"]),
            "Haha Likes": extract_number(like_counts["haha"]),
            "Wa Likes": extract_number(like_counts["wa"]),
            "Sad Likes": extract_number(like_counts["sad"]),
            "Angry Likes": extract_number(like_counts["angry"]),
            "Courage Likes": extract_number(like_counts["courage"]),
            "Comments Count": extract_number(comment_count),
            "Shares Count": extract_number(share_count),
            "Post Text": post_text,
            "Post Time": post_time,
            "Comments": comment_list,
        }

    except Exception as e:
        print(f"[ERROR] 無法處理貼文")
        return None

def create_excel(filename):
    """創建一個新的空的 Excel 文件"""
    try:
        # 創建一個空的 DataFrame
        df = pd.DataFrame()
        # 將空的 DataFrame 保存到 Excel 文件
        df.to_excel(filename, index=False)
        print(f"[INFO] 已創建新的 Excel 文件: {filename}")
    except Exception as e:
        print(f"[ERROR] 無法創建 Excel 文件: {filename}: {str(e)}")

def append_to_excel(filename, data):
    """将数据追加到 Excel 文件"""
    try:
        df = pd.DataFrame([data])
        with pd.ExcelWriter(filename, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
            if 'Sheet1' in writer.sheets:
                startrow = writer.sheets['Sheet1'].max_row
                header = startrow == 1
            else:
                startrow = 0
                header = True
            df.to_excel(writer, index=False, header=header, startrow=startrow)
        print(f"[INFO] 数据已追加到 {filename}")
    except Exception as e:
        print(f"[ERROR] 无法追加数据到 {filename}: {str(e)}")
        
def main():
    chrome_options = webdriver.ChromeOptions()

    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager(driver_version="132.0.6834.84").install()),
        options=chrome_options
    )

    try:
        # 1. 登入 Facebook
        driver.get("https://www.facebook.com/")
        print("[INFO] 嘗試自動登入...")
        if not facebook_login(driver, FB_EMAIL, FB_PASSWORD):
            print("[ERROR] 自動登入失敗，請手動登入...")
            time.sleep(30)

        for i in range(1,12):
            next_day = False
            # media = news.ebc / YahooTWNews / FTVNews53 / setnews / tvbsfb / ttvnews / myudn / CTfans
            media = "CTfans"
            TARGET_PAGE = f"https://www.facebook.com/{media}"
            driver.get(TARGET_PAGE)
            time.sleep(10)
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            output_filename = f'{media}_2025020{i}_{now}.xlsx'
            create_excel(output_filename)  # 創建 Excel 文件
            
            actions = ActionChains(driver)
            previous_count = 0
            time.sleep(1)
            # 篩選條件操作
            try:
                # 查找篩選條件按鈕並點擊
                filter_button = driver.find_element(By.XPATH, "//div[@aria-label='篩選條件' and contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3')]")
                filter_button.click()
                time.sleep(3)
                # 點擊年份選單
                date = driver.find_element(By.XPATH, ".//div[contains(@class, 'x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w xdl72j9 x2lah0s xe8uvvx x2lwn1j xeuugli x1hl2dhg xggy1nq x1t137rt x1q0g3np x87ps6o x1lku1pv x78zum5 x1a2a7pz x6s0dn4 xjyslct x1qhmfi1 xhk9q7s x1otrzb0 x1i1ezom x1o6z2jb x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk x1qughib xdj266r x11i5rnm xat24cr x1mh8g0r x1a8lsjc xn6708d x1ye3gou x889kno x1n2onr6 x1yc453h x1ja2u2z')]")
                date.click()
                time.sleep(3)
                # 選擇年份
                year = driver.find_elements(By.XPATH, ".//div[contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n xe8uvvx x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xjyslct x9f619 x1ypdohk x78zum5 x1q0g3np x2lah0s x1i6fsjq xfvfia3 xnqzcj9 x1gh759c x10wwi4t x1x7e7qh x1344otq x1de53dj x1n2onr6 x16tdsg8 x1ja2u2z')]")
                year[1].click()
                time.sleep(3)
                # 點擊月份選單
                date = driver.find_elements(By.XPATH, ".//div[contains(@class, 'x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w xdl72j9 x2lah0s xe8uvvx x2lwn1j xeuugli x1hl2dhg xggy1nq x1t137rt x1q0g3np x87ps6o x1lku1pv x78zum5 x1a2a7pz x6s0dn4 xjyslct x1qhmfi1 xhk9q7s x1otrzb0 x1i1ezom x1o6z2jb x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk x1qughib xdj266r x11i5rnm xat24cr x1mh8g0r x1a8lsjc xn6708d x1ye3gou x889kno x1n2onr6 x1yc453h x1ja2u2z')]")
                date[1].click()
                time.sleep(3)
                # 選擇月份
                month = driver.find_elements(By.XPATH, ".//div[contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n xe8uvvx x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xjyslct x9f619 x1ypdohk x78zum5 x1q0g3np x2lah0s x1i6fsjq xfvfia3 xnqzcj9 x1gh759c x10wwi4t x1x7e7qh x1344otq x1de53dj x1n2onr6 x16tdsg8 x1ja2u2z')]")
                month[2].click()
                time.sleep(3)
                # 點擊日期選單
                date = driver.find_elements(By.XPATH, ".//div[contains(@class, 'x1i10hfl xjqpnuy xa49m3k xqeqjp1 x2hbi6w xdl72j9 x2lah0s xe8uvvx x2lwn1j xeuugli x1hl2dhg xggy1nq x1t137rt x1q0g3np x87ps6o x1lku1pv x78zum5 x1a2a7pz x6s0dn4 xjyslct x1qhmfi1 xhk9q7s x1otrzb0 x1i1ezom x1o6z2jb x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1ypdohk x1qughib xdj266r x11i5rnm xat24cr x1mh8g0r x1a8lsjc xn6708d x1ye3gou x889kno x1n2onr6 x1yc453h x1ja2u2z')]")
                date[2].click()
                time.sleep(3)
                # 選擇日期
                day = driver.find_elements(By.XPATH, ".//div[contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n xe8uvvx x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x6s0dn4 xjyslct x9f619 x1ypdohk x78zum5 x1q0g3np x2lah0s x1i6fsjq xfvfia3 xnqzcj9 x1gh759c x10wwi4t x1x7e7qh x1344otq x1de53dj x1n2onr6 x16tdsg8 x1ja2u2z')]")
                day[i].click()
                time.sleep(3)
                # 點擊完成按鈕
                done_button = driver.find_element(By.XPATH, ".//div[@aria-label='完成' and contains(@class, 'x1i10hfl xjbqb8w x1ejq31n xd10rxx x1sy0etr x17r0tee x972fbf xcfux6l x1qhh985 xm0m39n x1ypdohk xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1o1ewxj x3x9cwd x1e5q0jg x13rtm0m x87ps6o x1lku1pv x1a2a7pz x9f619 x3nfvp2 xdt5ytf xl56j7k x1n2onr6 xh8yej3')]")
                done_button.click()
                time.sleep(3)
            except Exception as e:
                print(f"[ERROR] 篩選條件操作失敗: {str(e)}")
                            
            while True:
                # 抓取當前頁面上的帖子
                posts = driver.find_elements(By.XPATH, "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']")
                current_count = len(posts)
                print(f"Previous count: {previous_count}")
                print(f"當前頁面上的帖子數量: {current_count}")

                time.sleep(1)
                posts_to_delete = []

                for index, post in enumerate(posts[previous_count:current_count], start=previous_count + 1):
                    print(f"處理第 {index} 則帖文")
                    time.sleep(1)
                    post_data = process_post(driver, post)
                    if post_data:
                        post_time = post_data.get("Post Time")
                        if f"2025年2月{i}日" not in post_time:
                            print(f"發文時間不是 2025年2月{i}日，停止抓取資料")
                            next_day = True
                            break  # 結束程式碼

                        append_to_excel(output_filename, post_data)  # 追加數據
                        posts_to_delete.append(post)  # 儲存要刪除的元素
                    else:
                        continue  # 跳過該帖文
                if next_day:
                    break    

                # **等所有 6 則處理完後再刪除**
                for post in posts_to_delete:
                    driver.execute_script("arguments[0].remove();", post)
                    del post
                gc.collect()
                print(f"已刪除 {len(posts_to_delete)} 則已處理的貼文")
                
                posts_to_delete.clear()

                if current_count == previous_count:
                    print("沒有新帖子，停止滾動")
                    break

                # 打印內存使用情況
                print_memory_usage()
                
                previous_count = current_count

                # 移動到指定的元素以觸發 lazy loading
                target_element = driver.find_element(By.XPATH, "//div[contains(@class, 'x1a2a7pz x1yztbdb xh8yej3')]")
                actions.move_to_element(target_element).perform()
                print("第一次移動到指定元素以觸發 lazy loading")
                time.sleep(10)

                # 再次檢查是否有新帖子
                posts = driver.find_elements(By.XPATH, "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']")
                current_count = len(posts)

                if current_count == previous_count:
                    actions.move_to_element(target_element).perform()
                    print("第二次移動到指定元素以觸發 lazy loading")
                    time.sleep(30)

                    posts = driver.find_elements(By.XPATH, "//div[@class='x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z']")
                    current_count = len(posts)
                    if current_count == previous_count:
                        print("沒有新帖子，停止滾動")
                        break
    except Exception as e:
        print("[ERROR] 程式執行錯誤：")
        print(str(e))
    finally:
        driver.quit()

if __name__ == "__main__":
    main()