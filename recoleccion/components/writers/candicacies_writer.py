from recoleccion.components.writers import Writer
from recoleccion.components.writers import PersonsWriter

class CandicaciesWriter(Writer):

    def write(self, data):
        data.dropna(subset=["dni"], inplace=True)
        return PersonsWriter().write(data)
    