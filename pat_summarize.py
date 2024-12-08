import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import signal

class Copilot:
  def __init__(self):
    self.service = Service(ChromeDriverManager().install())
    self.driver = webdriver.Chrome(service = self.service)
    self.driver.get("https://copilot.microsoft.com/")
    kaishi = self.get_element('*', '開始する')
    if kaishi != 0:
      kaishi.click()
    namae = self.get_element('*', 'あなたの名')
    if namae != 0:
      namae.send_keys("test")
      namae.send_keys(Keys.RETURN)
  def get_element(self, attribute, value):
    length = 0
    #xpath = '//*[@*="' + value + '"]'
    xpath = '//*[@' + attribute + '="' + value + '"]'
    start = time.perf_counter()
    while length == 0:
      length = len(self.driver.find_elements(By.XPATH, xpath))
      end = time.perf_counter()
      if (end - start) > 5.0:
        return 0
    return self.driver.find_element(By.XPATH, xpath)
  def kill(self):
    os.kill(self.driver.service.process.pid, signal.SIGTERM)
  def send_prompt(self, prompts, fname):
    prompt_box = self.get_element('id', 'userInput')
    for prompt in prompts:
      prompt_box.send_keys(prompt.rstrip('\n'))
    time.sleep(1)
    prompt_box.send_keys(Keys.RETURN)
    time.sleep(10)
    output_txt = copilot.driver.find_element(By.XPATH, '//*/p/span').text
    print(output_txt)
    with open('out/' + fname + '.txt', 'w') as file:
      file.write(output_txt)

url = 'https://patents.google.com/patent/'

def get_patent(pat_num):
  response = requests.get(url + pat_num)
  if response.status_code == 200:
    soup = BeautifulSoup(response.content, "html.parser")
    claims = soup.find_all('section', {'itemprop': 'claims'})[0].find_all('div', {'class': 'claim-text'})
    descriptions = soup.find_all('section', {'itemprop': 'description'})[0].find_all('div', {'class': 'description-paragraph'})
    for i, claim in enumerate(claims, 1):
      print('【請求項' + str(i) + '】' + claim.get_text().replace('\n', '').replace('  ', ''))
    for i, description in enumerate(descriptions, 1):
      print('【段落' + str(i) + '】' + description.get_text().replace('\n', '').replace('  ', ''))
  else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
  return claims, descriptions

def make_prompt(pat_num):
  claims, descriptions = get_patent(pat_num)
  prompt = []
  prompt_head = 'これまでの会話を一旦忘れてください。全て忘れたら再度会話を始めてください。以下の文章および請求項に基づいて、まず、解決しようとしている課題、すなわち困りごとを教えてください。次に、その課題を解決する方法を教えてください。さらに、発明において工夫されている点を教えてください。なお、箇条書きにしたり、改行したりせず文章で回答してください。文章は、句読点で区切って、読みやすくしてください。'
  prompt.append(prompt_head)
  if len(descriptions) >= 4:
    for i in range(0, 4):
      prompt.append('【段落' + str(i + 1) + '】' + descriptions[i].get_text().replace('\n', '').replace('  ', ''))
  if len(claims) >= 8:
    for i in range(0, 8):
      prompt.append('【請求項' + str(i + 1) + '】' + claims[i].get_text().replace('\n', '').replace('  ', ''))
  print(prompt)
  return prompt

for pat_num in ['JP2024xxxxxxA']:
  copilot = Copilot()
  time.sleep(3)
  prompt = make_prompt(pat_num)
  copilot.send_prompt(prompt, pat_num)

copilot.kill()

