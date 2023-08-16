from django.test import TestCase
from recoleccion.components.data_sources.law_projects_text_source import (
    DeputiesLawProyectsText,
    SenateLawProyectsText,
)
from unittest import skip


class DeputiesLawProjectsTextTestCase(TestCase):
    @skip("Not mocked")
    def test_get_text_from_infobase_doesnt_overwrite_link_if_data_obtained_is_empty(
        self,
    ):
        # Proyect 2528-D-2023 has a image pdf link, but no text.
        text, link = DeputiesLawProyectsText.get_text("2528", "D", "2023")
        self.assertEqual(
            link,
            "https://www4.hcdn.gob.ar/dependencias/dsecretaria/Periodo2023/PDF2023/TP2023/2528-D-2023.pdf",
        )
        self.assertLess(len(text), 10)

    # def test_5558_D_2022(
    #     self,
    # ):
    #     # Proyect 2528-D-2023 has a image pdf link, but no text. 5558-D-2022
    #     text, link = DeputiesLawProyectsText.get_text("5558", "D", "2022")
    #     self.assertEqual(
    #         link,
    #         "https://www4.hcdn.gob.ar/dependencias/dsecretaria/Periodo2023/PDF2023/TP2023/2528-D-2023.pdf",
    #     )
    #     self.assertLess(len(text), 10)


class SenateLawsProjectTextTestCase(TestCase):
    @skip("Not mocked")
    def test_get_text_parses_correctly_number_and_year_and_retrieves_ok(self):
        text, link = SenateLawProyectsText.get_text("0003", "S", "2023")

        self.assertIn(
            "CREACION DEL INSTITUTO DE COROS DE LA REPÚBLICA",
            text,
        )
        self.assertEqual(
            link,
            "https://www.senado.gob.ar/parlamentario/parlamentaria/465308/downloadPdf",
        )
