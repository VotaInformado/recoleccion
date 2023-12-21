from .writer import Writer
from .persons_writer import PersonsWriter


class CandicaciesWriter(Writer):
    def write(self, data):
        data.dropna(subset=["dni"], inplace=True)
        return PersonsWriter().write(data)
