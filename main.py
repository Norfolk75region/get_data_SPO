import os
from collections import defaultdict

import pandas as pd

from utils.spo import SPO as spo
from utils.web import get_html_page

YEARS = [2023, 2024, 2025]


def get_organisation_id(year):
    """
    Получает список идентификаторов организаций для указанного года.

    :param year: int, год, для которого нужны идентификаторы организаций
    :return: list, список идентификаторов организаций
    """
    url = f"https://monitoring.miccedu.ru/iam/{year}/_spo/material.php?type=2&id=10606"
    soup = get_html_page(url=url)
    links = soup.find_all('a', href=True)
    return [link['href'].split('=')[1] for link in links if 'inst.php?id=' in link['href']]


def save_tables(data, name):
    """
    Сохраняет объединенные таблицы в CSV файл.

    :param data: list, список таблиц в формате pandas DataFrame
    :param name: str, суффикс имени файла
    :return: None
    """
    if not data:
        print(f'No data to save for {name}')
        return

    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)
    df = pd.concat(data, ignore_index=True)
    df.to_csv(f'{output_dir}/data_{name}.csv', index=False, encoding='utf-8', sep=';')
    print(f'saved data_{name}.csv')


def main():
    organisations = {}
    list_organisations = []

    for year in YEARS:
        print(f'Loading organisation ids for {year}...')
        for org_id in get_organisation_id(year):
            if org_id in organisations:
                organisations[org_id].append(year)
            else:
                organisations[org_id] = [year]

    for org_id, years in organisations.items():
        print(f'Processing organisation {org_id} for years {years}...')
        list_organisations.append(spo(org_id, years))

    education_by_year = defaultdict(list)
    student_by_year = defaultdict(list)

    for organisation in list_organisations:
        education_df = organisation.results_by_activity_areas
        if not education_df.empty:
            for year in education_df['year'].unique():
                year_key = str(year)[:4]
                education_by_year[year_key].append(education_df[education_df['year'] == year])

        students_df = organisation.students_by_profession
        if not students_df.empty:
            for year in students_df['year'].unique():
                year_key = str(year)[:4]
                student_by_year[year_key].append(students_df[students_df['year'] == year])

    for year in YEARS:
        save_tables(education_by_year.get(str(year), []), f'{year}_educations_spo_system_characteristics')
        save_tables(student_by_year.get(str(year), []), f'{year}_educations_spo_study_proffesion')

    org_records = [
        {
            'id': organisation.id,
            'name': organisation.name,
            'adress': organisation.location,
            'site': organisation.site,
            'inn': f'temp_{organisation.id}',
        }
        for organisation in list_organisations
    ]
    pd.DataFrame(org_records).to_csv(
        'data/organization.csv',
        index=False,
        encoding='utf-8',
        sep='|',
    )
    print('saved organization.csv')


if __name__ == '__main__':
    main()
