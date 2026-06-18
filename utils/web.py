import re
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup


def get_html_page(url):
    """
    Возвращает HTML содержимое веб-страницы для указанного URL-адреса.

    :param url: str, URL-адрес целевой веб-страницы
    :return: BeautifulSoup, разобранное HTML-содержимое страницы
    """
    headers = {
        'User-Agent': 'Mozilla/4.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/57.0.3029.110 Safari/537.3'
    }
    try:
        response = requests.get(url, headers=headers, timeout=9)
        response.raise_for_status()
        html_content = response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

    return BeautifulSoup(html_content, 'html.parser') if html_content else None


def get_tables_from_webpage(url, org_id=None, year=None, headers=None):
    """
    Получает и обрабатывает таблицы с указанной веб-страницы.

    :param url: str, URL-адрес веб-страницы с таблицами
    :param org_id: str, идентификатор организации
    :param year: int, год, к которому относятся данные
    :param headers: int, индекс строки с заголовками таблицы
    :return: list, список таблиц в виде объектов pandas DataFrame
    """
    soup = get_html_page(url=url)
    tables = soup.find_all('table') if soup else []
    pattern = r'(>\d+)\,(\d+<)'
    html_string = re.sub(pattern, r'\1.\2', str(tables))
    try:
        data_frame = pd.read_html(StringIO(html_string))
    except ValueError:
        print(f"No tables found at URL: {url}")
        return []

    for frame in data_frame:
        if headers is not None:
            frame.columns = frame.iloc[headers]
            frame.drop(frame.index[headers], inplace=True)
        if year is not None:
            frame['year'] = f'{year}-01-01'
        if org_id is not None:
            frame['id'] = org_id

    return data_frame

def normalize_results_table(table):
    extracted = table['Наименование показателя'].str.extract(r'^(\d+(?:\.\d+)*)\.\s*(.*)$')
    value_column = (
        'Значение показателя по  организации'
        if 'Значение показателя по  организации' in table.columns
        else 'Значение показателя'
    )

    return pd.DataFrame({
        'id_company': table['id'],
        'number_of_indicator': extracted[0],
        'indicator': extracted[1],
        'value': pd.to_numeric(table[value_column], errors='coerce'),
        'year': table['year'],
        'value_sub': (
            pd.to_numeric(table['Значение по субъекту РФ'], errors='coerce')
            if 'Значение по субъекту РФ' in table.columns
            else pd.Series([None] * len(table))  # Возвращаем None, а не пустую строку
        ),
        'value_sub_rf': (
            pd.to_numeric(table['Значение по РФ'], errors='coerce')
            if 'Значение по РФ' in table.columns
            else pd.Series([None] * len(table))
        ),
    })

