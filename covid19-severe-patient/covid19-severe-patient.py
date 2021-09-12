#!/usr/bin/env python3

'''
新型コロナ重症者数の速報メールを送信するプログラム。
厚労省の新型コロナ重症者数のオープンデータに前日分が入力されたら、
すぐに数値を取得して、メール送信する。

※データが更新されるまで、10秒ごとに「データがありません」と表示されます。

出典：厚生労働省　新型コロナ重症者数オープンデータ
https://covid19.mhlw.go.jp/public/opendata/severe_cases_daily.csv
'''

# 必要なモジュールのインポート
import pandas as pd
from datetime import datetime, timedelta, timezone
import time

# gmailを使ったメール送信プログラム
from smtplib import SMTP
from email.mime.text import MIMEText
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

# タイムゾーンの生成
JST = timezone(timedelta(hours=9), 'JST')

# 日付を設定する
today_datetime = datetime.now(JST)
yesterday_datetime = today_datetime - timedelta(days=1)
daybeforeyesterday_datetime = today_datetime - timedelta(days=2)

# 日付はフォーマットを統一して比較するため文字列に
today = today_datetime.strftime('%Y-%m-%d')
yesterday = yesterday_datetime.strftime('%Y-%m-%d')
daybeforeyesterday = daybeforeyesterday_datetime.strftime('%Y-%m-%d')

# データの取得元
url = 'https://covid19.mhlw.go.jp/public/opendata/severe_cases_daily.csv'

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


# 厚労省の重症者数CSVデータの読み込み, 日付に合わせたデータの抽出
def get_data(date):
    df_severe = pd.read_csv(url, encoding='utf-8')
    df_severe['Date'] = pd.to_datetime(df_severe['Date']).dt.strftime('%Y-%m-%d')
    df_date = df_severe[df_severe['Date'] == date]
    df_date_all = df_date[df_date['Prefecture'] == 'ALL']
    if len(df_date_all['Date']) != 0:
        date_value = df_date_all.iloc[0][0]
        severe_cases_value = df_date_all.iloc[0][2]
        print(f'日付: {date_value}  重症者数: {severe_cases_value}') 
        return date_value, severe_cases_value
    else:
        print(f'日付: {date}  データがありません')
        return 'None'


# グローバル変数に代入（初期化）
value1 = get_data(daybeforeyesterday)
value2 = get_data(yesterday)
value3 = get_data(today)


# 昨日のデータが更新されるまで、10秒ごとに繰り返し実行
def repeat_get_data():
    global value2
    while type(value2) != tuple or type(value2[1]) == str:
        value2 = get_data(yesterday)
        time.sleep(10)
    return value2

# gmailを使ってメールを送信
def sendGmailAttach():
    to = my_address  # 送信先メールアドレス
    sub = '厚労省：新型コロナ重症者数' #メール件名
    body = f'厚労省：新型コロナ重症者数 \n 日付: {value1[0]}  重症者数: {value1[1]} \n 日付: {value2[0]}  重症者数: {value2[1]}  前日比: {value2[1] - value1[1]} \n\n ※厚労省オープンデータから自動取得しています' # メール本文
    host, port = 'smtp.gmail.com', 587

    # メールヘッダー
    msg = MIMEMultipart()
    msg['Subject'] = sub
    msg['From'] = sender
    msg['To'] = to

    # メール本文
    body = MIMEText(body)
    msg.attach(body)

    # gmailへ接続(SMTPサーバーとして使用)
    gmail=SMTP(host, port)
    gmail.starttls() # SMTP通信のコマンドを暗号化し、サーバーアクセスの認証を通す
    gmail.login(sender, password)
    gmail.send_message(msg)


def main():
    input_mail_address()
    repeat_get_data()
    sendGmailAttach()
    print('メールが送信されました')

if __name__ == "__main__":
    main()

