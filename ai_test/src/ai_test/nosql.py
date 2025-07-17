import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_PORT = os.getenv("MONG_PORT", "27017") # 기본값 설정
DB_NAME = os.getenv("DB_NAME")

_mongo_client: Optional[AsyncIOMotorClient] = None
_database_instance: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb():
    global _mongo_client, _database_instance
    if _mongo_client is None:
        try:
            connection_string = f"mongodb://{MONGO_URI}:{MONGO_PORT}/"
            _mongo_client = AsyncIOMotorClient(connection_string)
            _database_instance = _mongo_client.get_database(DB_NAME)
            print("MongoDB에 성공적으로 연결되었습니다.")
        except Exception as e:
            print(f"MongoDB 연결 중 오류 발생: {e}")
            _mongo_client = None
            _database_instance = None
            raise

async def close_mongo_connection():
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        print("MongoDB connection closed.")

async def save_data_to_collections(data:dict|list):
    try:
        finance_collection = get_collection('finance_collection')
        news_collection = get_collection('news_collection')

        category = data.get('category') if isinstance(data, dict) else None
        collection_to_use: Optional[AsyncIOMotorCollection] = None

        if category == 'finance':
            collection_to_use = finance_collection
            print("-> finance_collection에 저장합니다.")
        elif category == 'news':
            collection_to_use = news_collection
            print("-> news_collection에 저장합니다.")
        else:
            print("-> 카테고리를 알 수 없거나 유효하지 않습니다. 데이터를 저장하지 않습니다.")
            return

        if isinstance(data, dict):
            insert_result = await collection_to_use.insert_one(data)
            print(f"문서 삽입 성공: _id = {insert_result.inserted_id}")
        elif isinstance(data, list):
            insert_result = await collection_to_use.insert_many(data)
            print(f"여러 문서 삽입 성공: _ids = {insert_result.inserted_ids}")
        else:
            print(f"지원하지 않는 데이터 형식입니다: {type(data)}")

    except ConnectionError as e:
        print(f"MongoDB 연결 오류: {e}")
    except Exception as e:
        print(f"데이터 저장 중 오류 발생: {e}")


async def get_data_by_criteria(
        collection_name: str,
        category: str,
        company_name: str,
        current_month: str
) -> Optional[Dict[str, Any]]:
    try:
        collection = get_collection(collection_name)
        query = {
            "category": category,
            "company_name": company_name,
            "current_month": current_month
        }

        print(f"컬렉션 '{collection_name}'에서 다음 조건으로 단일 문서 조회 중: {query}")

        result = await collection.find_one(query)

        if result:
            if '_id' in result and isinstance(result['_id'], ObjectId):
                result['_id'] = str(result['_id'])

        return result
    except Exception as e:
        print(f'Exception: {e}')
        return None

def get_database() -> AsyncIOMotorDatabase:
    if _database_instance is None:
        raise ConnectionError("MongoDB database is not connected. Call connect_to_mongodb() first.")
    return _database_instance

def get_collection(collection_name)->AsyncIOMotorCollection:
    db = get_database()
    return db.get_collection(collection_name)