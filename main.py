import os
import time
import configparser
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium import webdriver
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import (GetHistoryRequest)

config = configparser.ConfigParser()
config.read("config.ini")
api_id = int(config['Telegram']['api_id'])
api_hash = config['Telegram']['api_hash']
username = config['Telegram']['username']
channel_link = config['Telegram']['channel_link']
trade_amount = config['Bot']['trade_amount']


class Robot:
    def __init__(self):
        options = uc.ChromeOptions()
        # options.add_argument(f"--user-data-dir={profile}")
        self.available_pairs = []
        self.pair = False
        print(os.getcwd()+"\\chromedriver.exe")
        self.driver = uc.Chrome(options=options,subprocess=True, version_main=108)
        self.driver.get("https://qxbroker.com/en")
        WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable(
            (By.XPATH, "//a[@href='https://qxbroker.com/en/sign-in/']"))).click()
        print("Waiting for authorization...")

        while not self.driver.find_elements(By.XPATH, "//span[text()='Up']"):
            time.sleep(1)
        print("Authorized!")
        input("Tap if ready...")
        trade_amount_input = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'section-deal__investment')]//input")))

        trade_amount_input.click()
        trade_amount_input.send_keys(Keys.ARROW_DOWN)
        trade_amount_input.send_keys(Keys.BACKSPACE)
        trade_amount_input.send_keys(Keys.BACKSPACE)
        trade_amount_input.send_keys(Keys.BACKSPACE)
        trade_amount_input.send_keys(Keys.BACKSPACE)
        trade_amount_input.send_keys(Keys.BACKSPACE)
        trade_amount_input.send_keys(str(trade_amount))

    def up(self):
        button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(
            (By.XPATH, "//button/span[text()='Up']/parent::button")))
        self.driver.execute_script("arguments[0].click();", button)

    def down(self):
        button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(
            (By.XPATH, "//button/span[text()='Down']/parent::button")))
        self.driver.execute_script("arguments[0].click();", button)

    def set_time(self, hours=0, minutes=0, seconds=0, retry=0):
        if retry >= 3:
            return False

        hours = str(hours)
        if len(hours) < 2:
            hours = '0' + hours
        minutes = str(minutes)
        if len(minutes) < 2:
            minutes = '0' + minutes
        seconds = str(seconds)
        if len(seconds) < 2:
            seconds = '0' + seconds
        time_input = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
            (By.XPATH, "//input[@class='input-control__input opacity']")))
        time_input.click()
        time_input.send_keys(Keys.ARROW_UP)

        if hours == '00':
            if self.driver.find_elements(By.XPATH, f"//div[text()='{minutes}:{seconds}']"):
                button = self.driver.find_elements(By.XPATH, f"//div[text()='{minutes}:{seconds}']")[0]
                self.driver.execute_script("arguments[0].click();", button)
                return True
        else:
            if self.driver.find_elements(By.XPATH, f"//div[text()='{hours}:{minutes}:{seconds}']"):
                button = self.driver.find_elements(By.XPATH, f"//div[text()='{hours}:{minutes}:{seconds}']")[0]
                self.driver.execute_script("arguments[0].click();", button)
                return True

        for sym in hours + minutes + seconds:
            time_input.send_keys(sym)
        time.sleep(0.1)
        if time_input.get_attribute("value") != f"{hours}:{minutes}:{seconds}":
            return self.set_time(int(hours), int(minutes), int(seconds), retry + 1)
        else:
            return True

    def set_pair(self, pair):
        if 'OTC' in pair:
            query = 'OTC'
        else:
            query = pair.split(" ")[0]

        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(
            (By.XPATH, "//div[@class='tab__label-caret']"))).click()

        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(
            (By.XPATH, "//input[@class='asset-select__search-input']"))).send_keys(query)

        try:
            button = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, f"//span[contains(text(), '{pair.upper()}')]")))
            self.driver.execute_script("arguments[0].click();", button)
            return True
        except:
            print(f"Pair {pair} was not found.")
            return False

    def get_pairs(self):
        try:
            start_time = time.time()
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='tab__label-caret']"))).click()

            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, "//button[contains(@class, 'asset-select__search-filter')]")))
            filters = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'asset-select__search-filter')]")
            available_pairs = []
            for filter_ in filters:
                self.driver.execute_script("arguments[0].click();", filter_)
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                    (By.XPATH,
                     f"//button[contains(@class, 'active') and contains(text(), '{filter_.text}')]")))

                for available_pair in self.driver.find_elements(By.XPATH, "//div[@class='assets-table__name']//span"):
                    while available_pair.text == '':
                        time.sleep(0.01)
                        if time.time() - start_time > 5:
                            self.driver.refresh()
                            return self.get_pairs()
                available_pairs += [pair.text.lower() for pair in
                                    self.driver.find_elements(By.XPATH, "//div[@class='assets-table__name']//span")]

            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='tab__label-caret']"))).click()
            self.available_pairs = available_pairs
        except:
            self.driver.refresh()
            return self.get_pairs()

    def parse_message_for_pair(self, message):
        self.get_pairs()
        pair = False
        for available_pair in self.available_pairs:
            if available_pair in message.lower():
                pair = available_pair.lower()
                break
        if pair is False:
            self.get_pairs()
            for available_pair in self.available_pairs:
                if available_pair in message.lower():
                    pair = available_pair
                    break
        if pair:
            print(f"A pair is set: {pair}")
            self.pair = pair
            return True
        return False

    def parse_message(self, message):
        try:
            hours = 0
            minutes = 0
            seconds = 0
            words = message.split(" ")
            for i in range(len(words)):
                if words[i] == 'min':
                    minutes = int(words[i - 1])
                elif words[i] == 'sec':
                    seconds = int(words[i - 1])
                elif words[i] == 'hour':
                    hours = int(words[i - 1])

            up_or_down = False
            if "Call" in message:
                up_or_down = "up"
            elif "Put" in message:
                up_or_down = "down"

            if self.pair and (hours or minutes or seconds) and up_or_down:
                self.set_pair(self.pair)
                is_time_set = self.set_time(hours=hours, minutes=minutes, seconds=seconds)
                if not is_time_set:
                    print(f"Unable to set time: {hours} hours, {minutes} minutes, {seconds} seconds\n")
                    return
                if up_or_down == "up":
                    self.up()
                elif up_or_down == "down":
                    self.down()
                print(
                    "A bet was made!\n"
                    f"Pair: {self.pair}\n"
                    f"Time: {hours} hours, {minutes} minutes, {seconds} seconds\n"
                    f"Action: {up_or_down}\n"
                )
            else:
                is_pair_set_message = self.parse_message_for_pair(message)
                if not is_pair_set_message:
                    print("Unable to parse message :(")
        except:
            if self.pair is False:
                print("Pair is not set.")
            print("Unable to parse message :(")

    def __del__(self):
        self.driver.quit()


if __name__ == '__main__':
    client = TelegramClient(session=f"{username}.session", api_id=api_id, api_hash=api_hash)
    client.start()
    try:
        channel_link = int(channel_link)
    except:
        pass

    robot = Robot()
    robot.get_pairs()
    channel = client.get_entity(channel_link)

    processed_ids = []
    while True:
        posts = client(GetHistoryRequest(
            peer=channel,
            limit=1,
            offset_date=None,
            offset_id=0,
            max_id=0,
            min_id=0,
            add_offset=0,
            hash=0))
        if posts.messages[0].id not in processed_ids:
            msg = posts.messages[0].message
            print("\nNew message!\n" + msg)
            processed_ids.append(posts.messages[0].id)
            robot.parse_message(msg)
        else:
            print("\n\nThere are no new messages...")
        time.sleep(1)
