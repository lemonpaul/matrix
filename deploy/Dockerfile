FROM python:3.8

# Уровень ядра
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -yq update && apt-get -yq install supervisor

RUN --mount=id=matrix_pip_cache,type=cache,target=/root/.cache/pip pip install --upgrade wheel pip

# Специфика проекта
COPY ./requirements.txt /requirements.txt
RUN pip install -U -r /requirements.txt
