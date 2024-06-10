FROM python:3.12.3-bullseye

RUN apt-get update --yes && apt-get upgrade --yes

COPY src/ /project/src
COPY pyproject.toml /project
RUN pip install /project

ENTRYPOINT [ "python3", "-m", "mutator" ]
