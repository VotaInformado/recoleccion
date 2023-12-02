from abc import ABC
from pandas import DataFrame
import pandas as pd
import numpy as np

# Project
import logging


class Writer(ABC):
    logger = logging.getLogger(__name__)

    @classmethod
    def write(cls, data: DataFrame):
        existing = cls.get_existing_by_key(data)
        written = []
        total_written = total_updated = 0
        for i in data.index:
            row = data.loc[i]
            element = None
            if cls.get_key(row) in existing:
                element = existing[cls.get_key(row)]
                cls.update_element(row)
                total_updated += 1
            else:
                element = cls.create_element(row)
                total_written += 1
            written.append(element)
        cls.logger.info(f"{total_written} {cls.model.__name__}s were written and {total_updated} were updated")
        return written

    @classmethod
    def get_existing_by_key(data):
        raise NotImplementedError

    @classmethod
    def get_key(self, row):
        raise NotImplementedError

    @classmethod
    def create_element(self, row):
        row = row.replace({pd.NA: None, np.nan: None})
        # self.model should be defined in the child class
        return self.model.objects.create(**row)

    @classmethod
    def update_element(self, row: pd.Series):
        row = row.replace({pd.NA: None, np.nan: None})
        return self.model.objects.update(**row)
