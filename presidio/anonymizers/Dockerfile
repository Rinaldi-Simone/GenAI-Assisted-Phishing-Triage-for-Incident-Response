FROM mcr.microsoft.com/presidio-anonymizer:latest

WORKDIR /usr/bin/presidio-anonymizer

# Installa Faker e altri moduli
RUN poetry add faker

# Copia i file custom
COPY LLMAnonymizer.py __init__.py operators_factory.py presidio_anonymizer/operators