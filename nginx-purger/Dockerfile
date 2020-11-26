FROM alpine:3.12.1
MAINTAINER tommylikehu@gmail.com

COPY . /etc/nginx-purger/
# install requirements
RUN apk update && apk add tini tzdata python2 py-pip && cd /etc/nginx-purger && pip install -r ./requirements.txt

ENV TZ="Asia/Shanghai"
ENV CONFIGURATION_FILE="/etc/nginx-purger/config"
ENV FLASK_APP="app.py"
ENV FLASK_ENV="production"
WORKDIR /etc/nginx-purger/
EXPOSE 8080
ENTRYPOINT ["tini", "--"]
CMD ["flask", "run", "-h", "0.0.0.0", "-p", "8080"]
