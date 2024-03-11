from django.test import TestCase
from recoleccion.components.data_sources.law_projects_text_source import (
    DeputiesLawProjectsText,
    SenateLawProjectsText,
)
from recoleccion.tests.test_helpers.mocks import mock_method, FakeResponse
from requests import Session


class DeputiesLawProjectsTextTestCase(TestCase):
    def test_get_text_from_infobase_doesnt_overwrite_link_if_data_obtained_is_empty(
        self,
    ):
        # Proyect 2528-D-2023 has a image pdf link, but no text.
        pdf_link = b'<a target="_blank" class="btn btn-info" href="https://www4.hcdn.gob.ar/dependencias/dsecretaria/Periodo2023/PDF2023/TP2023/2528-D-2023.pdf">Ver documento original</a>'
        with mock_method(Session, "post", return_value=FakeResponse(content=pdf_link)):
            with mock_method(DeputiesLawProjectsText, "_get_pdf_text", return_value=""):
                with mock_method(DeputiesLawProjectsText, "_get_text_from_infobase", return_value=""):
                    text, link = DeputiesLawProjectsText._get_text("2528", "D", "2023")
                    self.assertEqual(
                        link,
                        "https://www4.hcdn.gob.ar/dependencias/dsecretaria/Periodo2023/PDF2023/TP2023/2528-D-2023.pdf",
                    )
                    self.assertEqual(text, "")


class SenateLawsProjectTextTestCase(TestCase):
    def test_parses_correctly_number_and_year(self):
        number, source, year = SenateLawProjectsText._parse_input("0003", "s", "2023")
        self.assertEqual(number, "3")
        self.assertEqual(source, "S")
        self.assertEqual(year, "23")

    def test_initial_text_is_retrieved_correctly_if_final_isnt_loaded(self):
        response = b"""<div role="tabpanel" class="tab-pane" id="textoDefinitivo">\n\t\t               \t\t\t\n\t\t\t\t\t\tEn proceso de carga\n\t\t\t\n\n \n\t</div>\n\n\t<div role="tabpanel" class="tab-pane" id="textoOriginal">\n\t\n\nSenado de la Naci\xc3\xb3n<br>\nSecretar\xc3\xada Parlamentaria<br>\nDirecci\xc3\xb3n Publicaciones<br>\n<br>\n(S-1047/04)<br>\n<br>\nPROYECTO DE LEY<br>\n<br>\nEl Senado y C\xc3\xa1mara de Diputados,...<br>\n<br>\nLEY ANTITERRORISTA<br></div>"""
        with mock_method(Session, "get", return_value=FakeResponse(content=response)):
            text, link = SenateLawProjectsText._get_text("1047", "S", "2004")
            self.assertIn(
                "LEY ANTITERRORISTA",
                text,
            )
            self.assertEqual(
                link,
                "https://www.senado.gob.ar/parlamentario/comisiones/verExp/1047.04/S/PL",
            )
