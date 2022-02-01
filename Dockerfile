FROM python:3.7-slim

RUN mkdir /foodgram

WORKDIR /foodgram

COPY backend/requirements.txt ./

RUN pip3 install -r ./requirements.txt --no-cache-dir

COPY ./ ./

WORKDIR backend/

CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]