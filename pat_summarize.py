
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import os
import signal
import numpy as np
import pyperclip

# ウェブページの内容を取得
def get_patent(pat_num):
  response = requests.get('https://patents.google.com/patent/' + pat_num)
  if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    claims = soup.find_all('section', {'itemprop': 'claims'})[0].find_all('div', {'class': 'claim-text'})
    descriptions = soup.find_all('section', {'itemprop': 'description'})[0].find_all('div', {'class': 'description-paragraph'})
  else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
  return claims, descriptions

# プロンプトを生成する
def make_prompt(pat_num):
  claims, descriptions = get_patent(pat_num)
  prompt = []
  prompt_head = 'これまでの会話を一旦忘れてください。全て忘れたら再度会話を始めてください。以下の文章および請求項に基づいて、まず、解決しようとしている課題、すなわち困りごとを教えてください。次に、その課題を解決する方法を教えてください。さらに、発明において工夫されている点を教えてください。なお、箇条書きにしたり、改行したりせず文章で回答してください。文章は、句読点で区切って、読みやすくしてください。'
  prompt.append(prompt_head)
  # 段落1から段落10までを追加
  if len(descriptions) >= 10:
    for i in range(0, 10):
      prompt.append('【段落' + str(i + 1) + '】' + descriptions[i].get_text().replace('\n', '').replace('  ', ''))
  # クレームを全て追加
  for i in range(0, len(claims)):
    prompt.append('【請求項' + str(i + 1) + '】' + claims[i].get_text().replace('\n', '').replace('  ', ''))
  return prompt

# プロンプトをCopilotに送る
class Copilot:
  def __init__(self):
    # ChromeDriverのパスを設定
    self.service = Service(ChromeDriverManager().install())
    # WebDriverを起動
    self.driver = webdriver.Chrome(service = self.service)
    # Copilotのページにアクセス
    self.driver.get("https://copilot.microsoft.com/")
    # 最初の画面を飛ばす
    kaishi = self.get_element('*', '開始する')
    if kaishi != 0:
      kaishi.click()
    namae = self.get_element('*', 'あなたの名')
    if namae != 0:
      namae.send_keys("test")
      namae.send_keys(Keys.RETURN)
  # 所望の属性値を持つ要素を取得する
  def get_element(self, attribute, value):
    length = 0
    #xpath = '//*[@*="' + value + '"]'
    xpath = '//*[@' + attribute + '="' + value + '"]'
    # ページが読み込まれるまで待機する
    start = time.perf_counter() # 計測開始
    while length == 0:
      length = len(self.driver.find_elements(By.XPATH, xpath))
      end = time.perf_counter() # 計測終了
      if (end - start) > 5.0:   # 5秒待ってもダメなら次に進む
        return 0
    return self.driver.find_element(By.XPATH, xpath)
  # ブラウザを開いたままにしておく
  def kill(self):
    os.kill(self.driver.service.process.pid, signal.SIGTERM)
  # プロンプトを送信する
  def send_prompt(self, prompts, fname):
    prompt_box = self.get_element('id', 'userInput')
    pyperclip.copy(prompts)
    time.sleep(1)
    prompt_box.send_keys(Keys.CONTROL,"v")
    prompt_box.send_keys(Keys.RETURN)
    time.sleep(10)
    try:
      output_txt = copilot.driver.find_element(By.XPATH, '//*/p/span').text
      print(output_txt)
      with open('out/' + fname + '.txt', 'w') as file:
        file.write(output_txt)
      with open('out/out.txt', 'a') as file:
        file.write(fname + '\n')
        file.write(output_txt)
        file.write('\n' + '\n')
      self.driver.close()
    except NoSuchElementException:
      print('error: ' + fname)
      self.driver.close()
      return -1

# メイン関数
pat_nums = []
with open('list.txt', 'r') as f:
  pat_nums = f.read().split('\n')
  pat_nums = pat_nums[:-1]  # 末尾は空なので削除する

for pat_num in pat_nums:
  copilot = Copilot()
  time.sleep(3)
  prompt = make_prompt(pat_num)
  copilot.send_prompt(prompt, pat_num)

copilot.kill()
