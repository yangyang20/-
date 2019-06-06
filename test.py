import pymysql

singerInformation = {
    'singClassify':'中国',
    'singer':'罗阳',
    'singId':123456789
}

conn = pymysql.connect(host='localhost',
                             port=3306,
                             user='root',
                             password='393622951',
                             db='WangYiYun',
                             charset='utf8')
cur = conn.cursor()
effect_row = cur.execute('INSERT INTO `singerInformation`( `singClassify`,`singer`,`singId`) VALUES (%(singClassify)s, %(singer)s ,%(singId)s)',singerInformation)
#effect_row = cur.execute('INSERT INTO `singerInformation` (`singClassify`,`singer`,`singId`) VALUES (%s, %s, %s)', ('mary','luoy' ,'18'))
print(effect_row)
conn.commit()
cur.close()
conn.close()