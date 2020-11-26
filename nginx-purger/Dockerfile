FROM alpine:3.12.1
MAINTAINER tommylikehu@gmail.com

COPY . /etc/nginx-purger/
# install requirements
RUN apk update && apk add tini tzdata python2 py-pip && cd /etc/nginx-purger && pip install -r ./requirements.txt

ENV TZ="Asia/Shanghai"
ENV CONFIGURATION_FILE="/etc/nginx-purger/config"
ENTRYPOINT ["tini", "--"]
CMD ["python /etc/nginx-purger/app.py"]
