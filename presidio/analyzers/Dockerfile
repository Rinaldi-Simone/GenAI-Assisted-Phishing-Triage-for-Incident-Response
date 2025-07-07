FROM mcr.microsoft.com/presidio-analyzer:latest

# Imposta la working directory
WORKDIR /usr/bin/presidio-analyzer

# Copia il file di configurazione per l'NLP engine
COPY default_analyzer.yaml presidio_analyzer/conf/default_analyzer.yaml
COPY default.yaml presidio_analyzer/conf/default.yaml
COPY default_recognizers.yaml presidio_analyzer/conf/default_recognizers.yaml



# Copia i riconoscitori personalizzati
COPY ip_recognizer.py presidio_analyzer/predefined_recognizers/ip_recognizer.py
COPY url_recognizer.py presidio_analyzer/predefined_recognizers/url_recognizer.py
COPY phone_recognizer.py presidio_analyzer/predefined_recognizers/phone_recognizer.py
