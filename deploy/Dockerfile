FROM python:3.7

# Уровень ядра
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -yq update \
    && apt-get -yq install apt-utils gcc swig gobject-introspection \
    libgirepository1.0-dev gobject-introspection libgirepository1.0-dev \
    python3-pip python3-dev python3-cairo \
    python3-apt python3-setuptools python3-distutils \
    libssl-dev libcurl4-openssl-dev libldap2-dev libffi-dev \
    libpulse-dev libasound2-dev libsasl2-dev libpulse-dev libcairo2-dev \
    supervisor poppler-utils openjdk-11-jdk ghostscript nano \
    libjpeg-dev libmagickwand-dev libmagickcore-dev sqlite \
    && apt-get purge -y --auto-remove

RUN pip install --upgrade wheel pip

# Специфика проекта
COPY ./requirements.txt /requirements.txt
RUN pip install -U -r /requirements.txt

