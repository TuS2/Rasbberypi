# обходим гугл-капчу на 9 элементов

import webbrowser, time, os, pyautogui
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, UnexpectedAlertPresentException
import urllib.request
import random
import tensorflow
from keras.models import load_model
import argparse
import pickle
import cv2
import os
from PIL import Image

browser = webdriver.Firefox()
browser.implicitly_wait(5)
browser.get('https://captcha.guru/ru/feedback/')
time.sleep(5)

iframe = browser.find_elements_by_tag_name('iframe')[0]
browser.switch_to.frame(iframe)
act = browser.find_element_by_css_selector('.recaptcha-checkbox-border')
act.click()


def captcha():
    t = random.uniform(1, 4)
    browser.switch_to.default_content()
    # возможно, вместо 3 ниже надо поставить 2
    iframe = browser.find_elements_by_tag_name('iframe')[3]  # узнаем категорию капчи:автобусы,гидранты...
    browser.switch_to.frame(iframe)
    time.sleep(2)
    act = browser.find_element_by_xpath('/html/body/div/div/div[2]/div[1]/div[1]/div/strong')
    print(act.text)
    global name
    name = str(act.text)  # для функции clicks
    a = ['велосипеды', 'пешеходные переходы', 'гидрантами', 'автомобили', 'автобус']
    # проверяем, что картинок не 16
    try:
        act = browser.find_element_by_xpath(' /html/body/div/div/div[2]/div[2]/div/table/tbody/tr[1]/td[4]/div/div[1]')
        # обновили картинку с капчи
        act = browser.find_element_by_xpath('//*[@id="recaptcha-reload-button"]')
        act.click()
        time.sleep(2)
        browser.switch_to.default_content()
        # возможно, вместо 3 ниже надо поставить 2
        iframe = browser.find_elements_by_tag_name('iframe')[3]  # узнаем категорию капчи:автобусы,гидранты...
        browser.switch_to.frame(iframe)
        time.sleep(2)
        act = browser.find_element_by_xpath('/html/body/div/div/div[2]/div[1]/div[1]/div/strong')
        print(act.text)
    except:
        if act.text not in a:
            # обновили картинку с капчи
            act = browser.find_element_by_xpath('//*[@id="recaptcha-reload-button"]')
            act.click()
            time.sleep(2)
            browser.switch_to.default_content()
            iframe = browser.find_elements_by_tag_name('iframe')[2]  # узнаем категорию капчи:автобусы,гидранты...
            browser.switch_to.frame(iframe)
            time.sleep(2)
            act = browser.find_element_by_xpath('/html/body/div/div/div[2]/div[1]/div[1]/div/strong')
            print(act.text)
        if act.text in a:
            # сохраняем картинку
            os.chdir('C:\\1\\vgg-net')
            im = pyautogui.screenshot(imageFilename=str(0) + '.jpg', region=(509, 411, 495, 495))

            # нарезаем картинку
            img = Image.open('0.jpg')
            area1 = (0, 0, 163, 163)  # спереди,сверху,справа,снизу)
            img1 = img.crop(area1)
            area2 = (163, 0, 326, 163)
            img2 = img.crop(area2)
            area3 = (326, 0, 489, 163)
            img3 = img.crop(area3)

            area4 = (0, 163, 163, 326)
            img4 = img.crop(area4)
            area5 = (163, 163, 326, 326)
            img5 = img.crop(area5)
            area6 = (326, 163, 489, 326)
            img6 = img.crop(area6)

            area7 = (0, 326, 163, 489)
            img7 = img.crop(area7)
            area8 = (163, 326, 326, 489)
            img8 = img.crop(area8)
            area9 = (326, 326, 489, 489)
            img9 = img.crop(area9)

            img1.save("1" + ".png")
            img2.save("2" + ".png")
            img3.save("3" + ".png")
            img4.save("4" + ".png")
            img5.save("5" + ".png")
            img6.save("6" + ".png")
            img7.save("7" + ".png")
            img8.save("8" + ".png")
            img9.save("9" + ".png")


captcha()


def prescript(file):  # функция нейросети: нашли категорию предмета
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", type=str, default=file, help="path to input image we are going to classify")
    ap.add_argument("-m", "--model", type=str, default="smallvggnet.model", help="path to trained Keras model")
    ap.add_argument("-l", "--label-bin", type=str, default="smallvggnet_lb.pickle", help="path to label binarizer")
    ap.add_argument("-w", "--width", type=int, default=64, help="target spatial dimension width")
    ap.add_argument("-e", "--height", type=int, default=64, help="target spatial dimension height")
    ap.add_argument("-f", "--flatten", type=int, default=-1, help="whether or not we should flatten the image")
    args = vars(ap.parse_args())

    image = cv2.imread(file)
    output = image.copy()
    image = cv2.resize(image, (args["width"], args["height"]))
    image = image.astype("float") / 255.0
    if args["flatten"] > 0:
        image = image.flatten()
        image = image.reshape((1, image.shape[0]))
    else:
        image = image.reshape((1, image.shape[0], image.shape[1], image.shape[2]))

    model = load_model(args["model"])
    lb = pickle.loads(open(args["label_bin"], "rb").read())
    preds = model.predict(image)
    i = preds.argmax(axis=1)[0]
    label = lb.classes_[i]
    text = "{}: {:.2f}%".format(label, preds[0][i] * 100)
    print(text[0])  # 1-предмет есть на картинке, 0 - предмета нет
    global result
    result = text[0]


# clicks
# если предмет есть на картинке и он совпадает с предметом из категории, нажимаем на картинку
def clicks(x, y):
    if (result == '1' and name == 'велосипеды') or (result == '2' and name == 'пешеходные переходы') or (
            result == '3' and name == 'гидрантами') or (result == '4' and name == 'автомобили') or (
            result == '5' and name == 'автобус'):
        act = browser.find_element_by_xpath(
            '/html/body/div/div/div[2]/div[2]/div/table/tbody/tr[' + str(x) + ']/td[' + str(y) + ']')
        act.click()
        # time.sleep(1)


# предсказываем капчи и кликаем по картинкам
def predict():
    prescript("1" + ".png")
    clicks(1, 1)
    prescript("2" + ".png")
    clicks(1, 2)
    prescript("3" + ".png")
    clicks(1, 3)
    prescript("4" + ".png")
    clicks(2, 1)
    prescript("5" + ".png")
    clicks(2, 2)
    prescript("6" + ".png")
    clicks(2, 3)
    prescript("7" + ".png")
    clicks(3, 1)
    prescript("8" + ".png")
    clicks(3, 2)
    prescript("9" + ".png")
    clicks(3, 3)
    act = browser.find_element_by_css_selector('#recaptcha-verify-button')
    act.click()
    time.sleep(1)


os.chdir('C:\\1\\vgg-net')
predict()
while True:
    captcha()
    predict()

# captcha()




