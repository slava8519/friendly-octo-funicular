from aiohttp import web, ClientSession, request
from bs4 import BeautifulSoup
from datetime import datetime
import json
import uvloop
import asyncio
import sqlite3
import aiosqlite
import hashlib
import time 

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
routes = web.RouteTableDef()

async def fetch(session,url):
    async with session.get(url) as resp:
        return await resp.text()

async def gather_tasks(session,urls):
    tasks=[]
    for _ in urls:
        tasks.append(asyncio.create_task(fetch(session,_)))    
    respons = await asyncio.gather(*tasks)
    return respons

async def get_resp_with_news(session):
    url_news = [r'https://news.ycombinator.com/']
    respons = await gather_tasks(session,url_news)
    return respons

async def extract_newsitems_from_resp(resp):
    soup = BeautifulSoup(resp[0], 'lxml')
    news_list = soup.find('table',{'class':'itemlist'})
    items = news_list.find_all('a',{'class': 'storylink'})
    return items

async def extract_news_from_newsitems(items):
    news=[]
    count =0
    for item in items:
        count +=1
        news_title = item.text
        # news_id = int(hashlib.sha1((news_title).encode('utf-8')).hexdigest(),16) 
        hash_digest = hashlib.shake_128(news_title.encode('utf-8')).digest(4)
        hash_int = int.from_bytes(hash_digest, byteorder='big', signed=True) 
        news_id = hash_int
        news_url = item.get('href')
        news.append((news_id,news_title,news_url,int(time.time())))
        if count >= 30:
            break
    return news
    

async def get_news(session):
    respons = await get_resp_with_news(session)
    items = await extract_newsitems_from_resp(respons)
    news = await extract_news_from_newsitems(items)
    return news

async def hackernews_scan_task(app):
    async with ClientSession() as session:
        while True:
            news = await get_news(session)
            await push_news_to_bd(news)
            await asyncio.sleep(10)

async def main_news_task(app):
    await check_and_create_table(app)
    await hackernews_scan_task(app)

async def check_and_create_table(app):
    async with aiosqlite.connect("newsdatabase.db") as db:
        try:
            await db.execute("""CREATE TABLE IF NOT EXISTS news
                                (hash int PRIMARY KEY, title text, url text, created int)      
                            """)
        except Exception as e:
                print (f'Some error occure while check and creating BD: {e}')
        
        await db.commit()

async def push_news_to_bd(news):
    async with aiosqlite.connect("newsdatabase.db") as db:
        for _ in news:
            try:
                await db.execute("""INSERT OR IGNORE INTO news (hash,title,url,created) VALUES (?,?,?,?)
            """,_)
            except Exception as e:
                print (f'Some error occure while BD inserting: {e}')           
        await db.commit()

async def pull_news_from_bd(order = 'rowid',offset=0,limit=5,orderType='ASC'):
    news=[]
    # I know, I know f-string is sql-injection unsafe. But I sanitize my database inputs at check_posts_keys
    sql = f'SELECT rowid,title,url,created FROM news ORDER BY {order} {orderType} LIMIT {limit} OFFSET {offset};'
    async with aiosqlite.connect("newsdatabase.db") as db:
        async with db.execute(sql) as cursor:
                async for row in cursor:
                    news.append({
                        "id":row[0],
                        "title":row[1],
                        "url":row[2],
                        "created":datetime.utcfromtimestamp(row[3]).strftime('%Y-%m-%dT%H:%M:%S')
                    })
    return news


async def start_background_tasks(app):
    app['news_listener'] = asyncio.create_task(main_news_task(app))


async def cleanup_background_tasks(app):
    app['news_listener'].cancel()
    await app['news_listener']

async def get_posts_keys(request):
    try:
        limit = request.rel_url.query['limit']
    except KeyError:
        limit =5
    try:
        offset = request.rel_url.query['offset']
    except KeyError:
        offset =0
    try:
        order = request.rel_url.query['order']
    except KeyError:
        order ='rowid'

    try:
        orderType = request.rel_url.query['orderType']
    except KeyError:
        orderType ='ASC'

    return limit, offset, order, orderType

async def check_posts_keys(limit, offset, order,orderType):
    check_errors={}
    #TODO get colums names from table
    posts_columns=['rowid','id', 'title', 'url', 'created']
    try: 
        if int(limit) not in range(1,31):
            check_errors['limit'] = 'Key must be integer in range(1,30)'
    except ValueError:
        check_errors['limit'] = 'Key must be integer in range(1,30)'
    
    try:
         _=int(offset)
    except ValueError:
        check_errors['offset'] = 'Key must be integer'
    
    if order not in posts_columns:
        check_errors['order'] = f'Key must be str and one of: {posts_columns}'
    
    if orderType not in ['ASC','DESC']:
        check_errors['orderType'] = 'Key must be str and one of: ASC, DESC'

    return check_errors

@routes.get('/')
async def handle(request):
    responce_obj = { 'status':'successs' }
    return web.json_response(responce_obj,status=200)

@routes.get('/posts')
async def posts(request):
    limit, offset, order, orderType = await get_posts_keys(request)
    check_errors = await check_posts_keys(limit, offset, order,orderType)
    if len(check_errors) >0:
        responce_obj = {'errorsInApi':{'posts':check_errors}}
        return web.json_response(responce_obj,status=200)
    
    responce_obj = await pull_news_from_bd(order,offset,limit,orderType)
    return web.json_response(responce_obj,status=200)

def init_app(argv=None) -> web.Application:
    app = web.Application()
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    app.add_routes(routes)
    return app


app = init_app()