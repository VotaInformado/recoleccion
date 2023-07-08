from abc import ABC
from pandas import DataFrame


class Writer(ABC):
    def write(self, data: DataFrame):
        existing = self.get_existing_by_key(data)
        written = []
        for i in data.index:
            row = data.loc[i]
            element = None
            if self.get_key(row) in existing:
                element = existing[self.get_key(row)]
                self.update_element(row)
            else:
                element = self.create_element(row)
            written.append(element)
        return written

    def get_existing_by_key(data):
        raise NotImplementedError

    def get_key(self, row):
        raise NotImplementedError

    def create_element(self, row):
        # self.model should be defined in the child class
        return self.model.objects.create(**row)

    def update_element(self, row):
        return self.model.objects.update(**row)
