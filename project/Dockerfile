FROM python:3.8

LABEL maintainer="Stephan Kluwe"

COPY techtrends  /app

WORKDIR /app

RUN pip3 install -r requirements.txt
 

CMD [ "python3", "init_db.py"]
CMD [ "python3", "app.py"]

EXPOSE 3111



