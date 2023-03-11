FROM python:3.9

ADD ./app /opt/app
RUN	pip3 install -r /opt/app/requirements.txt
RUN chmod +x /opt/app/test.sh
RUN useradd test

USER test
CMD  python /opt/app/app.py
EXPOSE 5001
