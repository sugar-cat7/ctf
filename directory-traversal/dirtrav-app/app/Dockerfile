FROM python:3.9

ADD ./app /opt/app
RUN	pip3 install -r /opt/app/requirements.txt

CMD ["python", "/opt/app/app.py"]
EXPOSE 5001
