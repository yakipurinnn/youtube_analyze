#youtube apiを用いて動画情報を取得する
#idはseleniumから取得する

#参照元: https://qiita.com/g-k/items/7c98efe21257afac70e9#%E5%8F%AF%E8%A6%96%E5%8C%96%E3%81%97%E3%81%A6%E3%81%BF%E3%82%8B
#日時計算など: https://note.nkmk.me/python-datetime-pytz-timezone/
#youtube api 500件以上取得できなくなる問題について: https://zenn.dev/jqinglong/articles/1161615fdaa6f6

from logging import exception
from multiprocessing.reduction import duplicate
from MySQLdb._exceptions import OperationalError
import pickle
import re
import datetime
from dateutil.relativedelta import relativedelta
from urllib.error import HTTPError
import pandas as pd
import numpy as np
from youtube_sql2 import selenium_to_mysql
from youtube_sql2 import open_json
#pd.set_option("display.max_rows", None)
from apiclient.discovery import build
from apiclient.errors import HttpError
import json


def pickle_load_list():    #pickleで保存したvideo_idのリストを返す
    with open("データ/video_stats.pkl", "rb") as f:
        video_id = pickle.load(f)
        video_id = list(video_id["video_id"])

        return video_id

def pickle_load():    #pandasで保存したdata_frameを返す
    with open("データ/video_stats.pkl", "rb") as f:
        video_data = pickle.load(f)

        return video_data


key_list_path = "key_list.json"
key_list = open_json(key_list_path)

class ytd_api:
    def __init__(self, api_key_list):
        self.video_stats = pd.DataFrame(columns=["video_id", "ch_name", "ch_url", "title", "published_date", \
                                                    "private_flag", "comment_count", "like_count", "view_count"])
        
        self.api_key_list = iter(api_key_list.keys())
        self.key_number_list = iter(api_key_list.values())

        self.ytd_apikey = next(self.api_key_list)   #youtube_apiキーを順に取り出す
        self.key_number = next(self.key_number_list)    #youtube_apiキーの番号を取り出す

        self.youtube = build("youtube", "v3", developerKey=self.ytd_apikey)

    def next_key(self):
        self.ytd_apikey = next(self.api_key_list)
        self.key_number = next(self.key_number_list )
        self.youtube = build("youtube", "v3", developerKey=self.ytd_apikey)

    def extract_info(self, id_list):
        for i, id in enumerate(id_list):
            break_flag = False
            for j in range(30):
                try:
                    res = self.youtube.videos().list(part='snippet,statistics', id = id).execute()
                    break
                except HttpError as e :
                    print(type(e), "APIクオートが上限に達しました。次のキーを使用します。", "next_key_number: ", 1 + int(self.key_number))
                    try:
                        self.next_key()
                    except StopIteration as e :
                        print(type(e), "APIクオートが上限に達しました。youtube_APIを終了します")
                        break_flag = True
                        break
            if break_flag:
                break

            if res["items"] == []:    #動画が非公開になった場合
                private_flag = 1
                video_data = pd.DataFrame(data=[[id, private_flag]], columns=["video_id", "private_flag"])
                self.video_stats = pd.concat([self.video_stats, video_data], ignore_index=True)

                print("動画が非公開の可能性があります")

            else:
                ch_name = res["items"][0]["snippet"]["channelTitle"]
                ch_id = ch_id = res["items"][0]["snippet"]["channelId"]
                ch_url = r"https://www.youtube.com/channel/" + ch_id + r"/videos"
                title = str(res["items"][0]["snippet"]["title"])

                published_date = res["items"][0]["snippet"]["publishedAt"]    #日本標準時に変更
                published_date = pd.to_datetime(published_date, format="%Y-%m-%d %H:%M:%S")
                published_date += datetime.timedelta(hours=9)
                published_date = published_date.replace(tzinfo=None)

                private_flag = 0

                try:
                    comment_count = res["items"][0]["statistics"]["commentCount"]
                except KeyError as e:
                    comment_count = 0
                    print(i, id, "コメント欄が非公開です")

                try:
                    view_count = int(res["items"][0]["statistics"]["viewCount"])
                except KeyError as e:
                    print(i, id, "メンバーシップ限定公開の可能性があります")
                    private_flag = 2
                    view_count = 0

                try:
                    like_count = int(res["items"][0]["statistics"]["likeCount"])
                except KeyError as e:
                    like_count = 0
                    print(i, id, "高評価数が非公開です")

                video_data = pd.DataFrame(data=[[id, ch_name, ch_url, title, published_date, private_flag, like_count, comment_count, view_count]], 
                                            columns=["video_id", "ch_name", "ch_url", "title", "published_date", "private_flag", "like_count", \
                                                "comment_count", "view_count"])
                self.video_stats = pd.concat([self.video_stats, video_data], ignore_index=True)
                print("key_number:", self.key_number, i, id, published_date, view_count)
                if i == 0:
                    self.video_stats = self.video_stats.astype({"title": "str", "like_count": "int", "view_count": "int"})  #int型に指定         

        #print(self.video_stats)
        return self.video_stats

    def serch_new_video(self, ch_list, current_id_list=[]):
        #ch_listからAPIを利用して更新された動画のvideo_idリストを返す ch_listは調べたいchのリスト
        #current_id_listはデータベースに登録されているvideo_idのリストfetch_video_idでとってきたもの
        new_id_list = []
        break_flag = False

        for ch_url in ch_list.values():
            pattern = re.compile(r'https://www.youtube.com/|channel/|/videos')

            ch_id = pattern.split(ch_url)
            ch_id = ch_id[2]    #ch_urlからch_idを取得

            st_dt = None
            ed_dt = None
            duplicate_flag = False

            if break_flag:
                break

            while duplicate_flag == False:
                if break_flag:
                    break
                for i in range(30):
                    try:
                        new_videos = self.youtube.search().list(part="snippet", 
                                                                channelId=ch_id, 
                                                                publishedAfter=st_dt, 
                                                                publishedBefore=ed_dt, 
                                                                maxResults=50, 
                                                                order="date", 
                                                                type="video").execute()
                        #channelIdに指定したチャンネルから最新の動画50件を取得
                        break
                    except HttpError as e :
                        print(type(e), "APIクオートが上限に達しました。次のキーを使用します。", "next_key_number: ", 1 + int(self.key_number))
                        try:
                            self.next_key()
                        except StopIteration as e:
                            print(type(e), "APIクオートが上限に達しました。youtube_APIを終了します")
                            break_flag = True
                            break

                if new_videos.get("items") == []:   #動画がAPIが返さない場合は検索を終了
                    duplicate_flag = True

                for new_video in new_videos.get("items"):
                    if new_video["id"]["kind"] == "youtube#video" and new_video["snippet"]["liveBroadcastContent"] == "none":
                        #playlistと未公開動画を回避するためのif文
                        video_id = new_video["id"]["videoId"]
                        published_date = new_video["snippet"]["publishedAt"]

                        if not video_id in current_id_list and not video_id in new_id_list:    #データベースに登録されていない場合のみ追加
                            new_id_list.append(video_id)

                            ed_dt = pd.to_datetime(published_date) - relativedelta(seconds=1)
                            st_dt = ed_dt - relativedelta(months=3)
                            ed_dt = ed_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                            st_dt = st_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

                            print(ed_dt, st_dt, video_id)

                        elif video_id in current_id_list:
                            duplicate_flag = True
                            print("新規動画の検索を終了します")
                            break

        print("新たな動画は"+ str(len(new_id_list)) + "件でした")

        self.extract_info(new_id_list)
        return self.video_stats

    def save(self):
        f = open("./データ/video_stats.pkl", "wb")
        pickle.dump(self.video_stats, f)
        print(self.video_stats)

class api_to_mysql(selenium_to_mysql):
    def __init__(self, dt_now=datetime.datetime.now(), video_data=None, user="root", passwd="Takanori6157", host="localhost", db="holo_analyze"):
        super().__init__(dt_now=dt_now, video_data=video_data, user=user, passwd=passwd, host=host, db=db)

    def api_update(self):
        try:
            self.cursor.execute(f"alter table {self.current_tbl} add `{self.last_update}` int")    #数字のみのカラム名は作成できないため``で囲む
        except OperationalError as e:
            print(type(e), "既に生成済のカラムです")

        id_list = self.fetch_video_id()

        for index, row in self.data.iterrows():
            private_flag = row["private_flag"]
            video_id = str(row["video_id"])

            if private_flag == 1:
                self.cursor.execute(f"update video_stats set private_flag = '{private_flag}' where video_id='{video_id}'")
                continue

            if not video_id in id_list:    #video_idがまだデータベースにない場合
                self.cursor.execute(f"""insert into video_stats 
                                    (video_id) values ('{video_id}')""")

            ch_name = row["ch_name"]
            ch_url = row["ch_url"]

            title = row["title"]    #titleのエスケープ処理
            if not title.find("'") == -1:    #シングルクオーテーション(')を含む場合は-1以外を返す
                title = title.replace("'", "\\'")

            published_date = row["published_date"]
            last_update = self.last_update
            like_count = row["like_count"]
            comment_count = row["comment_count"]
            view_count = row["view_count"]

            #video_statsの更新
            print(index, video_id, title)
            if private_flag == 0:
                self.cursor.execute(f"""update video_stats set
                                    view_count = {view_count} where video_id='{video_id}'""")

            self.cursor.execute(f"""update video_stats set
                                ch_name = '{ch_name}',
                                title = '{title}',
                                published_date = '{published_date}',
                                last_update = '{last_update}',
                                private_flag = '{private_flag}',
                                like_count = {like_count},
                                comment_count = {comment_count} 
                                where video_id='{video_id}'""")

            #ch_infoの更新
            self.cursor.execute(f"update ch_info set ch_name = '{ch_name}' where ch_url ='{ch_url}'")
            #viewsの更新
            self.cursor.execute(f"update {self.current_tbl} set `{self.last_update}`= {view_count} where video_id='{video_id}'")

        self.con.commit()

    def fetch_video_id(self):    #video_idのリストを返す
        self.cursor.execute("select video_id from video_stats")
        rows = self.cursor.fetchall()
        rows = pd.DataFrame(rows)
        rows = list(rows[:][0])

        return rows

    def fetch_latest_video(self, days_ago=30):     #days_agoに日数と指定してデータベースから直近 N 日の video_id を検索し、リストで返す
        dt_now=datetime.datetime.now()
        dt_delta = datetime.timedelta(days=days_ago)
        dt_now -= dt_delta
        dt_now = dt_now.strftime("%Y-%m-%d %H:%M:%S")

        self.cursor.execute(f"select video_id from video_stats where published_date > '{dt_now}'")
        rows = self.cursor.fetchall()
        rows = pd.DataFrame(rows)
        rows = list(rows[:][0])

        print("直近" + str(days_ago) + "日間の動画は" + str(len(rows)) + "件です")
        return rows

    def assign_published_index(self):
        self.cursor.execute("""update 
                            video_stats as t1, 
                            (SELECT video_id, row_number() over(order by published_date, video_id) dt from video_stats) as t2
                            set t1.published_index = t2.dt
                            where t1.video_id = t2.video_id""")
        self.con.commit()


if __name__ == "__main__":

    mysql = api_to_mysql()

    current_id_list = mysql.fetch_video_id()
    
    ch_list_path = "ch_list.json"
    ch_list = open_json(ch_list_path)

    youtube = ytd_api(key_list)
    video_data = youtube.serch_new_video(ch_list, current_id_list)
    video_data = youtube.extract_info(current_id_list)
    youtube.save()

    mysql = api_to_mysql(video_data = video_data)
    mysql.api_update()
    mysql.assign_published_index()
    mysql.close()


    #lists = pickle_load_list()

    #video_data = pickle_load()    #selenium_to mysqlでvideo_idをpickleで保存した場合

    """
    youtube = ytd_api(key_list)

    video_data = pickle_load()    #selenium_to mysqlでvideo_idをpickleで保存した場合
    print(video_data["video_id"])
    mysql = api_to_mysql(video_data = video_data)
    mysql.api_update()
    mysql.assign_published_index()
    mysql.close()
    """

