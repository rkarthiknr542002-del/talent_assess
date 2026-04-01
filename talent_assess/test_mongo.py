import pymongo

try:
    client = pymongo.MongoClient('mongodb://localhost:27017/')
    
    client.admin.command('ping')
    print(" MongoDB connection successful!")
    
    dbs = client.list_database_names()
    print(" Available databases:", dbs)
    
    client.close()
    
except Exception as e:
    print(" Connection failed:", str(e))
    print(" Solution: Check if MongoDB service is running")