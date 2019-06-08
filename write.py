import pymongo
import pymysql
from config import *
import requests

session = requests.session()
headers ={
    'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0',
    'X-Requested-With':'XMLHttpRequest'
}


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
    client = pymongo.MongoClient(MONGODB_URL)
    db = client[MONGODB_DB]
    table = db[MONGODB_TABLE]

    results = table.find({'singId': singId})
    # 还可以指定返回字段
    # results = table.find({'singId':singId},{'downloadURL':1,'_id':0})
    # 将查询结果转为一个列表
    results = list(results)
    print(len(results))
    for result in results:
        print(results)
        download(result)


def download(songDdetails):
    response = session.get(url=songDdetails['downloadURL'],headers=headers)
    file = open('/media/yang/yang/music/'+songDdetails['songName']+'.mp3','wb')
    file.write(response.content)
    file.close()
    print('成功')


if __name__ == '__main__':
    selectSingerID()


