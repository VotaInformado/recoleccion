from project.writers.writer import Writer
from project.writers.persons_writer import PersonsWriter
class CandicaciesWriter(Writer):

    def write(self, data):
        # Clean data
        data.dropna(subset=["dni"], inplace=True)
        return PersonsWriter().write(data)
    