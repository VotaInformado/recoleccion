from abc import ABC
from pandas import DataFrame

# Project
from recoleccion.utils.custom_logger import CustomLogger


class Writer(ABC):
    logger = CustomLogger("Writer")

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
        # self.model should be defined in the child class
        return self.model.objects.create(**row)

    @classmethod
    def update_element(self, row):
        return self.model.objects.update(**row)
