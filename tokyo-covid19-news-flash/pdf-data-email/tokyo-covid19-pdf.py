#!/usr/bin/env python3

"""
東京都の新型コロナデータPDFをメール送信するプログラム

毎日16時45分に更新される東京都の新型コロナデータを取得して、メール送信します。
更新されるまでは10秒ごとに取得を繰り返して、取得できるまで「ページが見つかりません」を表示し続け、
更新データを取得した時点で、データのpdfファイルを添付してメールで送信します。
更新直後の速報ニュース配信に活用できます。
出典：東京都福祉局HP
https://www.fukushihoken.metro.tokyo.lg.jp/
"""

# 必要なモジュールをインストール
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import re
import time
import os

# gmailを使ったメール送信用
from smtplib import SMTP
from email.mime.text import MIMEText
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

# タイムゾーンの生成
JST = timezone(timedelta(hours=9), 'JST')

# 送信元のgmailアカウント、送信先のメールアドレスを入れてください
def input_mail_address():
    global sender
    global password
    global my_address
    while True:
        sender = input('送信元のgmailアドレスを入力して下さい: ') # 送信元メールアドレスを入力
        password = input('送信元のgoogleアカウントのログインパスワードを入力して下さい: ') # 送信元googleアカウントのログインパスワード入力 
        my_address = input('送信先のメールアドレスを入力して下さい: ')
        ok = input('入力完了しましたか？(完了の場合 OK と入力): ')
        if ok == 'OK':
            break
    return sender, password, my_address


# 東京都福祉保健局のページをスクレイピング
url1 = 'https://www.fukushihoken.metro.tokyo.lg.jp/'

response1 = requests.get(url1)
response1.encoding = response1.apparent_encoding 

# 最新リリースの第●●●●報の数字を取得
soup = BeautifulSoup(response1.text,'html.parser')

#第●●●●報の数字取得
elms = soup.find_all(href=re.compile("/hodo/saishin/corona"))
elms_list = []
for i in range(len(elms)):
    elm = elms[i].attrs['href']
    elm_num = elm[-9:-5]
    elms_list.append(int(elm_num))

max_num = max(elms_list)


# 新しいリリースのページがあるかどうか確認
add_num = 1
url2 = f'https://www.fukushihoken.metro.tokyo.lg.jp/hodo/saishin/corona{max_num + add_num}.files/{max_num + add_num}.pdf'

response2 = requests.get(url2)
code = response2.status_code
content_length = int(response2.headers['Content-Length'])


# 新しいページが見つかるまで繰り返す
def repeat_get_page():
    global response2
    global code
    global add_num
    global content_length         
    while code == 404 or content_length <= 800000:
        url2 = f'https://www.fukushihoken.metro.tokyo.lg.jp/hodo/saishin/corona{max_num + add_num}.files/{max_num + add_num}.pdf'
        print(url2)
        response2 = requests.get(url2)
        code = response2.status_code
        content_length = int(response2.headers['Content-Length'])
        if code == 404:
            print('ページが見つかりません')
        if add_num <= 3:
            add_num += 1
        else:
            add_num = 1
        time.sleep(10)
    return response2


# 新しいリリースからPDFファイルを取得し名前を付けて保存
filename = 'tokyo_covid19.pdf'
today = datetime.now(JST)
save_filename = today.strftime("%Y%m%d_") + filename

def make_file():
    os.makedirs('/tmp', exist_ok=True)
    with open(f'/tmp/{save_filename}', 'wb') as save_file:
        save_file.write(response2.content)
   

def sendGmailAttach():
    to = my_address  # 送信先メールアドレス
    sub = '東京都の新型コロナ感染者数' #メール件名
    text = '東京都の新型コロナ感染者数をPDF添付ファイルで送ります。'  # メール本文
    html = """
    <html>
      <head></head>
      <body>
        <p>東京都の新型コロナ感染者数をPDF添付ファイルで送ります</p>
        <p>
          <a href = 'https://www.fukushihoken.metro.tokyo.lg.jp/'>東京都のリリースへのリンク</a>
        </p>
      </body>
    </html>
    """

    host, port = 'smtp.gmail.com', 587

    # メールヘッダー
    msg = MIMEMultipart('alternative')
    msg['Subject'] = sub
    msg['From'] = sender
    msg['To'] = to

    # メール本文
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)

    # 添付ファイルの設定 # nameは添付ファイル名。pathは添付ファイルの位置を指定
    attach_file = {'name': save_filename, 'path': f'/tmp/{save_filename}'} 
    attachment = MIMEBase('application', 'pdf')
    file = open(attach_file['path'], 'rb+')
    attachment.set_payload(file.read())
    file.close()
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment", filename=attach_file['name'])
    msg.attach(attachment)

    # gmailへ接続(SMTPサーバーとして使用)
    gmail=SMTP(host, port)
    gmail.starttls() # SMTP通信のコマンドを暗号化し、サーバーアクセスの認証を通す
    gmail.login(sender, password)
    gmail.send_message(msg)

def main():
    input_mail_address()
    repeat_get_page()
    make_file()
    sendGmailAttach()
    print('メールが送信されました')

if __name__ == '__main__':
    main()

