from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
import requests
import time
import os
import signal
import numpy as np
import pyperclip
import datetime
#################
# googlepatentsから特許を取得して、要約するためのプロンプトを生成する
#################
class Patent:
    # ウェブページの内容を取得する
    def __get_patent(self, pat_num):
      response = requests.get('https://patents.google.com/patent/' + pat_num)
      soup = BeautifulSoup(response.content, "html.parser")
      claims = soup.find_all('section', {'itemprop': 'claims'})[0].find_all('div', {'class': 'claim-text'})
      descriptions = soup.find_all('section', {'itemprop': 'description'})[0].find_all('div', {'class': 'description-paragraph'})
      return claims, descriptions
    # プロンプトを生成する
    def make_prompt(self, pat_num):
      claims, descriptions = self.__get_patent(pat_num)
      prompt = []
      prompt_head = '以下の文章および請求項に基づいて、まず、解決しようとしている課題、すなわち困りごとを教えてください。次に、その課題を解決する方法を教えてください。さらに、発明において工夫されている点を教えてください。なお、箇条書きにしたり、改行したりせず文章で回答してください。文章は、句読点で区切って、読みやすくしてください。必ず日本語で回答してください。'
      prompt.append(prompt_head)
      # 段落1から段落10までを追加
      if len(descriptions) >= 10:
        for i in range(0, 10):
          prompt.append('【段落' + str(i + 1) + '】' + descriptions[i].get_text().replace('\n', '').replace('  ', ''))
      # クレームを全て追加
      for i in range(0, len(claims)):
        prompt.append('【請求項' + str(i + 1) + '】' + claims[i].get_text().replace('\n', '').replace('  ', ''))
      return prompt
#################
# Copilotにプロンプトを送って回答をファイルに出力する
#################
class Copilot:
  # WebDriverを起動してCopilotのページにアクセスし、最初のページをスキップして、プロンプトを入力できる状態にする
  def __init__(self):
    self.driver = webdriver.Chrome()
    self.driver.get("https://copilot.microsoft.com/")
    self.__skip_page()
  # 最初のページをスキップする
  def __skip_page(self):
    kaishi = self.__get_element('*', '開始する')
    if kaishi != 0:
      kaishi.click()
    namae = self.__get_element('*', 'あなたの名')
    if namae != 0:
      namae.send_keys("test")
      namae.send_keys(Keys.RETURN)      
  # 所望の属性値を持つ要素を取得する
  def __get_element(self, attribute, value):
    length = 0
    xpath = '//*[@' + attribute + '="' + value + '"]'
    # ページが読み込まれるまで待機する
    start = time.perf_counter() # 計測開始
    while length == 0:
      length = len(self.driver.find_elements(By.XPATH, xpath))
      end = time.perf_counter() # 計測終了
      if (end - start) > 5.0:   # 5秒待ってもダメなら次に進む
        return 0
    return self.driver.find_element(By.XPATH, xpath)
  # プロンプトを送信して、回答をファイルに出力する
  def send_prompt(self, prompts, pat_num, out_dir):
    prompt_box = self.__get_element('id', 'userInput')
    pyperclip.copy(prompts) # プロンプトをクリップボードにコピーする
    time.sleep(1)
    prompt_box.send_keys(Keys.CONTROL,"v")  # プロンプトを貼り付ける
    prompt_box.send_keys(Keys.RETURN)
    time.sleep(10)
    try:
      output_txt = copilot.driver.find_element(By.XPATH, '//*/p/span').text
      print(output_txt)
      # 個別の回答を別々のファイルに出力する
      with open(out_dir + '/' + pat_num + '.txt', 'w') as file:
        file.write(output_txt)
      # 個別の回答を共通のファイルに上書きしていく
      with open(out_dir + '/out.txt', 'a') as file:
        file.write(pat_num + '\n')
        file.write(output_txt)
        file.write('\n' + '\n')
      self.driver.close()
    except NoSuchElementException:
      print('error: ' + pat_num)
      self.driver.close()
      return -1
#################
# メイン関数
#################
# 特許番号のリストを読み込む
pat_nums = []
with open('list.txt', 'r') as f:
  pat_nums = f.read().split('\n')
  pat_nums = pat_nums[:-1]  # 末尾は空なので削除する
# 出力フォルダを作る
now = datetime.datetime.now()
out_dir = now.strftime("%Y-%m-%d-%H-%M-%S")
os.makedirs(out_dir)
# 特許を要約する
for pat_num in pat_nums:
  copilot = Copilot()
  patent = Patent()
  time.sleep(3)
  prompt = patent.make_prompt(pat_num)
  copilot.send_prompt(prompt, pat_num, out_dir)
