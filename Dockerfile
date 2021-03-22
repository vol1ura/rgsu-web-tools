FROM python:3.9-alpine

MAINTAINER "Yuriy Volodin"
LABEL version=1.1

WORKDIR /app
COPY requirements.txt ./

RUN apk update && \
    apk add libxml2-dev libxslt-dev && \
    apk add --virtual build-dependencies build-base && \
    pip install -r requirements.txt && \
    apk del build-dependencies

EXPOSE 5000

COPY . .

CMD ["gunicorn", "-b 0.0.0.0:5000", "run:app"]