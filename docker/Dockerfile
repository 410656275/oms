# -- Usage
# docker build --rm -t oms .
# docker run -it oms
# docker run -it -v /root/uuu/oms:/var/www/html/oms -v /data/oms:/data/oms -p 127.17.0.1:5000:80 -d oms
# docker run -it -v /home/wujing/oms:/var/www/html/oms -v /data/oms:/data/oms -p 5000:80 -d oms
# docker exec -it 8e823819dd3b bash


FROM python:3


COPY sources.list /etc/apt/sources.list
RUN apt-get update


RUN echo "Asia/Shanghai" >/etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata


RUN apt-get -y install nginx redis-server vim
RUN rm -f /etc/nginx/sites-enabled/default
COPY oms.conf /etc/nginx/sites-enabled/oms.conf


COPY pip.conf /root/.pip/pip.conf
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install -r /tmp/requirements.txt


WORKDIR /var/www/html/
CMD /etc/init.d/nginx start && \
    /etc/init.d/redis-server start && \
    cd /var/www/html/oms/ && bash uwsgi.sh stop && \
    cd /var/www/html/oms/ && find . -name '*.py[c|o]' -delete && \
    cd /var/www/html/oms/ && bash uwsgi.sh start && \
    cd /var/www/html/oms/ && bash celery.sh start && \
    bash
