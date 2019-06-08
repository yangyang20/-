from builtins import Exception
import time
from concurrent.futures import ProcessPoolExecutor
import requests
import pymongo
import pymysql
import re
from bs4 import BeautifulSoup
from config import *

headers ={
    'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0',
    'X-Requested-With':'XMLHttpRequest'
}
session = requests.session()
# 歌曲信息
songDdetails = {}
# 歌手信息
singerInformation ={}
# 计数器
Counter = {}

# 获取歌手分类的id
def singClassifyList():
    url = 'https://music.163.com/discover/artist'
    try:
        response = session.get(url=url,headers=headers)
        soup = BeautifulSoup(response.text,"html5lib")
        classify = soup.select(".cat-flag")
        for item in classify:
            # 歌手分类名称
            singerInformation['singClassify'] = item.string
            href = item['href']
            # 解析出歌手分类名称的id
            singerInformation['singClassifyId'] = str(re.findall(r'id=(\d{4})',href))[2:-2]
            if singerInformation['singClassifyId']:
            # 调用多进程分别爬去不同分页
                myProcess()
            # 单进程就使用下面的
            #     for i in range(65, 90):
            #         singPage(i)
    except Exception:
        print('singClassifyList有问题')
        time.sleep(0.1)
        singClassifyList()
# 获取当前歌手分类下的分页信息
def singPage(id):
    url = 'https://music.163.com/discover/artist/cat?id=%s&initial=%s' % (singerInformation['singClassifyId'],id)
    try:
        response = session.get(url=url,headers=headers)
        soup = BeautifulSoup(response.text, "html5lib")
        pageHref = soup.select("#initial-selector a")
        # 循环分页,获取所有分页的歌手href
        for item in pageHref:
            href = item['href']
            result = singList(href)
    except Exception:
        print('singPage有问题')
        print(url)
        time.sleep(0.2)
        # singPage(id)
        return None
# 多进程爬取
def myProcess():
    with ProcessPoolExecutor(max_workers=26) as executor:
        for i in range(65, 90):
            # 创建26个进程，分别执行A-Z分类
            executor.submit(singPage, i)

# 获取所有的歌手的id
def singList(href):
    url = 'https://music.163.com%s' % href
    try:
        response = session.get(url=url,headers=headers)
        soup = BeautifulSoup(response.text,"html5lib")
        singList = soup.select('.nm-icn')
        for item in singList:
            # 歌手名称
            text = item.string
            href = item['href']
            # 解析出的歌手id
            id = str(re.findall(r'id=(\d+)',href))[2:-2]
            songDdetails['singer'] = text
            singerInformation['singer'] = text
            # 以歌手的id为索引,方便查歌曲信息
            singerInformation['singId'] = int(id)
            songDdetails['singId'] = int(id)
            insert_mysql()
            result = singerPopularSong(id)
    except Exception:
        print('singList有问题')
        print(url)
        time.sleep(0.3)
        # singList(href)
        return None
# 获取每个歌手热门歌曲的id
def singerPopularSong(id):
    url = 'https://music.163.com/artist?id=%s' % id
    try:
        response = session.get(url=url,headers=headers)
        soup = BeautifulSoup(response.text,"html5lib")
        a = soup.select("ul.f-hide a")
        for item in a:
            href = item['href']
            text = item.text
            songDdetails['songName'] = text
            # 将链接中的歌曲id解析出来
            songDdetails['_id'] = str(re.findall(r'id=(\d+)',href))[2:-2]
            result = download(songDdetails['_id'])
    except Exception:
        print('singerPopularSong有问题')
        print(url)
        time.sleep(0.4)
        # singerPopularSong(id)
        return None


# 获取所有的榜单id
def rankingList():
    url = 'https://music.163.com/discover/toplist'
    response = session.get(url=url,headers=headers)
    soup = BeautifulSoup(response.text, "html5lib")
    # 获取所有的class为avatar的a标签
    avatar = soup.select('.avatar')
    for item in avatar:
        href = item['href']
        # print(id)
        songList(href)


# 云音乐榜单抓取,url中不能有#号,才是框架源码
def songList(href):
    url = 'https://music.163.com%s' % href
    response = session.get(url=url,headers=headers)
    soup = BeautifulSoup(response.text, "html5lib")
    # 网页数据在<textarea>标签内,先获取到所有歌曲的数据
    songList = soup.find('textarea',id='song-list-pre-data').get_text()
    # 网页数据为字符串,一个列表包含许多歌曲信息的对象
    # 对象内有许多名称相同的key,没有找到较好的转换为json对象的方式
    # 只能正则表达式匹配歌手,歌名,歌曲id信息
    songList = re.findall(r'artists":\[(.*?\d{10}[}|,])',songList)
    for index,item in enumerate(songList):
        # 有些字符串结尾是,先将其转换为}
        if item.endswith('}') == False:
            item = re.sub(r',$','}',item)
        # 匹配到所有的name值,
        nameList = re.findall(r'"name":"(.*?)",',item)
        # 以第一个name值为歌手
        songDdetails['singer'] = nameList[0]
        # 以最后一个name值为歌曲名
        songDdetails['songName'] = nameList[-1]
        # 匹配歌曲的id值
        idList = re.findall(r',"id":(\d+)}',item)
        # 由于名为id的key有重复,如果匹配到多次,取最后一个id的值
        if len(idList)>1:
            songDdetails['_id'] = str(idList[-1])
        songDdetails['_id'] = str(idList)
        songDdetails['_id'] = songDdetails['_id'][2:-2]
        if songDdetails['_id']:
            # len(idList)这个判断总是出现遗漏,再次排除多id的情况
            if len(songDdetails['_id'])>10:
                songDdetails['_id'] = re.findall(r',\'(\d+)',songDdetails['_id'])
            print(songDdetails['_id'])
            download(songDdetails['_id'])
        else:
            print('为空')


# 我的喜欢歌曲列表,此处参数特点还不明确,可以获得歌曲信息
def songMessage():
    url = 'https://music.163.com/weapi/v3/playlist/detail?csrf_token=75097dfb0b9d61d1a7c8eae8e191bef0'
    datas = {
        'params': 'UiQeYTPku7HXOqfZ++LRrTy5tNd1brm0Vznvn63eIIUwKpG63kTbfqHIyZDLrXlCMU8UupHfWhnjeTT61IMarmYU4oBpUGsFZqcNupx2S9hp2NQr1/ZK7mPYYI+Wd2AkK2iyTYiulWVt83d6h5LTpYgooIP9+P4KM5FaunBQZt6YLX+tP/yQKyWKa+wGddghN0ZPwNlyfX4LQYermdAOqmueKbiaNg3J0cd7G9GxSik=',
        'encSecKey': 'd691207d35dc3f4a8dd67ee722232f4fe2e20db553f83c4c037c90772d88e8cde3d9188458a3b9398899d61796cc4f4e09d0176da5ec579fe9761ae4ea65b9c64235535a8eb758578fe3f29dd1ca5f4ef16581172996e365233313ee6cf0f386bd04d061660c38b61f9c714a9893c9c415cb8d28709a0616f3a9f06e1b850f01'
    }
    response = session.post(url=url, headers=headers, data=datas)
    tracks = response.json()['playlist']['tracks']
    for track in tracks:
        songDdetails['songName'] = track['name']
        songDdetails['singer'] = track['ar'][0]['name']
        songDdetails['Album'] = track['al']['name']
        songDdetails['picUrl'] = track['al']['picUrl']
        songDdetails['_id'] = track['id']
        download(songDdetails['_id'])
        print(songDdetails)

# 根据歌曲的id值下载歌曲
def download(id):
    url = 'http://music.163.com/song/media/outer/url?id=%s.mp3' % id
    songDdetails['downloadURL'] = url
    print(songDdetails)
    # music = open('J:/music/' + songDdetails['songName']+'.mp3','wb')
    try:
        response = session.get(url=url,headers=headers)
        if response.status_code == 200:
            # music.write(response.content)
            # music.close()
            # return 1
            insert_db()
        else:
            return None
    except Exception:
        print('download有问题')
        time.sleep(0.5)
        # download(id)
        return None

# 存入数据库歌曲信息
def insert_db():
    client = pymongo.MongoClient(MONGODB_URL)
    db = client[MONGODB_DB]
    table = db[MONGODB_TABLE]
    # 数据再次插入的时候避免重复
    table.update({'_id': songDdetails['_id']}, {'$set': songDdetails}, True)
    # result = table.insert_one(songDdetails)

# 存入歌手分类与歌手信息
def insert_mysql():
    conn = pymysql.connect(host='127.0.0.1', user='root', password="393622951", db='WangYiYun')
    cur = conn.cursor()
    # 字典的插入方式
    effect_row = cur.execute(
        'INSERT IGNORE INTO `singerInformation`( `singClassify`,`singClassifyId`,`singer`,`singId`) VALUES (%(singClassify)s,%(singClassifyId)s, %(singer)s ,%(singId)s)',
        singerInformation)
    if effect_row:
        # 这一步才是真正的提交数据
        conn.commit()
    effect = cur.execute(
        'INSERT IGNORE INTO `songsClassifiedNames`( `singClassifyId`,`singClassify`) VALUES (%s,%s)',
        (singerInformation['singClassifyId'],singerInformation['singClassify']))
    if effect:
        conn.commit()
    cur.close()
    conn.close()


if __name__=='__main__':
    # 根据榜单抓取
    # rankingList()
    # 根据歌手抓取
    singClassifyList()