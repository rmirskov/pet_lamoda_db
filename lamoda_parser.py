import json
import re
import random
import requests
import time
import psycopg2


API_LINK = 'https://www.lamoda.ru/api/v1/product/'


def get_articles(url: str, headers: dict[str, str], page: int, proxy=None) -> list[str]:
    '''Scraping unique articles of clothes from page'''
    articles_list = list()
    url = f'{url}?page={page}'
    try:
        r = requests.get(url, headers, proxies=proxy)
        if r.status_code == 200:
            text = r.text
            pattern = r'(?<=[A-Z]\/[A-Z]\/)[A-Z0-9]{12}'
            articles_list = list(set(re.findall(pattern, text)))
    except Exception as e:
        print(e)

    return list(set(articles_list))


def get_random_headers_and_proxy(user_agents: list[str], proxies: list[str]) -> dict[str, str]:
    return (
        {'Content-type': 'application/json', 'User-agent': random.choice(user_agents)},
        {'http': f'{random.choice(proxies)}:80'}
        )


def count_rows(cursor, db_table: str) -> int:
    query = f"SELECT COUNT(*) FROM {db_table};"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0]


def get_key(cursor, db_table: str, key: str, column: str, value: str) -> int:
    query = f"SELECT {key} FROM {db_table} WHERE {column} = \'{value}\';"
    cursor.execute(query)
    result = cursor.fetchone()
    if result:
        return result[0]
    return result


def inserting_data(connection, cursor, query: str, tpl: tuple) -> None:
    try:
        cursor.execute(query, tpl)
    except Exception as e:
        print(e)
    connection.commit()


def product_data_insert(data: dict, exclusive_fields: list, connection, cursor) -> None:
    '''INSERT DATA INTO TABLE products'''
    product_items = [item for item in data.items() if item[0] not in exclusive_fields]
    product_fields = ", ".join([f[0] for f in product_items])
    product_values = tuple([f[1] for f in product_items])
    product_query = f"INSERT INTO products ({product_fields})" + " VALUES \
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
    inserting_data(connection, cursor, product_query, product_values)


def size_data_insert(data: dict, connection, cursor) -> None:
    '''INSERT DATA INTO TABLE sizes'''
    for size_item in data['sizes']:
        rus_size, brand_size, stock_quantity = size_item
        sizes_query = "INSERT INTO sizes (product_id, rus_size, brand_size, stock_quantity) \
            VALUES (%s, %s, %s, %s);"
        sizes_tuple = (data['product_id'], rus_size, brand_size, stock_quantity)
        inserting_data(connection, cursor, sizes_query, sizes_tuple)


def material_data_extract_and_insert(data: dict, item_info: dict, connection, cursor) -> None:                   
    '''EXTRACT AND INSERT DATA INTO TABLES materials, material_filling, lining_material and material_filler'''
    materials_attr = ['material_filling', 'lining_material', 'material_filler']
    for elem in data['attributes']:
        if elem['key'] in materials_attr:
            material_names = re.findall(r'[А-Я]{1}[а-я]*(?=\s-)', elem['value'])
            fillings = re.findall(r'(?<=\s)[0-9]{1,3}(?=%)', elem['value'])                       
            for material_name, filling in zip(material_names, fillings):
                material_id = get_key(cursor, 'materials', 'material_id', 'material_name', material_name)
                if material_id is None:
                    material_id = count_rows(cursor, 'materials') + 1
                    material_query = "INSERT INTO materials (material_id, material_name) VALUES (%s, %s);"
                    material_tuple = (material_id, material_name)
                    inserting_data(connection, cursor, material_query, material_tuple)
                material_filling_query = f"INSERT INTO {elem['key']}" + " (product_id, material_id, percentage_in) \
                    VALUES (%s, %s, %s);"
                material_filling_tuple = (item_info['product_id'], material_id, filling)
                inserting_data(connection, cursor, material_filling_query, material_filling_tuple)


def get_product_reviews_or_questions(link: str, table_name: str, product_id: str, proxies: list[str],
                                     user_agents: list[str], connection, cursor) -> None:
    '''EXTRACT AND INSERT DATA INTO TABLE reviews or questions'''
    cur_offset = 0
    while True:
        headers, proxy = get_random_headers_and_proxy(user_agents, proxies)
        if table_name == 'reviews':
            params = {
            'limit': 50, 'offset': cur_offset,'only_with_photos': False,
            'sku': product_id, 'sort': 'date', 'sort_direction': 'desc'
            }
        elif table_name == 'questions':
            params = {'limit': 10, 'offset': cur_offset, 'sku': product_id}
        cur_r = requests.get(link, params=params, headers=headers, proxies=proxy)
        if cur_r.status_code == 200:
            cur_data = json.loads(cur_r.text)
            elemets = cur_data[table_name]
            if len(elemets) == 0:
                break
            for element in elemets:
                element_id = count_rows(cursor, table_name) + 1
                text = element['text']
                created_time = element['created_time']
                if table_name == 'reviews':
                    uuid = element['uuid']
                    rating = element['rating']
                    if 'size' in element['fittings']:
                        fittings = element['fittings']['size']['title']
                    else:
                        fittings = None
                    query = f"INSERT INTO {table_name}" + "(review_id, product_id, uuid, text, fittings, created_time, rating)\
                    VALUES (%s, %s, %s, %s, %s, %s, %s);"
                    tple = (element_id, product_id, uuid, text, fittings, created_time, rating)
                elif table_name == 'questions':
                    username = element['username']
                    answer = element['answer']
                    query = f"INSERT INTO {table_name}" + "(question_id, product_id, username, text, created_time, answer)\
                    VALUES (%s, %s, %s, %s, %s, %s);"
                    tple = (element_id, product_id, username, text, created_time, answer)
                inserting_data(connection, cursor, query, tple)
            cur_offset += params['limit']
        else:
            print('products reviews request >> status_code is not equal 200')
            break


def get_items_product_data(articles: list[str], proxies: list[str], user_agents: list[str], pg_connection, pg_cursor) -> None:
    for i in range(len(articles)):
        time.sleep(1.0 + random.random())
        item_link = f'{API_LINK}get?sku={articles[i]}'
        headers, proxy = get_random_headers_and_proxy(user_agents, proxies)
        cur_r = requests.get(item_link, headers=headers, proxies=proxy)
        if cur_r.status_code == 200:
            cur_data = json.loads(cur_r.text)
            print(cur_data['sku'])
            # EXTRACT AND INSERT DATA INTO TABLE brands
            brand_name = re.sub(r"\'", r"-", cur_data['brand']['title']).strip()
            brand_id = get_key(pg_cursor, 'brands', 'brand_id', 'brand_name', brand_name)
            if brand_id is None:
                brand_id = count_rows(pg_cursor, 'brands') + 1
                brand_query = "INSERT INTO brands (brand_id, brand_name) VALUES (%s, %s);"
                brand_tuple = (brand_id, brand_name)
                inserting_data(pg_connection, pg_cursor, brand_query, brand_tuple)
            # EXTRACT AND INSERT DATA INTO others tables
            product_info = {}
            product_info['product_id'] = cur_data['sku']
            product_info['sex'] = cur_data['gender']
            product_info['brand_id'] = brand_id
            if 'model_title' in cur_data:
                product_info['model'] = f"{cur_data['title']} {cur_data['model_title']}"
            else:
                product_info['model'] = cur_data['title']
            product_info['color'] = cur_data['colors'][0]['title']
            if 'price' in cur_data:
                product_info['price'] = cur_data['price']
            else:
                print('There is not price_field')
                product_info['price'] = None
            if 'old_price' in cur_data:
                product_info['old_price'] = cur_data['old_price']
            else:
                product_info['old_price'] = None
            product_attr_names = ['season_wear', 'print', 'guarantee_period', 'production_country', 'clothes_clasp']
            for attr in product_attr_names:
                product_info[attr] = None
            for elem in cur_data['attributes']:
                if elem['key'] in product_attr_names:
                    product_info[elem['key']] = elem['value']
            if 'average_rating' in cur_data:    
                product_info['average_rating'] = cur_data['average_rating']
            else:
                product_info['average_rating'] = None
            sizes = []
            for size in cur_data['sizes']:
                sizes.append((size['title'], size['brand_title'], size['stock_quantity']))
            product_info['sizes'] = sizes
            
            size_fields = ['sizes']
            product_data_insert(product_info, size_fields, pg_connection, pg_cursor)
            size_data_insert(product_info, pg_connection, pg_cursor)
            material_data_extract_and_insert(cur_data, product_info, pg_connection, pg_cursor)
            reviews_and_questions = [
                {'link': f'{API_LINK}reviews', 'table_name': 'reviews'},
                {'link': f'{API_LINK}questions', 'table_name':'questions'}
            ]
            for i in reviews_and_questions:
                get_product_reviews_or_questions(i['link'], i['table_name'], product_info['product_id'], proxies,
                                                 user_agents, pg_connection, pg_cursor)
        else:
            print('product request >> status_code is not equal 200')


if __name__ == '__main__':
    with open('proxy.txt', 'r') as f:
        proxy_list = f.read().split(' ')
    with open('user_agent.txt', 'r') as f:
        user_agent_list = f.read().split('\n')

    URL = "https://www.lamoda.ru/c/477/clothes-muzhskaya-odezhda/"
    page = 1
    try:
        conn = psycopg2.connect(
            dbname='lamoda_db', user='lamoda', 
            password='lamodA2023', host='localhost'
            )
        cursor = conn.cursor()
        while True:
            headers, proxy = get_random_headers_and_proxy(user_agent_list, proxy_list)
            current_page_articles = get_articles(URL, headers, page, proxy=proxy)
            if len(current_page_articles) != 0:
                get_items_product_data(current_page_articles, proxy_list, user_agent_list, conn, cursor)
            else:
                break
            page += 1
    finally:
        cursor.close()
        conn.close()
