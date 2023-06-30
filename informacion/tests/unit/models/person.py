"""Company legal model tests"""

# Django
from django.test import TestCase

# Models
from informacion.models.person import Person

# Exception
from django.db.utils import IntegrityError

# Utils
from cryptus.utils.enums.risk import Risk


class CompanyLegalTests(TestCase):
    """CompanyLegal test cases"""

    fixtures = [
        'country.json',
        'userdocumenttype.json',
        'currency.json', 
        'apicurrencylimitation.json',
        'cachevariables.json',
        'currencytranslate.json',
        'blockchain.json',
        'blockchaintranslate.json',
        'integratedAPI.json',
        'notificationtopic',
        'notificationtemplate'
    ]

    def setUp(self):
        self.address = Address.objects.create(
            name="Av. Maipú 2116, B1636AAO Olivos, Provincia de Buenos Aires, Argentina",
            raw="Av. Maipú 2116, B1636AAO Olivos, Provincia de Buenos Aires, Argentina",
            street="Av. Maipú",
            street_number="2116",
            apartment="Oficina 1",
            city="Olivos",
            state="Provincia de Buenos Aires",
            country="Argentina",
            postal_code="B1636AAO",
            lat=-34.5153304,
            lng=-58.493372
        )
        self.company = Company.objects.create(name='Copany Name')
        self.country = Country.objects.get(iso='ARG')
        self.tax_id = '23393427378'
        self.company_legal = CompanyLegal.objects.create(        
            name = 'Company Name',
            legal_name = 'LEGAL NAME',
            legal_address = self.address,            
            tax_id = self.tax_id,
            company = self.company,                   
            nationality = self.country
        )

    def test_unique_contraint_country_tax_id_success(self):
        """If country and tax_id are unique together, CompanyLegal instance is created successfully"""
        other_company = Company.objects.create(name='Other Copany Name')
        other_company_legal = CompanyLegal.objects.create(
            name = 'Other Company Name',
            legal_name = 'OTHER LEGAL NAME',
            legal_address = self.address,            
            tax_id = '13393427370',
            company = other_company,       
            nationality = self.country
        )