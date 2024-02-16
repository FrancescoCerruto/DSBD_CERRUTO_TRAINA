#import python
FROM python:3.11-slim-buster

#dipendenze mysqlclient
RUN apt-get update && apt-get install -y gcc && apt-get install -y default-libmysqlclient-dev

#working directory
WORKDIR /app

#copy all files
COPY . /app

#install dependencies
RUN pip install -r requirements.txt

#avvio applicazione
CMD ["python", "main.py"]