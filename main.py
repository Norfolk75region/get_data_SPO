from io import StringIO
import os

import requests
from bs4 import BeautifulSoup
import pandas as pd

import re

from pprint  import pp


ORGANIZATION = {}

def get_html_page(url):
    """
    Возвращает HTML содержимое веб-страницы для указанного URL-адреса.
    
    :param url: str, URL-адрес целевой веб-страницы
    :return: str, HTML содержимое страницы в виде строки
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        html_content = response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None
    
    return BeautifulSoup(html_content, 'html.parser') if html_content else None

def get_organisation_id(year):
    """
    Получает список идентификаторов организаций для указанного года.

    :param year: int, год, для которого нужны идентификаторы организаций
    :return: list, список идентификаторов организаций
    """
    url = f"https://monitoring.miccedu.ru/iam/{year}/_spo/material.php?type=2&id=10606"
    soup = get_html_page(url=url)
    links = soup.find_all('a', href=True)
    return [link['href'] for link in links if 'inst.php?id=' in link['href']]

def get_tables(url, id, year):
    """
    Получает и обрабатывает таблицы с указанной веб-страницы.

    :param url: str, URL-адрес веб-страницы с таблицами
    :param id: str, идентификатор организации
    :param year: int, год, к которому относятся данные
    :return: list, список таблиц в виде объектов pandas DataFrame
    """
    soup = get_html_page(url=url)
    tables = soup.find_all('table') if soup else []
    pattern = r'(>\d+)\,(\d+<)'
    replacement = r'\1.\2'
    html_string = str(tables)
    html_string = re.sub(pattern, replacement, html_string)
    try:
        data_frame = pd.read_html(StringIO(html_string))
    except ValueError:
        print(f"No tables found at URL: {url}")
        return []
    for frame in data_frame:
        # frame.columns = frame.iloc[0]
        # frame.drop(frame.index[0], inplace=True)
        frame['year'] = str(year) + '-01-01'
        frame['id'] = id
    return data_frame

def get_data_from_educations(educations, year):
    """
    Обрабатывает данные об образовательных организациях за указанный год.

    :param educations: list, список образовательных организаций или их идентификаторов
    :param year: int, год, за который обрабатываются данные
    :return: None
    """
    print(f"Processing data for year {year}...")
    res = []
    required_columns = [['Наименование показателя', 'Выборка2)',
                        'Значение показателя по  организации', 
                        'Значение по субъекту РФ', 
                        'Значение по РФ', 'year', 'id'],
                        ['№ п/п',
                         'Наименование показателя',
                         'Единица измерения',
                         'Значение показателя',
                         'year',
                         'id']]
    for education in educations:
        id = education.split('=')[1]
        print(f"Processing education {id}...")
        url = f'https://monitoring.miccedu.ru/iam/{year}/_spo/{education}'
        tables = get_tables(url, id, year)
        organization_name = [tables[1].columns.to_list()] + tables[1].values.tolist()
        ORGANIZATION[id] = {
            "id": id,
            "name": organization_name[0][1],
            "adress": organization_name[1][1] if len(organization_name) > 1 else "N/A",
            "site": organization_name[2][1] if len(organization_name) > 2 else "N/A",
            "inn": "temp_"+id
        }
        res.extend([table for table in tables if list(table.columns) == required_columns[0] or list(table.columns) == required_columns[1]])

    # pprint.pprint(res)
    return  res

def get_proffesion(educations, year):
    """
    Обрабатывает данные об образовательных организациях за указанный год.

    :param educations: list, список образовательных организаций или их идентификаторов
    :param year: int, год, за который обрабатываются данные
    :return: None
    """
    print(f"Processing data for year {year}...")
    res = []
    for education in educations:
        try:
            id = education.split('=')[1]
            print(f"Processing education {id}...")
            url = f'https://monitoring.miccedu.ru/iam/{year}/_spo/{education}'
            tables = get_tables(url, id, year)
            res.append(tables)
        except:
            continue

    print(res)
    return  res

def save_tables(data, year):
    """
    Сохраняет объединенные таблицы в CSV файл.

    :param data: list, список таблиц в формате pandas DataFrame
    :param year: int, год, к которому относятся данные
    :return: None
    """
    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)
    pd.concat(data).to_csv(f'{output_dir}/data_{year}.csv', index=False, encoding='utf-8', sep=';')

def main():
    """
    Основная функция программы, которая обрабатывает данные для каждого года 
    и сохраняет результаты в соответствующие файлы.
    """
    years = [2024]
    for year in years:
        organization_id = get_organisation_id(year)
        try:
            data = get_data_from_educations(organization_id, year) # для базовых индикаторов
            data = get_proffesion(organization_id, year) # для распределения учеников
        except Exception as e:
            print(f"Error processing data for year {year}: {e}")
            continue
        save_tables(data, year)

    pd.DataFrame(ORGANIZATION.values()).to_csv('data/organization.csv', index=False, encoding='utf-8', sep='|')

main()