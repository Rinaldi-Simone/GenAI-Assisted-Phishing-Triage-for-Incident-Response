from presidio_anonymizer.operators import Operator, OperatorType
from presidio_anonymizer.entities import InvalidParamError
from faker import Faker
from typing import Dict

fake = Faker()
fake_internet = Faker()
fake_internet.add_provider('faker.providers.internet')


MAX_ENTRIES = 1000

entity_mapping = {
    "IPV4_ADDRESS": {},
    "IPV6_ADDRESS": {},
    "EMAIL_ADDRESS": {},
    "URL": {},
    "DOMAIN_NAME": {},
    "DATE_TIME": {},
}

class LLMAnonymizer(Operator):
    def operate(self, text: str = None, params: Dict = None) -> str:
        entity_type = params.get("entity_type")
        if entity_type not in entity_mapping:
            return "<ANONYMIZED>"

        mapping = entity_mapping[entity_type]

        # Reset mapping se troppo grande
        if len(mapping) > MAX_ENTRIES:
            mapping.clear()

        # Normalizza il testo per evitare duplicati tipo "www.Example.com/" vs "example.com"
        normalized_text = text.lower().strip().rstrip("/")

        # Se già presente, restituisci il valore fittizio esistente
        if normalized_text in mapping:
            return mapping[normalized_text]

        # Genera nuovo valore finto
        if entity_type == "IPV4_ADDRESS":
            new_value = fake.ipv4()
        elif entity_type == "IPV6_ADDRESS":
            new_value = fake.ipv6()
        elif entity_type == "EMAIL_ADDRESS":
            new_value = fake.email()
        elif entity_type == "URL":
            new_value = fake.url()
        elif entity_type == "DOMAIN_NAME":
            new_value = fake_internet.domain_name()
        elif entity_type == "DATE_TIME":
            new_value = fake.date()
        else:
            new_value = "<ANONYMIZED>"

        # Evita duplicati nel mapping
        existing_values = set(mapping.values())
        attempts = 0
        while new_value in existing_values and attempts < 5:
            if entity_type == "IPV4_ADDRESS":
                new_value = fake.ipv4()
            elif entity_type == "IPV6_ADDRESS":
                new_value = fake.ipv6()
            elif entity_type == "EMAIL_ADDRESS":
                new_value = fake.email()
            elif entity_type == "URL":
                new_value = fake.url()
            elif entity_type == "DOMAIN_NAME":
                new_value = fake_internet.domain_name()
            elif entity_type == "DATE_TIME":
                new_value = fake.date()
            else:
                new_value = "<ANONYMIZED>"
            attempts += 1

        mapping[normalized_text] = new_value
        return new_value

    def validate(self, params: Dict) -> None:
        if "entity_type" not in params:
            raise InvalidParamError("Missing 'entity_type' param")

    def operator_name(self) -> str:
        return "LLMAnonymizer"

    def operator_type(self) -> OperatorType:
        return OperatorType.Anonymize
