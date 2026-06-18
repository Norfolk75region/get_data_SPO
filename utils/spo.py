from functools import cached_property

import pandas as pd

from utils.web import get_tables_from_webpage, normalize_results_table

RESULTS_COLUMNS = [
    'id_company',
    'number_of_indicator',
    'indicator',
    'value',
    'year',
    'value_sub',
    'value_sub_rf',
]



class SPO:
    def __init__(self, spo_id: int, reporting_years=None):
        self.id = spo_id

        if isinstance(reporting_years, list):
            self.reporting_years = reporting_years
        elif isinstance(reporting_years, (str, int)):
            self.reporting_years = [int(reporting_years)]
        else:
            self.reporting_years = []

        self.name = None
        self.location = None
        self.site = None
        self.specific = None

        if self.reporting_years:
            last_year = max(self.reporting_years)
            tables = get_tables_from_webpage(
                f'https://monitoring.miccedu.ru/iam/{last_year}/_spo/inst.php?id={self.id}'
            )

            if tables and len(tables) > 1:
                info = tables[1]
                self.name = info.iloc[0, 1]
                self.location = info.iloc[1, 1]
                self.site = info.iloc[2, 1]
                if len(info) > 5:
                    self.specific = info.iloc[5, 1]

    @cached_property
    def results_by_activity_areas(self):
        required_columns = [['Наименование показателя', 'Выборка2)',
                             'Значение показателя по  организации',
                             'Значение по субъекту РФ',
                             'Значение по РФ', 'year', 'id'],
                            ['№ п/п',
                             'Наименование показателя',
                             'Единица измерения',
                             'Значение показателя', 'year', 'id'],
                            ['Наименование показателя',
                             'Значение показателя по  организации',
                             'Значение по субъекту РФ',
                             'Значение по РФ', 'year', 'id']]
        frames = []
        for year in self.reporting_years:
            url = f'https://monitoring.miccedu.ru/iam/{year}/_spo/inst.php?id={self.id}'
            tables = get_tables_from_webpage(url, org_id=self.id, year=year, headers=0)
            for table in tables:
                if list(table.columns) in required_columns:
                    frames.append(normalize_results_table(table))

        if not frames:
            return pd.DataFrame(columns=RESULTS_COLUMNS)

        return pd.concat(frames, ignore_index=True)[RESULTS_COLUMNS]

    @cached_property
    def students_by_profession(self):
        required_columns = [['Unnamed: 0', 'Доля в субъекте РФ', 'Контингент  студентов', 'year', 'id']]
        frames = []
        for year in self.reporting_years:
            try:
                url = f'https://monitoring.miccedu.ru/iam/{year}/_spo/inst.php?id={self.id}'
                tables = get_tables_from_webpage(url, org_id=self.id, year=year)
                for table in tables:
                    if list(table.columns) in required_columns:
                        frames.append(table)
            except Exception:
                continue

        if not frames:
            return pd.DataFrame(columns=required_columns[0])
        frames = pd.concat(frames, ignore_index=True)
        frames.columns = ['name', 'percent_in_subj', 'student', 'year', 'id']
        return frames
