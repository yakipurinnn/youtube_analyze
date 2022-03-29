#youtube apiを用いて動画情報を取得する
#idはseleniumから取得する

#参照元: https://qiita.com/g-k/items/7c98efe21257afac70e9#%E5%8F%AF%E8%A6%96%E5%8C%96%E3%81%97%E3%81%A6%E3%81%BF%E3%82%8B
#日時計算など: https://note.nkmk.me/python-datetime-pytz-timezone/
#youtube api 500件以上取得できなくなる問題について: https://zenn.dev/jqinglong/articles/1161615fdaa6f6

import pandas as pd
import numpy as np
import os
import pickle
import re
import MySQLdb
import datetime
import urllib.request
from logging import exception
from multiprocessing.reduction import duplicate
from MySQLdb._exceptions import OperationalError
from dateutil.relativedelta import relativedelta
from urllib.error import HTTPError
from youtube_sql2 import selenium_to_mysql
from youtube_sql2 import open_json
from apiclient.discovery import build
from apiclient.errors import HttpError


def pickle_load_id():
    """
    pickeleで保存したpandasデータを開き、video_idのリストを返す
    """
    with open("データ/video_stats.pkl", "rb") as f:
        video_id = pickle.load(f)
        video_id = list(video_id["video_id"])

        return video_id

def pickle_load():    #pandasで保存したdata_frameを返す
    """
    pandasで保存したデータをdata frame形式で返す
    """
    with open("データ/video_stats.pkl", "rb") as f:
        video_data = pickle.load(f)

        return video_data

class ytd_api:
    """
    youtube apiを利用し、動画のデータを取得する。
    以下メソッドについて、extract_infoは動画の詳細情報を取得する。
    serch_new_videoは指定したチャンネルの新たな動画を検索する。
    saveはpickele形式で取得したデータを保存する。
    """
    def __init__(self, api_key_list):
        self.video_stats = pd.DataFrame(columns=["video_id", "ch_name", "ch_url", "title", "published_date", "thumbnail_url"\
                                                    "private_flag", "membership_flag", "comment_flag", "likecount_flag", "comment_count", "like_count", "view_count"])
        
        self.ch_stats = pd.DataFrame(columns=["ch_id", "ch_name", "published_date", "thumbnail_url", "deleted_flag", "subscriber_count", "video_count", "view_count"])
        
        self.api_key_list = iter(api_key_list.keys())
        self.key_number_list = iter(api_key_list.values())

        self.ytd_apikey = next(self.api_key_list)   #youtube_apiキーを順に取り出す
        self.key_number = next(self.key_number_list)    #youtube_apiキーの番号を取り出す

        self.youtube = build("youtube", "v3", developerKey=self.ytd_apikey)

    def next_key(self, e, break_flag=False):    #再帰関数使った方がきれい(未実装)
        """
        youtube api keyのリストから次のキーを呼びだす
        引数についてbreak_flagは基本的にFalse
        eはerror class
        """
        break_flag = break_flag
        print(type(e), "APIクオートが上限に達しました。次のキーを使用します。", "next_key_number: ", 1 + int(self.key_number))

        try:
            self.ytd_apikey = next(self.api_key_list)
            self.key_number = next(self.key_number_list )
            self.youtube = build("youtube", "v3", developerKey=self.ytd_apikey)
        except StopIteration as e :
            print(type(e), "APIクオートが上限に達しました。youtube_APIを終了します")
            break_flag = True
        
        return break_flag

    def get_ch_id(self, ch_url):
        pattern = re.compile(r'https://www.youtube.com/|channel/|/videos')
        ch_id = pattern.split(ch_url)
        ch_id = ch_id[2]    #ch_urlからch_idを取得

        return ch_id

    def extract_info(self, id_list):
        """
        youtube api を利用して各動画の詳細なデータを取得する。
        返り値はpandas.dataframeの形式
        引数には調べたい動画のIDのリストを渡す
        """
        for i, id in enumerate(id_list):
            break_flag = False
            for j in range(30):
                try:
                    res = self.youtube.videos().list(part='snippet,statistics', id = id).execute()
                    break
                except HttpError as e :
                    break_flag = self.next_key(e, break_flag)
                    if break_flag:
                        break
            if break_flag:
                break

            if res["items"] == []:    #動画が非公開になった場合
                private_flag = 1
                video_data = pd.DataFrame(data=[[id, private_flag]], columns=["video_id", "private_flag"])
                self.video_stats = pd.concat([self.video_stats, video_data], ignore_index=True)

                print(id, "動画が非公開の可能性があります")

            else:
                ch_name = res["items"][0]["snippet"]["channelTitle"]
                ch_id = ch_id = res["items"][0]["snippet"]["channelId"]
                ch_url = r"https://www.youtube.com/channel/" + ch_id + r"/videos"
                title = str(res["items"][0]["snippet"]["title"])

                published_date = res["items"][0]["snippet"]["publishedAt"]    #日本標準時に変更
                published_date = pd.to_datetime(published_date, format="%Y-%m-%d %H:%M:%S")
                published_date += datetime.timedelta(hours=9)
                published_date = published_date.replace(tzinfo=None)

                thumbnail_url = res["items"][0]["snippet"]["thumbnails"]["medium"]["url"]    #動画サムネイルのURL

                private_flag = 0    #private_flagについて 0: 通常 1: 非公開または削除 2: メンバー限定公開 (再生数確認できない) 3: 評価数非公開 4: コメント欄非公開
                memmbership_flag = 0
                comment_flag = 0
                likecount_flag = 0

                try:
                    view_count = int(res["items"][0]["statistics"]["viewCount"])
                except KeyError as e:
                    print(i, id, "メンバーシップ限定公開の可能性があります")
                    memmbership_flag = 1
                    view_count = 0

                try:
                    like_count = int(res["items"][0]["statistics"]["likeCount"])
                except KeyError as e:
                    like_count = 0
                    likecount_flag = 1
                    print(i, id, "高評価数が非公開です")

                try:
                    comment_count = res["items"][0]["statistics"]["commentCount"]
                except KeyError as e:
                    comment_count = 0
                    comment_flag = 1
                    print(i, id, "コメント欄が非公開です")

                video_data = pd.DataFrame(data=[[id, ch_name, ch_url, title, published_date,\
                                                thumbnail_url, private_flag, memmbership_flag, comment_flag, likecount_flag,\
                                                like_count, comment_count, view_count]], 
                                            columns=["video_id", "ch_name", "ch_url", "title", "published_date",\
                                                "thumbnail_url", "private_flag", "membership_flag", "comment_flag", "likecount_flag",\
                                                    "like_count", "comment_count", "view_count"])
                self.video_stats = pd.concat([self.video_stats, video_data], ignore_index=True)
                print("key_number:", self.key_number, i, id, published_date, view_count)

                if i == 0:
                    self.video_stats = self.video_stats.astype({"title": "str", "like_count": "int", "view_count": "int"})  #int型に指定         

        #print(self.video_stats)
        return self.video_stats

    def serch_new_video(self, ch_list, current_id_list=[]):
        """ 
        ch_listからAPIを利用して更新された新たな動画のvideo_idリストを返す。
        引数ch_listは調べたいchのリスト\{チャンネル名: URL\}の形式のjsonリスト。
        current_id_listはデータベースに登録されているvideo_idのリスト。基本的にfetch_video_idでとってきたもの
        """
        new_id_list = []
        break_flag = False

        for ch_url in ch_list.values():
            ch_id = self.get_ch_id(ch_url)

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
                        break_flag = self.next_key(e, break_flag)
                        if break_flag:
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
                            print(ch_id, "新規動画の検索を終了します")
                            break

        print("新たな動画は"+ str(len(new_id_list)) + "件でした")

        self.extract_info(new_id_list)
        return self.video_stats

    def extract_ch_info(self, ch_list):
        """
        youtubeチャンネルの情報を取得する
        引数ch_listは\{チャンネル名: チャンネルの動画欄URL\}のjsonファイル
        """
        break_flag = False
        for i, ch_url in enumerate(ch_list.values()):
            ch_id = self.get_ch_id(ch_url)

            for j in range(30):
                try:
                    res = self.youtube.channels().list(part='snippet,statistics,brandingSettings', id = ch_id).execute()
                except HttpError as e :
                    break_flag = self.next_key(e, break_flag)
                    if break_flag:
                        break
                if break_flag:
                    break

            deleted_flag = 0
            try:    #チャンネルが削除された場合
                res["items"]
            except KeyError as e:
                deleted_flag = 1
                print(ch_id, "チャンネルが削除された可能性があります")
                continue

            ch_name  = res["items"][0]["snippet"]["title"]
            published_date = res["items"][0]["snippet"]["publishedAt"]
            thumbnail_url = res["items"][0]["snippet"]["thumbnails"]["medium"]["url"]

            hidden_subscriber_count = res["items"][0]["statistics"]["hiddenSubscriberCount"]

            if not hidden_subscriber_count:    #hidden_subscriber_countは登録者数非公開の場合はTrueを返す
                subscriber_count = res["items"][0]["statistics"]["subscriberCount"]

            video_count = res["items"][0]["statistics"]["videoCount"]
            view_count = res["items"][0]["statistics"]["viewCount"]

            ch_data = pd.DataFrame(data=[[ch_id, ch_name, published_date, thumbnail_url, deleted_flag, subscriber_count, video_count, view_count]], 
                                            columns=["ch_id", "ch_name", "published_date", "thumbnail_url", "deleted_flag", "subscriber_count", "video_count", "view_count"])
            self.ch_stats = pd.concat([self.ch_stats, ch_data], ignore_index=True)
            print("key_number:", self.key_number, i, ch_id, view_count)

        return self.ch_stats

    def save(self):
        """
        取得したpandas.dataframeをpickle形式で保存する
        """
        f = open("./データ/video_stats.pkl", "wb")
        pickle.dump(self.video_stats, f)
        print(self.video_stats)


class api_to_mysql(selenium_to_mysql):
    def __init__(self, dt_now=datetime.datetime.now(), video_data=None, ch_data=None, user="root", passwd="Takanori6157", host="localhost", db="holo_analyze"):
        super().__init__(dt_now=dt_now, video_data=video_data, user=user, passwd=passwd, host=host, db=db)
        self.ch_data = ch_data

    def api_update(self):
        try:
            self.cursor.execute(f"alter table {self.current_tbl} add `{self.last_update}` int")    #数字のみのカラム名は作成できないため``で囲む
        except OperationalError as e:
            print(type(e), "既に生成済のカラムです")

        id_list = self.fetch_video_id()

        for index, row in self.data.iterrows():
            private_flag = row["private_flag"]
            membership_flag = row["membership_flag"]
            comment_flag = row["comment_flag"]
            likecount_flag = row["likecount_flag"]
            video_id = str(row["video_id"])
            last_update = self.last_update

            if private_flag == 1:    #非公開の場合
                self.cursor.execute(f"""update video_stats set
                                    private_flag = '{private_flag}', 
                                    last_update = '{last_update}'
                                    where video_id = '{video_id}'""")
                continue

            if not video_id in id_list:    #video_idがまだデータベースにない場合
                self.cursor.execute(f"""insert into video_stats 
                                    (video_id) values ('{video_id}')""")

            ch_name = row["ch_name"]

            title = row["title"]    #titleのエスケープ処理
            if not title.find("'") == -1:    #シングルクオーテーション(')を含む場合は-1以外を返す
                title = title.replace("'", "\\'")

            published_date = row["published_date"]
            thumbnail_url = row["thumbnail_url"]
            like_count = row["like_count"]
            comment_count = row["comment_count"]
            view_count = row["view_count"]

            #video_statsの更新
            print(index, video_id, title)
            if membership_flag == 0:    #メンバーシップ限定公開
                self.cursor.execute(f"""update video_stats set
                                    view_count = {view_count}
                                    where video_id='{video_id}'""")

            if comment_flag == 0:    #コメント欄非公開
                self.cursor.execute(f"""update video_stats set
                                    comment_count = {comment_count}
                                    where video_id='{video_id}'""")

            if likecount_flag == 0:    #評価数非公開
                self.cursor.execute(f"""update video_stats set
                                    like_count = {like_count}
                                    where video_id='{video_id}'""")

            self.cursor.execute(f"""update video_stats set
                                ch_name = '{ch_name}',
                                title = '{title}',
                                published_date = '{published_date}',
                                last_update = '{last_update}',
                                thumbnail_url = '{thumbnail_url}',
                                private_flag = '{private_flag}',
                                membership_flag = '{membership_flag}',
                                comment_flag = '{comment_flag}',
                                likecount_flag = '{likecount_flag}'
                                where video_id = '{video_id}'""")

            #viewsの更新
            self.cursor.execute(f"update {self.current_tbl} set `{self.last_update}`= {view_count} where video_id='{video_id}'")

        self.conn.commit()

    def api_ch_update(self):
        ch_list = self.fetch_ch_id()

        for index, row in self.ch_data.iterrows():
            deleted_flag = row["deleted_flag"]
            ch_id = str(row["ch_id"])

            if deleted_flag == 1:
                self.cursor.execute(f"update ch_stats set deleted_flag = '{deleted_flag}' where video_id='{ch_id}'")
                continue
            
            if not ch_id in ch_list:    #ch_idがまだデータベースに登録されていない場合
                self.cursor.execute(f"""insert into ch_stats 
                                    (ch_id) values ('{ch_id}')""")

            ch_name = row["ch_name"]
            published_date = row["published_date"]
            last_update = self.last_update
            thumbnail_url = row["thumbnail_url"]
            subscriber_count = row["subscriber_count"]
            video_count = row["video_count"]
            view_count = row["view_count"]

            print(index, ch_id, ch_name)
            self.cursor.execute(f"""update ch_stats set
                                ch_name = '{ch_name}',
                                published_date = '{published_date}',
                                last_update = '{last_update}',
                                thumbnail_url = '{thumbnail_url}',
                                deleted_flag = '{deleted_flag}',
                                subscriber_count = {subscriber_count},
                                video_count = {video_count},
                                view_count = {view_count} 
                                where ch_id='{ch_id}'""")

        self.conn.commit()


    def fetch_video_id(self):    #video_idのリストを返す
        self.cursor.execute("select video_id from video_stats")
        rows = self.cursor.fetchall()
        rows = pd.DataFrame(rows)
        try:    #データベースが空の場合の回避
            rows = list(rows[:][0])
        except KeyError as e:
            rows = []

        return rows


    def fetch_ch_id(self):    #ch_idのリストを返す
        self.cursor.execute("select ch_id from ch_stats")
        rows = self.cursor.fetchall()
        rows = pd.DataFrame(rows)
        try:
            rows = list(rows[:][0])
        except KeyError as e:
            rows = []

        return rows


    def fetch_latest_video(self, days_ago=30):
        """
        days_agoに日数を指定してデータベースから直近 N 日の video_id を検索し、リストで返す
        """
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

    def assign_published_index(self):    #投稿日時順にindexを振る
        self.cursor.execute("""update 
                            video_stats as t1, 
                            (SELECT video_id, row_number() over(order by published_date, video_id) dt from video_stats) as t2
                            set t1.published_index = t2.dt
                            where t1.video_id = t2.video_id""")
        self.conn.commit()

class save_thumbnail:
    def __init__(self, video_id_list, user="root", passwd="Takanori6157", host="localhost", db="holo_analyze"):
        self.conn = MySQLdb.connect(user=user, passwd=passwd, host=host, db=db)    #mysqlに接続
        self.cursor = self.conn.cursor()
        self.video_data = video_id_list

    def save_video_thumbnail(self, thumbnail_url_list):
        for i, row in self.video_data.iterrows():
            video_id = row["video_id"]
            thumbnail_url = row["thumbnail_url"]
            ch_name = row["ch_name"]

            self.cursor.execute(f"select ch_id from ch_stats where ch_name = '{ch_name}'")
            ch_id = self.cursor.fetchall()[0][0]

            dst_path = os.path.join("video_thumbnails", ch_id, video_id) + ".jpg"

            with urllib.request.urlopen(thumbnail_url) as web_img:
                data = web_img.read()
                with open(dst_path, mode="wb") as local_img:
                    local_img.write(data)


if __name__ == "__main__":

    key_list_path = "key_list.json"
    key_list = open_json(key_list_path)

    ch_list_path = "ch_list.json"
    ch_list = open_json(ch_list_path)

    mysql = api_to_mysql()

    current_id_list = mysql.fetch_video_id()

    youtube = ytd_api(key_list)
    video_data = youtube.serch_new_video(ch_list, current_id_list)
    video_data = youtube.extract_info(current_id_list)
    ch_data = youtube.extract_ch_info(ch_list)
    youtube.save()

    mysql = api_to_mysql(video_data = video_data, ch_data=ch_data)
    mysql.api_update()
    mysql.api_ch_update()
    mysql.assign_published_index()
    mysql.close()


    """
    video_data = pickle_load()    #selenium_to mysqlでvideo_idをpickleで保存した場合

    mysql = api_to_mysql(video_data = video_data)
    mysql.api_update()
    mysql.assign_published_index()
    mysql.close()
    """

    #mysql = api_to_mysql(video_data = video_data)


