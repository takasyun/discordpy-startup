from discord.ext import commands
import os
import traceback
import time
import requests
import json
import copy
from datetime import datetime, timedelta, timezone

bot = commands.Bot(command_prefix='/')
token = os.environ['DISCORD_BOT_TOKEN']


@bot.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, "original", error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)


@bot.command()
async def ping(ctx):
    await ctx.send('pong')




Hololive = {
    "UCx1nAvtVDIsaGmCMSe8ofsQ": [
        "加藤純一",
        "https://yt3.ggpht.com/ytc/AAUvwnhmkQKAZWonAFY4aNoq6dOwgfThDWTRfa2NXH6_DQ=s88-c-k-c0x00ffffff-no-rj"
    ],
    "UCt30jJgChL8qeT9VPadidSw": [
        "しぐれうい ",
        "https://yt3.ggpht.com/ytc/AAUvwniuo8k4PtT6z_AsalVyQbz6BUpTebJVt22kZDw8Ig=s88-c-k-c0x00ffffff-no-rj"
    ],
    "UC1opHUrw8rvnsadT-iGp7Cg": [
        "湊あくあ",
        "https://yt3.ggpht.com/ytc/AAUvwngPGs1t6iJAT6hLWj7cBQcvJg2y_L9mzpy3lpxgqw=s88-c-k-c0x00ffffff-no-rj"
    ],
    "UC5CwaMl1eIgY8h02uZw7u8A": [
        "星町すいせい",
        "https://yt3.ggpht.com/ytc/AAUvwnjdAl5rn3IjWzl55_0-skvKced7znPZRuPC5xLB=s88-c-k-c0x00ffffff-no-rj"
    ],
    "UC1DCedRgGHBdm81E1llLhOQ": [
        "兎田ぺこら",
        "https://yt3.ggpht.com/ytc/AAUvwnjvkyPGzOmEXZ34mEFPlwMKTbCDl1ZkQ_HkxY-O5Q=s88-c-k-c0x00ffffff-no-rj"
    ]
} #配信者のチャンネルID, 配信者名, アイコン画像のURLのリスト

webhook_url_Hololive = 'https://discord.com/api/webhooks/851400687333146655/k9JmrIOgIi0u2wlXmUZ_rYL3UKiOadvUKsO4Kr3yY22_w2MX8yMy5eb42skf3-0ld32s' #ホロライブ配信開始
webhook_url_Hololive_yotei = 'https://discord.com/api/webhooks/851400883891601408/OB6R3Q_K6Uj-Xs0pG9J1Y93AODgiwxVxH8z6Rk0_A2Tz7g6aCaqU4kp62YaIYbtaSEI6' #ホロライブ配信予定
broadcast_data = {} #配信予定のデータを格納

YOUTUBE_API_KEY = ["AIzaSyCqELFwupRF390aQT_f0syEuJjHg0sAV2o"
                   ,"AIzaSyA3tKX6i4KkD-rZekM7LlRcBaUxRIgjquI"
                   ,"AIzaSyDpvW2pmQcWfi-8YxfC8SEco03hl_33ODY"
                   ,"AIzaSyA0cq75V7xpqhceobj8DjHb3XvbprWsMSE"
                   ,"AIzaSyD9DEzPe4YIGEangZOnfDjlISZV0rVk1lo"] #複数のAPI(str型)をリストで管理

def dataformat_for_python(at_time): #datetime型への変換
    at_year = int(at_time[0:4])
    at_month = int(at_time[5:7])
    at_day = int(at_time[8:10])
    at_hour = int(at_time[11:13])
    at_minute = int(at_time[14:16])
    at_second = int(at_time[17:19])
    return datetime(at_year, at_month, at_day, at_hour, at_minute, at_second)

def replace_JST(s):
    a = s.split("-")
    u = a[2].split(" ")
    t = u[1].split(":")
    time = [int(a[0]), int(a[1]), int(u[0]), int(t[0]), int(t[1]), int(t[2])]
    if(time[3] >= 15):
      time[2] += 1
      time[3] = time[3] + 9 - 24
    else:
      time[3] += 9
    return (str(time[0]) + "/" + str(time[1]).zfill(2) + "/" + str(time[2]).zfill(2) + " " + str(time[3]).zfill(2) + "-" + str(time[4]).zfill(2) + "-" + str(time[5]).zfill(2))

def post_to_discord(userId, videoId):
    haishin_url = "https://www.youtube.com/watch?v=" + videoId #配信URL
    content = "配信中！\n" + haishin_url #Discordに投稿される文章
    main_content = {
        "username": Hololive[userId][0], #配信者名
        "avatar_url": Hololive[userId][1], #アイコン
        "content": content #文章
    }
    requests.post(webhook_url_Hololive, main_content) #Discordに送信
    broadcast_data.pop(videoId)

def get_information():
    tmp = copy.copy(broadcast_data)
    api_now = 0 #現在どのYouTube APIを使っているかを記録
    for idol in Hololive:
        api_link = "https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=" + idol + "&key=" + YOUTUBE_API_KEY[api_now] + "&eventType=upcoming&type=video"
        api_now = (api_now + 1) % len(YOUTUBE_API_KEY) #apiを1つずらす
        aaa = requests.get(api_link)
        v_data = json.loads(aaa.text)
        try:
            for item in v_data['items']:#各配信予定動画データに関して
                broadcast_data[item['id']['videoId']] = {'channelId':item['snippet']['channelId']} #channelIDを格納
            for video in broadcast_data:
                try:
                    a = broadcast_data[video]['starttime'] #既にbroadcast_dataにstarttimeがあるかチェック
                except KeyError:#なかったら
                    aaaa = requests.get("https://www.googleapis.com/youtube/v3/videos?part=liveStreamingDetails&id=" + video + "&key=" + YOUTUBE_API_KEY[api_now])
                    api_now = (api_now + 1) % len(YOUTUBE_API_KEY) #apiを1つずらす
                    vd = json.loads(aaaa.text)
                    print(vd)
                    broadcast_data[video]['starttime'] = vd['items'][0]['liveStreamingDetails']['scheduledStartTime']
        except KeyError: #配信予定がなくて403が出た
            continue
    for vi in broadcast_data:
        if(not(vi in tmp)):
            print(broadcast_data[vi])
            try:
                post_broadcast_schedule(broadcast_data[vi]['channelId'], vi, broadcast_data[vi]['starttime'])
            except KeyError:
                continue

def check_schedule(now_time, broadcast_data):
    for bd in list(broadcast_data):
        try:
            # RFC 3339形式 => datetime
            sd_time = datetime.strptime(broadcast_data[bd]['starttime'], '%Y-%m-%dT%H:%M:%SZ') #配信スタート時間をdatetime型で保管
            sd_time += timedelta(hours=9)
            if(now_time >= sd_time):#今の方が配信開始時刻よりも後だったら
                post_to_discord(broadcast_data[bd]['channelId'], bd) #ツイート
        except KeyError:
            continue

def post_broadcast_schedule(userId, videoId, starttime):
    st = starttime.replace('T', ' ')
    sst = st.replace('Z', '')
    ssst = replace_JST(sst)
    haishin_url = "https://www.youtube.com/watch?v=" + videoId #配信URL
    content = ssst + "に配信予定！\n" + haishin_url #Discordに投稿される文章
    main_content = {
        "username": Hololive[userId][0], #配信者名
        "avatar_url": Hololive[userId][1], #アイコン
        "content": content #文章
    }
    requests.post(webhook_url_Hololive_yotei, main_content) #Discordに送信

#2時間ごとにget_information()
#1分ごとにcheck_schedule()
# メッセージ受信時に動作する処理
@bot.command()
async def main_discordbot(ctx):
    await ctx.send('start!!!')
    while True:
        now_time = datetime.now() + timedelta(hours=9)
        if(((now_time.minute == 0) or (now_time.minute == 30) or (now_time.minute == 15) or (now_time.minute == 45))):
            get_information()
        check_schedule(now_time, broadcast_data)
        time.sleep(60)
bot.run(token)
