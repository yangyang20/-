import pymysql
def insert_db():
    client = pymongo.MongoClient(MONGODB_URL)
    db = client[MONGODB_DB]
    table = db[MONGODB_TABLE]
    # 数据再次插入的时候避免重复
    table.update({'_id': songDdetails['_id']}, {'$set': songDdetails}, True)
    # result = table.insert_one(songDdetails)