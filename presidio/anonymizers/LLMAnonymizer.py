from presidio_anonymizer.operators import Operator, OperatorType
from presidio_anonymizer.entities import InvalidParamError
from faker import Faker
from typing import Dict

fake = Faker()
fake.add_provider('faker.providers.internet')

entity_mapping = {
    "IPV4_ADDRESS": {},
    "IPV6_ADDRESS": {},
    "EMAIL_ADDRESS": {},
    "URL": {},
    "DOMAIN_NAME": {}
}

class LLMAnonymizer(Operator):
    def operate(self, text: str = None, params: Dict = None) -> str:
        entity_type = params.get("entity_type")
        if entity_type not in entity_mapping:
            return "<ANONYMIZED>"

        mapping = entity_mapping[entity_type]

        # Se già sostituito, ritorna la versione finta
        if text in mapping:
            return mapping[text]

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
            new_value = fake.domain_name()
        else:
            new_value = "<ANONYMIZED>"

        # Evita duplicati
        while new_value in mapping.values():
            if entity_type == "IPV4_ADDRESS":
                new_value = fake.ipv4()
            elif entity_type == "IPV6_ADDRESS":
                new_value = fake.ipv6()
            elif entity_type == "EMAIL_ADDRESS":
                new_value = fake.email()
            elif entity_type == "URL":
                new_value = fake.url()
            elif entity_type == "DOMAIN_NAME":
                new_value = fake.domain_name()

        mapping[text] = new_value
        return new_value

    def validate(self, params: Dict) -> None:
        if "entity_type" not in params:
            raise InvalidParamError("Missing 'entity_type' param")

    def operator_name(self) -> str:
        return "LLMAnonymizer"

    def operator_type(self) -> OperatorType:
        return OperatorType.Anonymize
