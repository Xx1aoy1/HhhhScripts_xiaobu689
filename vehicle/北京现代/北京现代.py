"""
北京现代

任意请求头token
变量名: BJXD
cron: 25 6 * * *
const $ = new Env("北京现代");
"""
import json
import os
import random
import time
from datetime import datetime
import requests
from urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning
from common import save_result_to_file
from gpt import get_gpt_response
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class RUN():
    name = "北京现代"

    def __init__(self, token):
        self.token = token
        self.pre_score = 0
        self.article_ids = []
        self.gpt_answer = True
        self.headers = {
            'Host': 'bm2-api.bluemembers.com.cn',
            'token': token,
            'Accept': '*/*',
            'device': 'iOS',
            'User-Agent': 'ModernCar/8.25.1 (iPhone; iOS 13.4.1; Scale/2.00)',
            'Accept-Language': 'zh-Hans-CN;q=1',
            'App-Version': '8.25.1',
            'Origin-Id': 'DEC39175-978E-4B7B-948F-4176D567831B',
        }

    def user_info(self):
        url = 'https://bm2-api.bluemembers.com.cn/v1/app/account/users/info'
        response_json = requests.get(url, headers=self.headers).json()
        if response_json['code'] == 0:
            nickname = response_json['data']['nickname']
            phone = response_json['data']['phone']
            score_value = response_json['data']['score_value']
            self.pre_score = score_value
            print(f'👻用户名: {nickname} | 手机号: {phone} | 积分: {score_value}')
            content = f'{self.name}|{phone}'
            save_result_to_file("success", content)
            return True
        else:
            print(f'❌获取用户信息失败， CK已失效，请重新抓包')
            save_result_to_file("error", self.name)
            return False

    def user_score_info(self):
        url = 'https://bm2-api.bluemembers.com.cn/v1/app/account/users/info'
        response_json = requests.get(url, headers=self.headers).json()
        if response_json['code'] == 0:
            nickname = response_json['data']['nickname']
            phone = response_json['data']['phone']
            score_value = response_json['data']['score_value']
            diff_score = score_value - self.pre_score
            print(f'👻用户: {phone} | 总积分: {score_value} |今日新增积分: {diff_score}')

    def do_sign(self):
        score = 0
        hid = ''
        url = 'https://bm2-api.bluemembers.com.cn/v1/app/user/reward_list'
        while score < 5:
            response_json = requests.get(url, headers=self.headers).json()
            if response_json['code'] == 0:
                hid = response_json['data']['hid']
                rewardHash = response_json['data']['rewardHash']
                list = response_json['data']['list']
                for item in list:
                    if item["hid"] == hid:
                        score = item["score"]
                        if score >= 5:
                            print(f'tip: 如果签到成功, 积分+{score}')
                            self.sign(hid, rewardHash, score)
                            break
                        else:
                            print(f'预计签到成功，可得{score}积分，太低不签，重新初始化！')
            time.sleep(random.randint(20, 30))

    def sign(self, hid, rewardHash, score):
        # 状态上报
        json_data = {
            'hid': hid,
            'hash': rewardHash,
            'sm_deviceId': '',
            'ctu_token': None,
        }
        url = 'https://bm2-api.bluemembers.com.cn/v1/app/user/reward_report'
        response_json_ = requests.post(url, headers=self.headers, json=json_data).json()
        if response_json_['code'] == 0:
            print(f'✅签到成功 | 积分+{score}')
        else:
            print(f'❌签到失败， {response_json_["message"]}')

    # 浏览3篇文章5积分
    def view_article(self):
        article_id = random.choice(self.article_ids)
        print(f'浏览文章 | 文章ID: {article_id}')
        url = f'https://bm2-api.bluemembers.com.cn/v1/app/white/article/detail_app/{article_id}'
        requests.get(url, headers=self.headers)

    def article_list(self):
        params = {
            'page_no': '1',
            'page_size': '20',
            'type_hid': '',
        }
        url = 'https://bm2-api.bluemembers.com.cn/v1/app/white/article/list2'
        response_json = requests.get(url, params=params, headers=self.headers).json()
        if response_json['code'] == 0:
            list = response_json['data']['list']
            for item in list:
                article_id = item['hid']
                self.article_ids.append(article_id)

    def article_score_add(self):
        json_data = {
            'ctu_token': '',
            'action': 12,
        }
        url = 'https://bm2-api.bluemembers.com.cn/v1/app/score'
        response_json_ = requests.post(url, headers=self.headers, json=json_data).json()
        if response_json_['code'] == 0:
            score = response_json_['data']['score']
            print(f'✅浏览文章成功 | 积分+{score}')

    # 每日问答
    def daily_question(self):
        question_str = ''
        today_date = datetime.now().strftime("%Y%m%d")
        params = {
            'date': today_date,
        }
        url = 'https://bm2-api.bluemembers.com.cn/v1/app/special/daily/ask_info'
        response_json = requests.get(url, params=params, headers=self.headers).json()
        if response_json['code'] == 0:
            question_info = response_json['data']['question_info']
            questions_hid = question_info['questions_hid']
            # 题目
            question = question_info['content']
            print(question)
            question_str += f'{question}\n'
            # 选项
            options = question_info['option']
            for option in options:
                option_content = option['option_content']
                print(f'{option["option"]}. {option_content}')
                question_str += f'{option["option"]}. {option_content}\n'

            answer = self.get_answer(question_str)
            time.sleep(random.randint(5, 10))

            self.answer_question(questions_hid, answer)

    def get_answer(self, question_str):
        if self.gpt_answer:
            answer = get_gpt_response(question_str)
            print(f"本次使用GPT回答，GPT给出的答案是：{answer}")
            if answer == "":
                answer = random.choice(['A', 'B', 'C', 'D'])
            return answer
        else:
           answer = random.choice(['A', 'B', 'C', 'D'])
           print(f"本次盲答, 随机选出的答案是: {answer}")
           return answer

    def answer_question(self, questions_hid, my_answer):
        print('开始答题')
        json_data = {
            'answer': my_answer,
            'questions_hid': questions_hid,
            'ctu_token': ''
        }
        url = 'https://bm2-api.bluemembers.com.cn/v1/app/special/daily/ask_answer'
        response_json = requests.post(url, headers=self.headers, json=json_data).json()
        print("response_json=", response_json)
        # response_json= {'code': 0, 'data': {'answer': '', 'answer_score': '', 'state': 3}, 'msg': '', 'title': ''}
        if response_json['code'] == 0:
            if response_json['data']['state'] == 3:
                print('❌回答错误')
            elif response_json['data']['state'] == 2:
                answer = response_json['data']['answer']  # C.造价低
                print("answer=", answer)
                score = response_json['data']['answer_score']
                print("score=", score)
                print(f'✅回答正确|积分+{score}')
        else:
            print('❌答题异常')

    def main(self):
        if self.user_info():
            self.do_sign()
            time.sleep(random.randint(10, 15))
            self.article_list()
            for i in range(3):
                self.view_article()
                time.sleep(random.randint(10, 15))
            self.article_score_add()
            time.sleep(random.randint(5, 10))
            self.daily_question()
            self.user_score_info()


if __name__ == '__main__':
    env_name = 'BJXD'
    tokenStr = os.getenv(env_name)
    if not tokenStr:
        print(f'⛔️未获取到ck变量：请检查变量 {env_name} 是否填写')
        exit(0)

    try:
        json_data = json.loads(tokenStr)
        print(f"共获取到{len(json_data)}个账号")
    except json.JSONDecodeError:
        print('⛔️ JSON 解析失败，请检查变量格式是否正确')
        exit(0)

    for i, token_data in enumerate(json_data, start=1):
        print(f"\n======== ▷ 第 {i} 个账号 ◁ ========")
        token = token_data.get('token')
        user_id = token_data.get('id')
        RUN(token).main()
        print("\n随机等待10-15s进行下一个账号")
        time.sleep(random.randint(10, 15))
