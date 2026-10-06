"""
Migration script to update all media URLs from local /api/cdn/ paths to external server URLs.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

EXTERNAL_CDN = 'https://files.ihgbrands.com/brightluxx'
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'brightluxx')


async def migrate_collection(db, collection_name, field_name):
    """Update a specific field in a collection from /api/cdn/ to external URL."""
    collection = db[collection_name]
    
    # Find all documents with local paths
    cursor = collection.find({field_name: {'$regex': '^/api/cdn/'}})
    docs = await cursor.to_list(length=1000)
    
    updated = 0
    for doc in docs:
        old_url = doc[field_name]
        # Convert /api/cdn/filename.webp to https://files.ihgbrands.com/brightluxx/uploads/filename.webp
        filename = old_url.replace('/api/cdn/', '')
        new_url = f'{EXTERNAL_CDN}/uploads/{filename}'
        
        await collection.update_one(
            {'_id': doc['_id']},
            {'$set': {field_name: new_url}}
        )
        updated += 1
        print(f'  {old_url} -> {new_url}')
    
    return updated


async def migrate_all():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print('=' * 60)
    print('Media URL Migration Script')
    print(f'External CDN: {EXTERNAL_CDN}')
    print('=' * 60)
    
    # Products collection - image_url field
    print('\n[1/4] Migrating products.image_url...')
    count = await migrate_collection(db, 'products', 'image_url')
    print(f'  Updated {count} products')
    
    # Projects collection - image_url field
    print('\n[2/4] Migrating projects.image_url...')
    count = await migrate_collection(db, 'projects', 'image_url')
    print(f'  Updated {count} projects')
    
    # Inspirations collection - image_url field
    print('\n[3/4] Migrating inspirations.image_url...')
    count = await migrate_collection(db, 'inspirations', 'image_url')
    print(f'  Updated {count} inspirations')
    
    # Settings collection - logoUrl and faviconUrl
    print('\n[4/4] Migrating settings...')
    settings = db['settings']
    settings_doc = await settings.find_one({})
    if settings_doc:
        updates = {}
        for field in ['logoUrl', 'faviconUrl']:
            if settings_doc.get(field, '').startswith('/api/cdn/'):
                old_url = settings_doc[field]
                filename = old_url.replace('/api/cdn/', '')
                new_url = f'{EXTERNAL_CDN}/uploads/{filename}'
                updates[field] = new_url
                print(f'  {field}: {old_url} -> {new_url}')
        
        if updates:
            await settings.update_one({}, {'$set': updates})
            print(f'  Updated settings with {len(updates)} fields')
        else:
            print('  No settings needed updating')
    else:
        print('  No settings document found')
    
    # Verify migration
    print('\n' + '=' * 60)
    print('Verification:')
    
    sample_product = await db['products'].find_one({})
    if sample_product:
        print(f'  Sample product image_url: {sample_product.get("image_url", "N/A")}')
    
    sample_project = await db['projects'].find_one({})
    if sample_project:
        print(f'  Sample project image_url: {sample_project.get("image_url", "N/A")}')
    
    # Count remaining local paths
    local_products = await db['products'].count_documents({'image_url': {'$regex': '^/api/cdn/'}})
    local_projects = await db['projects'].count_documents({'image_url': {'$regex': '^/api/cdn/'}})
    
    print(f'\n  Remaining /api/cdn/ paths in products: {local_products}')
    print(f'  Remaining /api/cdn/ paths in projects: {local_projects}')
    
    print('\n' + '=' * 60)
    print('Migration complete!')
    print('=' * 60)


if __name__ == '__main__':
    asyncio.run(migrate_all())
