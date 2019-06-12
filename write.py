import pymongo
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
import pymysql
from config import *
import requests

session = requests.session()
headers ={
    'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0',
    'X-Requested-With':'XMLHttpRequest'
}
#歌曲详情
songDdetails = {}

def selectSingerID():
    conn = pymysql.connect(host='127.0.0.1', user='root', password="393622951", db='WangYiYun')
    cur = conn.cursor()
    # 查询歌手的id
    sql = "SELECT singId FROM singerInformation WHERE singer LIKE '%邓紫%'"
    effect_row = cur.execute(sql)
    if effect_row:
        # 返回结果是一个元组
        singId =  cur.fetchone()
    cur.close()
    conn.close()
    singId = singId[0]
    selectSong(singId)

def selectSong(singId):
    global songDdetails
    client = pymongo.MongoClient(MONGODB_URL)
    db = client[MONGODB_DB]
    table = db[MONGODB_TABLE]
    # 条件查询
    results = table.find({'singId': singId})
    # 还可以指定返回字段
    # results = table.find({'singId':singId},{'downloadURL':1,'_id':0})
    # 将查询结果转为一个列表
    results = list(results)
    print(len(results))
    for item in results:
        print(item)
        songDdetails = item
        download()


def download():
    response = session.get(url=songDdetails['downloadURL'],headers=headers)
    file = open('/home/yang/Music/'+songDdetails['songName']+'.mp3','wb')
    file.write(response.content)
    file.close()
    write()

# 写入歌曲作者,专辑,图片信息
def write():
    # img = open("/home/yang/PycharmProjects/网易云音乐音乐/"+"img.webp","wb")
    # res = session.get(url=songDdetails['singer_pic'],headers=headers)
    # img.write(res.content)
    # img.close()
    audio = ID3("/home/yang/Music/"+songDdetails['songName'] + '.mp3')
    # audio['APIC'] = APIC(  # 插入专辑图片
    #     encoding=3,
    #     mime='webp',
    #     type=3,
    #     desc=u'Cover',
    #     data=img.read()
    # )
    audio['TIT2'] = TIT2(  # 插入歌名
        encoding=3,
        text=songDdetails['songName']
    )
    audio['TPE1'] = TPE1(  # 插入第一演奏家、歌手、等
        encoding=3,
        text=songDdetails['singer']
    )
    audio.save()


if __name__ == '__main__':
    selectSingerID()


