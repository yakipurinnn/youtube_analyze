#youtube_再生数4をsqlに対応
#抽出したデータをmysqlに保存する
#commitによるsql保存を留意

# https://qiita.com/memakura/items/20a02161fa7e18d8a693
# CSSセレクターについて: https://developer.mozilla.org/ja/docs/Web/CSS/CSS_Selectors
# javaScriptでのsleep方法: https://hirooooo-lab.com/development/javascript-sleep/
#月単位の計算: https://qiita.com/dkugi/items/8c32cc481b365c277ec2


from msilib.schema import tables
import MySQLdb
from MySQLdb._exceptions import IntegrityError
from MySQLdb._exceptions import OperationalError
import time
import datetime
from dateutil.relativedelta import relativedelta
import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.common.by import By
import numpy as np
import pickle
import pandas as pd
import json
#pd.set_option("display.max_rows", 500)    #表示を省略しない設定


def open_json(path):
    json_data = open(path,"r", encoding="utf8")
    json_data = json.load(json_data)

    return json_data


class get_video_info:
    def __init__ (self, ch_url, ch_name):
        #wevdriverの起動
        self.driver = webdriver.Chrome()
        self.driver.get(ch_url)
        time.sleep(2)

        self.ch_url = ch_url
        self.ch_name = ch_name
        self.pre_info = self.driver.find_element(By.XPATH, "/html/body/ytd-app/div/ytd-page-manager/ytd-browse/ytd-two-column-browse-results-renderer/div[1]\
            /ytd-section-list-renderer/div[2]/ytd-item-section-renderer/div[3]/ytd-grid-renderer/div[1]")

        self.video_stats = pd.DataFrame(columns=["title", "href", "ch_name", "ch_url", "video_id", "published_date", "like_count", "view_count"])    #データを格納するシート
        self.video_info = None

    def web_scroll (self):
        pre_last_href = None
        #表示画面を下へスクロール
        for i in range(1000):
            video_info = self.pre_info.find_elements(By.TAG_NAME, "ytd-grid-video-renderer")

            last_href = video_info[len(video_info)-1].find_element(By.CSS_SELECTOR, "h3 a")
            last_href = last_href.get_attribute("href")

            #読み込んだ前後でhrefが同じ場合はスクロールを終了
            if last_href == pre_last_href:
                self.video_info = video_info
                self.video_info.reverse()
                print("最後の動画のため、画面スクロールを終了します")
                break

            print(str(len(video_info)) + "件の動画が見つかりました")

            #javascriptによるスクロール
            self.driver.execute_script("window.scrollTo(0 + 2160*"+ str(i) +", 12000*(" + str(i) +"+1));")
            time.sleep(2 + np.random.rand())

            pre_last_href = video_info[len(video_info)-1].find_element(By.CSS_SELECTOR, "h3 a")
            pre_last_href = pre_last_href.get_attribute("href")


    def extract_info(self, views_flag = False):
        #動画情報を抽出
        for i, info in enumerate(self.video_info):
            view_count = None
            info = info.find_element(By.CSS_SELECTOR, "h3 a")

            title = str(info.get_attribute("title"))    #タイトル
            href = info.get_attribute("href")    #URL

            video_id = href.replace("https://www.youtube.com/watch?v=", "")     #video id
            video_id = video_id.replace("https://www.youtube.com/shorts/", "")
            print(i, video_id)

            if not views_flag:    #動画再生は抽出しない場合(APIに任せる場合)
                video_data = pd.DataFrame(data=[[title, href, self.ch_name, self.ch_url, video_id]], columns=["title", "href", "ch_name", "ch_url", "video_id"])
                self.video_stats = pd.concat([self.video_stats, video_data], ignore_index=True)    #ignore_index = True で空配列に新たな行番号を割り当てられる

            elif views_flag:    #動画再生回数も抽出する場合
                aria_label = info.get_attribute("aria-label")    #その他情報
                aria_label = aria_label.replace(" - ショート動画を再生", "")    #ショート動画の場合
                print(aria_label)

                for j in range(15):    #aria_labelから再生回数を抽出
                    num = aria_label[len(aria_label)-5-j]
                    if num.isdecimal() or num == "," :
                        continue
                    else:
                        view_count = aria_label[len(aria_label)-4-j:len(aria_label)-4]
                        view_count = int(view_count.replace(",", ""))
                        break

                video_data = pd.DataFrame(data=[[title, href, self.ch_name, self.ch_url, video_id, view_count]], 
                                            columns=["title", "href", "ch_name", "ch_url",  "video_id", "view_count"])
                self.video_stats = pd.concat([self.video_stats, video_data], ignore_index=True)     #ignore_index = True で空配列に新たな行番号を割り当てられる
                if i == 0:
                    self.video_stats = self.video_stats.astype({"title": "str", "view_count": "int"})    #再生回数をpandasのint型に指定

            #print(i+1, "再生数:", view_count, "回", "\n", href, "\n", title)

        return self.video_stats

    def save(self):
        print(self.video_stats)
        #抽出した情報をpickle形式で保存
        f = open("データ/video_stats.pkl", "wb")
        pickle.dump(self.video_stats, f)


class selenium_to_mysql:    #mysqlのデータベースに保存
    def __init__  (self, dt_now=datetime.datetime.now(), video_data=None, user="root", passwd="Takanori6157", host="localhost", db="holo_analyze", create_trigger_flag=False):
        try:
            if video_data is None:
                print("注意: 引数 video_data が空です。メソッド fetch_video_id のみを使用する場合またはyoutube apiを利用する場合は無視して下さい")
        except Exception as e:
            print(type(e), e) 

        self.dt_now = dt_now    #現在の日付、時刻を取得
        t_delta = int(self.dt_now.strftime("%M")) % 5

        if not t_delta == 0:    #5分毎に時間を更新
            self.dt_now = self.dt_now - datetime.timedelta(minutes=t_delta)

        self.last_update = self.dt_now.strftime("%Y-%m-%d %H:%M")

        self.con = MySQLdb.connect(user=user, passwd=passwd, host=host, db=db)    #mysqlに接続
        self.cursor = self.con.cursor()
        
        self.data = video_data

        #各月ごとに動画再生数を記録するテーブルを作成する
        self.current_tbl = self.dt_now.strftime("%Y%m")    #例:202202

        self.current_tbl = str(self.current_tbl) + "_views"    #今月の再生数テーブル名 例:2022_views

        self.cursor.execute(f"show tables from {db}")    #存在しているテーブルを取得
        tables = []
        for tbl in self.cursor:
            tables.append(tbl[0])

        #当月の再生回数記録用のテーブルがない場合は新たに作成する
        if not self.current_tbl in tables:
            print("今月の再生回数記録用のテーブルを作成します")

            self.cursor.execute(f"create table {self.current_tbl} (video_id varchar(12) primary key, ch_name text, title text)")
            self.cursor.execute(f"insert into {self.current_tbl} (video_id, ch_name, title) select video_id, ch_name, title from video_stats")

        if not self.current_tbl in tables or create_trigger_flag:
            #video_statsからviewsへのデータを自動的にコピーするトリガーを作成
            self.cursor.execute(f"""create trigger if not exists {self.current_tbl}_insert_trigger  
                                after insert on video_stats for each row 
                                insert into {self.current_tbl} (video_id, ch_name, title) values(new.video_id, new.ch_name, new.title)""")

            #video_statsからデータを削除した場合、viewsからも削除するトリガーを作成
            self.cursor.execute(f"""create trigger if not exists {self.current_tbl}_delete_trigger  
                                after delete on video_stats for each row 
                                delete from {self.current_tbl} where video_id = old.video_id""")

            #先月分のトリガーを削除
            dt_mouth_ago = self.dt_now - relativedelta(months=1)
            tbl_mouth_ago = dt_mouth_ago.strftime("%Y%m") + "_views"

            self.cursor.execute(f"drop trigger if exists {tbl_mouth_ago}_insert_trigger")
            self.cursor.execute(f"drop trigger if exists {tbl_mouth_ago}_delete_trigger")
        self.con.commit()    #sql文による変更を保存する

    def add_data(self):
        for index, row in self.data.iterrows():
            video_id = row["video_id"] 
            ch_name = row["ch_name"]
            title = row["title"]
            if not title.find("'") == -1:    #シングルクオーテーション(')を含む場合は-1以外を返す
                title = title.replace("'", "\\'")
            view_count = row["view_count"]

            print(video_id, title)

            try:
                self.cursor.execute(f"""insert into video_stats 
                                    (video_id, ch_name, title, last_update, view_count) 
                                    values ('{video_id}', '{ch_name}', '{title}', '{self.last_update}', {view_count})""")
            except IntegrityError as e:
                print(index, e, "既にデータベースに追加されている動画です")
        self.con.commit()

    def update_views(self):    #動画再生回数の記録とvideo_statsの更新
        #viewsテーブルへの記録
        try:
            self.cursor.execute(f"alter table {self.current_tbl} add `{self.last_update}` int")    #数字のみのカラム名は作成できないため``で囲む
        except OperationalError as e:
            print(type(e), e, "既に生成済のカラムです")

        for index, row in self.data.iterrows():
            video_id = row["video_id"] 
            view_count = row["view_count"]

            self.cursor.execute(f"update {self.current_tbl} set `{self.last_update}`= {view_count} where video_id='{video_id}'")
            #video_statsの更新
            self.cursor.execute(f"update video_stats set last_update = '{self.last_update}', view_count = {view_count} where video_id='{video_id}'")
        self.con.commit()

    def close(self):
        self.cursor.close()
        self.con.close()


if __name__ == "__main__":
    ch_list_path = "ch_list.json"
    ch_list = open_json(ch_list_path)

    ch_name = list(ch_list.keys())[29]
    ch_url = list(ch_list.values())[29]

    print(ch_url, ch_name)

    youtube_ch = get_video_info(ch_url, ch_name)
    youtube_ch.web_scroll()
    video_data = youtube_ch.extract_info(views_flag = True)
    youtube_ch.save()

    mysql = selenium_to_mysql(video_data=video_data, create_trigger_flag=True)
    mysql.add_data()
    mysql.update_views()
    mysql.close()
