FROM python:3.9

ADD ./app /opt/app
# RUN useradd -s /usr/sbin/nologin ctf &&\
RUN	pip3 install -r /opt/app/requirements.txt

# USER ctf

CMD ["python", "/opt/app/patterns.py"]
EXPOSE 5003
