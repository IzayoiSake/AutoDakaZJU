from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import datetime
import time
import os
from DingRobot import dingpush
# from chaojiying import Chaojiying_Client

# 使用代理的方法 ，可以直接windows使用代理，不用这么麻烦
# browserOptions = webdriver.ChromeOptions()
# browserOptions.add_argument('--proxy-server=ip:port)
# browser = webdriver.Chrome(chrome_options=browserOptions)

# 自动打卡
class AutoDaka:
    # 初始化
    def __init__(self, url, username, password, latitude, longitude, cookie):
        self.url = url
        self.username = username  # 用户名(学号)
        self.password = password  # 密码 
        self.latitude = latitude  # 纬度 默认是杭州市西湖区，可以在main函数里进行修改
        self.longitude = longitude  # 经度
        self.cookie = cookie  # cookie
        self.DD_BOT_TOKEN = os.getenv("DD_BOT_TOKEN") # 钉钉机器人token
        self.DD_BOT_SECRET=os.getenv("DD_BOT_SECRET") # 钉钉机器人secret

    # 获得Chrome驱动，并访问url
    def init_driver(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-infobars")

        #使用headless无界面浏览器模式，因为要放在linux服务器上运行，无法显示界面，调试的时候需要把下面五行注释掉，显示chrome界面
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('window-size=1920x1080')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--headless')

        driver = webdriver.Chrome(options=chrome_options) 
        
        return driver

    def login(self, driver):
        print("\n[Time] %s" %
              datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("打卡任务启动")
        # # 尝试5次打开网页
        # for i in range(5):
        #     try:
        #         driver.get(self.url)
        #         print("打开浙大统一身份认证平台成功")
        #         break
        #     except WebDriverException:
        #         # 如果超时
        #         print("打开网页超时，正在重试...""第"+str(i+1)+"次")
        #         continue
        # # 5次都打不开，就抛出异常
        # else:
        #     # 发送钉钉通知
        #     self.Reminder("浙大统一身份认证平台加载超时")
        #     print("页面加载超时")
        #     # 结束全部程序
        #     exit()
        
        print("等待登录...")
        try:
            errorMessage="未知"
            # 使用cookie登录
            if  self.cookie != "":
                print("使用cookie登录")
                self.Reminder("使用cookie登录")
                # 登录一个404页面,防止页面跳转导致无法添加cookie
                driver.get(self.url+"1")
                driver.delete_all_cookies()
                # 给"healthreport.zju.edu.cn"添加cookie
                for cookie in self.cookie.split(';'):
                    name,value=cookie.strip().split('=',1)
                    try:
                        driver.add_cookie({'name':name,'value':value,'domain':'healthreport.zju.edu.cn'})
                    except:
                        1
                cookies = driver.get_cookies()
                try:
                    # 加载时长设为60s
                    driver.set_page_load_timeout(60)
                    # 尝试登录5次
                    for i in range(5):
                        try:
                            driver.get(self.url)
                            print("打开浙大统一身份认证平台成功")
                            break
                        except :
                            # 如果超时
                            print("打开网页超时，正在重试...""第"+str(i+1)+"次")
                            continue
                    # 5次都打不开，就抛出异常
                    else:
                        # 发送钉钉通知
                        self.Reminder("浙大统一身份认证平台加载超时")
                        print("页面加载超时")
                        raise Exception
                    print("登录成功")
                    print("cookie登录成功")
                except Exception:
                    errorMessage="cookie登录失败"
                    raise Exception
            elif self.username != "" and self.password != "":
                driver.get(self.url)
                # 找到输入框,发送要输入的用户名和密码,模拟登陆
                username_input = driver.find_element(by=By.ID, value="username")
                password_input = driver.find_element(by=By.ID, value="password")
                login_button = driver.find_element(by=By.ID, value="dl")
                
                print("使用账号密码登录")
                self.Reminder("使用账号密码登录")
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(username_input))
                username_input.send_keys(self.username)
                password_input.send_keys(self.password)
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable(login_button))
                login_button.click()
                
            else:
                print("请填写cookie或账号密码")
                self.Reminder("您没有填写cookie或账号密码")
                raise Exception
        except Exception:
            print("登录失败"+errorMessage)
            # 发送钉钉通知
            self.Reminder("登录失败"+errorMessage)
            # 报错
            raise Exception

    def daka(self, driver):
        print("已登录到浙大统一身份认证平台")
        print("打卡任务启动...")
        print("正在获得虚拟地理位置信息...")
        
        # 获取虚拟地理位置信息
        driver.execute_cdp_cmd(
            "Browser.grantPermissions",  # 授权地理位置信息
            {
                "origin": self.url,
                "permissions": ["geolocation"]
            },
        )

        driver.execute_cdp_cmd(
            "Emulation.setGeolocationOverride",  # 虚拟位置
            {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "accuracy": 50,
            },
        )

        time.sleep(2)  # 等待位置信息

        print("在校信息填写中...")
        # 是否在校
        try:
            inSchool=driver.find_element(by=By.NAME,value="sfzx")
            inSchoolOption=inSchool.find_element(by=By.TAG_NAME, value="div").find_elements(by=By.TAG_NAME, value="div")
            inSchoolYes=WebDriverWait(driver, 10).until(EC.element_to_be_clickable(inSchoolOption[0]))
            inSchoolYes.click()
            Campus=driver.find_element(by=By.NAME,value="campus")
            CampusOption=Campus.find_element(by=By.TAG_NAME, value="div").find_elements(by=By.TAG_NAME, value="div")
            CampusYuquan=WebDriverWait(driver, 10).until(EC.element_to_be_clickable(CampusOption[1]))
            CampusYuquan.click()
            
        except Exception as error:
            print("在校信息填写异常\n", error)
        time.sleep(1)

        # 是否在实习
        print("实习信息填写中...")
        try:
            internship=driver.find_element(by=By.NAME,value="internship")
            internshipOption=internship.find_element(by=By.TAG_NAME, value="div").find_elements(by=By.TAG_NAME, value="div")
            internshipNo=WebDriverWait(driver, 10).until(EC.element_to_be_clickable(internshipOption[2]))
            internshipNo.click()
            print("实习信息已提交")
        except Exception as error:
            print("实习信息填写异常\n", error)
        time.sleep(1)

        # 位置填写
        print("位置信息填写中...")

        try:  # 提交位置信息
            area_element=driver.find_element(by=By.NAME,value="area")
            area_element=area_element.find_element(by=By.TAG_NAME, value="input")
            area_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(area_element))
        except Exception as error:
            # 如果是没找到元素，可忽略
            if "element not interactable" in str(error):
                print("位置窗口没找到,已忽略")
                ElementNotFind = True
            else:
                print("地理位置信息填写异常\n", error)
        if not ElementNotFind:
            try:
                # 尝试点击，最大尝试次数为5
                for i in range(5):
                    try:
                        area_element.click()
                        break
                    except:
                        print("提交位置信息超时，正在重试...""第"+str(i+1)+"次")
                        continue
                else:
                    print("提交位置信息超时，重试5次失败")
                    self.Reminder("提交位置信息超时，重试5次失败")
                    raise Exception
                # 检查位置是否正确
                area_element=driver.find_element(by=By.NAME,value="area")
                area_element=area_element.find_element(by=By.TAG_NAME, value="input")
                # 等待位置信息加载
                try:
                    t=0
                    while area_element.get_attribute("value") == "" and t<10:
                        time.sleep(0.5)
                        t=t+0.5
                    if area_element.get_attribute("value") == "浙江省 杭州市 西湖区":
                        print("位置信息已提交")
                    elif area_element.get_attribute("value") == '':
                        raise Exception("位置信息加载超时")
                    else:
                        raise Exception("位置信息错误")
                    print(area_element.get_attribute("value"))
                except Exception:
                    print(area_element.get_attribute("value"))
                    raise Exception("位置不正确")
            except Exception as error:
                print("地理位置信息填写异常\n", error)
                # 停止程序
                raise Exception
        else:
               1# 什么都不做
        time.sleep(3)

        #健康码信息
        print("健康码信息填写中...")

        try:  # 提交健康码信息
            HealthCode=driver.find_element(by=By.NAME,value="sqhzjkkys")
            HealthCodeOption=HealthCode.find_element(by=By.TAG_NAME, value="div").find_elements(by=By.TAG_NAME, value="div")
            GreenCode=WebDriverWait(driver, 10).until(EC.element_to_be_clickable(HealthCodeOption[0]))
            GreenCode.click()
            print("健康码信息填写已提交")
        except Exception as error:
            print("健康码信息填写异常\n", error)



        #同住人员信息
        print("同住人员信息填写中...")

        try:  # 提交同住人员信息
            RoomMate=driver.find_element(by=By.NAME,value="sfymqjczrj")
            RoomMateOption=RoomMate.find_element(by=By.TAG_NAME, value="div").find_elements(by=By.TAG_NAME, value="div")
            # 在RoomMateOption中寻找元素<span>否 No</span>
            RoomMateNo=WebDriverWait(driver, 10).until(EC.element_to_be_clickable(RoomMateOption[1]))
            RoomMateNo.click()
            print("同住人员信息填写已提交")
        except Exception as error:
            print("同住人员信息填写异常\n", error)

        time.sleep(3)
        
        # 本人承诺
        try:
            Commit=driver.find_element(by=By.NAME,value="sfqrxxss")
            CommitYes=Commit.find_element(by=By.TAG_NAME, value="div").find_element(by=By.TAG_NAME, value="div")
            CommitYes.click()
        except Exception as error:
            print("承诺失败\n", error)

        time.sleep(1)
        
        # 提交信息
        driver.find_element(by=By.XPATH, 
                            value="/html/body/div[1]/div[1]/div/section/div[5]/div/a").click()

        time.sleep(2)
        
        # 弹出的确认提交窗口，点击确定
        try:
            # 寻找<div class="wapcf-btn wapcf-btn-ok">确认提交</div>的按钮
            submit=driver.find_element(by=By.ID, value="wapcf")
            submit=submit.find_element(by=By.CLASS_NAME, value="wapcf-inner")
            submitTitle=submit.find_element(by=By.CLASS_NAME, value="wapcf-title")
            if submitTitle.text=="每天只能填报一次，请确认信息是否全部正确？":
                submit=submit.find_element(by=By.CLASS_NAME, value="wapcf-btn-box")
                submit=submit.find_element(by=By.CLASS_NAME, value="wapcf-btn-ok")
                submit = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(submit))
                submit.click()
                print("确认提交")
                self.Reminder("今天的打卡完成了，耶！")
            else:
                raise Exception("")
        except:
            try:
                # 寻找<div class="wapat-title">每天只能填报一次，你已提交过</div>的按钮
                HaveSubmitted=driver.find_element(by=By.CLASS_NAME, value="wapat-title")
                if HaveSubmitted.text=="每天只能填报一次，你已提交过":
                    print('您今天已提交过.\n')
                    self.Reminder("您今天已提交过")
                else:
                    raise Exception("")
            except Exception as error:
                print('提交失败.\n')
                self.Reminder("提交失败,请注意")

        time.sleep(1)
    
    def Reminder(self, content):
        if self.DD_BOT_TOKEN:
            ding= dingpush('浙江大学每日健康打卡小助手', content, self.DD_BOT_TOKEN,self.DD_BOT_SECRET)
            ding.SelectAndPush()
        else:
            print("钉钉推送未配置，请自行查看签到结果")
        

    def run(self):
        driver = self.init_driver()
        self.login(driver)
        self.daka(driver)
        driver.close()
        print("打卡完成")



if __name__ == "__main__":
    
    """
    用户输入区：
    学号
    密码
    定位地点的经纬度
    """
    url = "https://healthreport.zju.edu.cn/ncov/wap/default/index"
    account = os.getenv("account")#os.getenv("account")
    password = os.getenv("password")#os.getenv("password")
    cookie = "eai-sess="+os.getenv("cookie")
    latitude = 30.27  # 虚拟位置纬度
    longitude = 120.13  # 经度
    daka = AutoDaka(url, account, password, latitude, longitude, cookie)
    daka.run()
