"""
随申行

路径：随申行APP
用途：签到、做任务、养宠物攒兜豆，兑换上海地铁优惠券
变量名：SSX_COOKIE
格式： 任意请求头抓 Authorization 值
---------------------------------
20240529 新增当日首次登陆、游戏成就分享
20240610 新增每日签到、浏览商场任务
20240717 增加自动领养宠物
20240808 增加浏览兜豆商城任务
20240815 更新兜豆领取API && 移除废弃活动
---------------------------------
cron: 0 0 * * *
const $ = new Env("随申行");
"""
import os
import random
import time
import requests
from datetime import datetime
from common import make_request, save_result_to_file
from urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
from sendNotify import send


class SSX():
    name = "随申行"

    def __init__(self, cookie):
        parts = cookie.split('#')
        self.cookie = parts[0]
        self.uid = parts[1]
        self.adoptingId = 0
        self.adoptingName = ''
        self.wait_receive_ids = []
        self.needReceiveBean = 0
        self.msg = ''
        self.headers = {
            'Host': 'api.shmaas.net',
            'User-Agent': 'ios-shell-maas/2.00.41 (iPhone; iOS 16.6; Scale/3.00)',
            'X-Saic-App-Version': '2.00.41',
            'X-Saic-Req-Ts': '1716953610832',
            'X-Saic-LocationTime': '1716953604744',
            'X-Maas-Req-Ts': '1716953610830.563965',
            'X-Saic-Real-App-Version': '2.00.41.27141',
            'X-Saic-Channel': 'maas',
            'X-Saic-AppId': 'maas_car',
            'X-Saic-Gps': '121.306501,31.136068',
            'X-Saic-Device-Id': '633EB41D5EEC41B1BA90E94C0A37D1D6',
            'X-Saic-OS-Name': 'ios',
            'X-Saic-User-Agent': 'timezone/GMT+8 platform/iOS platform_version/16.6 carrier_code/65535 carrier_name/-- device_name/iPhone device_id/633EB41D5EEC41B1BA90E94C0A37D1D6 app_name/passenger app_version/2.00.41',
            'X-Saic-Platform': 'IOS',
            'X-Saic-Finger': '5503748B-E81C-45B9-AA30-326F15A40C91',
            'X-Saic-ProductId': '5',
            'X-Saic-CityCode': '310100',
            'Connection': 'keep-alive',
            'X-Saic-Ds': 'db0cdc011b62592d',
            'uid': self.uid,
            'Authorization': self.cookie,
            'Accept-Language': 'zh-Hans-CN;q=1',
            'X-Saic-Req-Sn': 'EAFB3547-C4EB-4078-8C4F-66405E351E08',
            'env': 'release',
            'X-Saic-Location-CityCode': '310100',
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'X-Maas-Req-Sn': '8C4EACA9-06DD-4FAF-8CFA-1D6657F2FE68',
            'X-Saic-LocationAccuracy': '28.780395'
        }

    def getUserInfo(self):
        json_data = {
            'clientId': '1501489616703070208',
            'language': 'zh-cn',
        }
        url = 'https://api.shmaas.net/auth/maas/queryUserInformationForPersonalCenter'
        response = make_request(url, json_data=json_data, method='post', headers=self.headers)
        if response and response['errCode'] == 0:
            save_result_to_file("success", self.name)
            msg = f'---------------------------\n'
            msg += f'🐹昵称：{response["data"]["userBasicInformation"]["name"]}\n'
            msg += f'🐹手机：{response["data"]["userBasicInformation"]["mobile"]}\n'
            msg += f'🐹兜豆：{response["data"]["userCombineInformation"]["userCredit"]["greenCredit"]}'
            self.msg += msg
            print(msg)
        else:
            save_result_to_file("error", self.name)

    def user_game_list(self):
        gameName = ''
        json_data = {
            'language': 'zh-cn',
        }
        url = 'https://api.shmaas.net/cap/base/credits/v2/queryUserGameList'
        response = make_request(url, json_data=json_data, method='post', headers=self.headers)
        if response and response['errCode'] == 0:
            for i in response['data']['gameCardInfo']:
                if i["type"] == 2:  # type 2喂养中
                    self.adoptingId = i["gameId"]
                    if i["gameId"] == '998':
                        gameName = '和平鸽'
                    elif i["gameId"] == '999':
                        gameName = '白玉兰'
                    self.adoptingName = gameName
                    break

    def get_game_info(self):
        msg = ''
        url = 'https://api.shmaas.net/cap/base/credits/queryNowAdoptInfo'
        data = {"language": "zh-cn"}
        response = requests.post(url, headers=self.headers, json=data).json()
        msg += f'✅领养物: {self.adoptingName}\n'
        msg += f'✅当前等级：{response["data"]["feedUserGameNew"]["level"]}\n'
        msg += f'✅喂养进度：{response["data"]["feedUserGameNew"]["nowScore"]}/{response["data"]["feedUserGameNew"]["needScore"]}\n'

        self.msg += msg
        print(msg)

    # 领养宠物
    def adopt(self):
        gameIds = ['998', '999']
        gameName = ''
        gameId = random.choice(gameIds)
        if gameId == '998':
            gameName = '和平鸽'
        elif gameId == '999':
            gameName = '白玉兰'
        json_data = {
            'language': 'zh-cn',
            'gameId': gameId,
        }
        url = 'https://api.shmaas.net/cap/base/credits/v2/adoptUserGame'
        response = requests.post(url, headers=self.headers, json=json_data)
        response_json = response.json()
        if response_json['errCode'] == 0:
            msg = f'✅领养成功！| 拿下: {gameName}'
            print(msg)
        else:
            msg = f'❌领养失败，{response_json["errMsg"]}'
            print(msg)

    def feed(self):
        msg = '✅开始喂养......\n'
        url = 'https://api.shmaas.net/cap/base/credits/v2/feedUserGame'
        data = {
            'language': 'zh-cn',
            'gameId': self.adoptingId
        }
        response = requests.post(url, headers=self.headers, json=data).json()
        now_score = response["data"]["feedUserGameNew"]["nowScore"]
        need_score = response["data"]["feedUserGameNew"]["needScore"]
        msg = f'-----------------------------------\n'
        if response['errCode'] == 0:
            msg += f'✅喂养成功，更新等级进度：{now_score - 10}/{need_score}➡️{now_score}/{need_score}\n'
            if now_score == 100:
                print("✅喂养完成，开始领养新的宠物")
                self.adopt()
        elif response['errCode'] == -2763250:
            msg += f'✅今天已经喂养过了，明天再来吧!\n'
        else:
            msg += f'❌喂养失败，{response["errMsg"]}\n'

        self.msg += msg
        print(msg)

    def today_first_login(self):
        json_data = {
            'language': 'zh-cn',
            'behaviorType': 3,
        }
        url = 'https://api.shmaas.net/actbizgtw/v1/reportUserBehavior'
        response = requests.post(url, headers=self.headers, json=json_data)
        if response and response.status_code == 200:
            response_json = response.json()
            if response_json['errCode'] == 0:
                msg = f'✅登录成功'
            else:
                msg = f'❌今日首次登录失败，{response_json["errMsg"]}'
        else:
            msg = f'❌今日首次登录失败'

        self.msg += msg
        print(msg)

    def xl_subway_ticket_list(self):
        msg = f'---------- 🐹限量抢购🐹 ----------\n'
        json_data = {
            'productIdList': [
                102,
                104,
                105,
            ],
            'sellPlatform': 'app',
        }
        url = 'https://api.shmaas.net/cap/product/queryProductInfoList'
        response = make_request(url, json_data=json_data, method='post', headers=self.headers)
        if response and response['errCode'] == 0:
            for i in response['data']['productInfoList']:
                if i["sellOut"] == 1:
                    status = "已售罄"
                elif i["sellOut"] == 2:
                    status = "可兑换"
                else:
                    status = "其他状态"
                msg += f'🐹{i["productName"]} | {i["price"]}兜豆 | {status}\n'
        else:
            msg = f'❌获取地铁券失败，{response["errMsg"]}'

        self.msg += msg
        print(msg)

    def my_subway_tickets(self):
        msg = f'---------- 🐹可用地铁券🐹 ----------\n'
        json_data = {
            'userId': self.uid,
            'carService': 'PUB-TRAFFIC',
        }
        url = 'https://api.shmaas.net/cap/base/coupon/queryAvailableCouponCardList'
        response = make_request(url, json_data=json_data, method='post', headers=self.headers)
        if response and response['errCode'] == 0:
            if 'records' in response['data']:
                for i in response['data']['records']:
                    msg += f'🐹【{i["title"]}】：数量{i["couponCount"]}，有效期至：{i["endTime"]}\n'
            else:
                msg += f'暂无可用地铁券'

        else:
            msg += f'❌获取地铁券失败，{response["errMsg"]}'

        self.msg += msg
        print(msg)

    def ssx_sign(self):
        json_data = {
            'sourceId': 'activityPlay66e9b9acf94d0293',
            'taskId': 10,
        }
        url = 'https://api.shmaas.net/actbizgtw/v1/report/sign'
        response = requests.post(url, headers=self.headers, json=json_data)
        if response and response.status_code == 200:
            response_json = response.json()
            if response_json['errCode'] == 0 or response_json['errCode'] == -196502:
                msg = f'✅签到成功'
            else:
                msg = f'❌签到失败，{response_json["errMsg"]}'
        else:
            msg = f'❌签到失败'

        self.msg += msg
        print(msg)

    def view_mall(self):
        json_data = {
            'sourceId': 'activityPlay66e9b9acf94d0293',
            'taskId': 57,
            'browseAddress': '',
        }
        url = 'https://api.shmaas.net/actbizgtw/v1/report/browse'
        response_json = requests.post(url, headers=self.headers, json=json_data).json()
        if response_json['errCode'] == 0:
            print(f'✅浏览兜豆商城成功')
        else:
            print(f'❌浏览兜豆商城失败，{response_json["errMsg"]}')

    # 待领取积分
    def wait_receive_credit(self):
        json_data = {
            'uid': self.uid,
        }
        url = 'https://api.shmaas.net/cap/base/credits/queryCreditsDetail'
        response_json = requests.post(url, headers=self.headers, json=json_data).json()
        if response_json['errCode'] == 0:
            list = response_json['data']['detail']
            if len(list) > 0:
                for item in response_json['data']['detail']:
                    id = item['id']
                    self.wait_receive_ids.append(id)
        else:
            print(f'❌获取待领取积分失败，{response_json["errMsg"]}')

    def receive_all_credit(self):
        json_data = {
            'greenCreditId': self.wait_receive_ids,
            'uid': self.uid,
        }
        url = 'https://api.shmaas.net/cap/base/credits/getBubbleCredit'
        response_json = requests.post(url, headers=self.headers, json=json_data).json()
        if response_json['errCode'] == 0:
            print("✅兜豆领取成功")
        else:
            print(f'❌兜豆领取失败|{response_json["errMsg"]}')

    def main(self):
        title = "随申行"
        self.getUserInfo()

        self.today_first_login()
        time.sleep(random.randint(7, 15))

        self.ssx_sign()
        time.sleep(random.randint(5, 10))

        self.user_game_list()
        self.get_game_info()
        time.sleep(random.randint(7, 15))
        self.feed()
        time.sleep(random.randint(5, 10))

        self.view_mall()
        time.sleep(random.randint(5, 10))

        self.wait_receive_credit()
        self.receive_all_credit()
        time.sleep(random.randint(5, 10))

        # self.xl_subway_ticket_list()
        # time.sleep(random.randint(5, 10))


if __name__ == '__main__':
    env_name = 'SSX_COOKIE'
    cookie = os.getenv(env_name)
    if not cookie:
        print(f'⛔️未获取到ck变量：请检查变量 {env_name} 是否填写')
        exit(0)

    SSX(cookie).main()
