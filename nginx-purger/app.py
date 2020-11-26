# coding=utf-8
import os
import logging
import time

from flask import Flask
from flask import request
from flask_basicauth import BasicAuth
import requests

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.config.from_envvar('CONFIGURATION_FILE')

BASIC_AUTH_USERNAME = os.environ.get("BASIC_AUTH_USERNAME")
if BASIC_AUTH_USERNAME:
    app.config['BASIC_AUTH_USERNAME'] = BASIC_AUTH_USERNAME

BASIC_AUTH_PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD")
if BASIC_AUTH_PASSWORD:
    app.config['BASIC_AUTH_PASSWORD'] = BASIC_AUTH_PASSWORD

KUBERNETES_TOKEN = os.environ.get("KUBERNETES_TOKEN")
if KUBERNETES_TOKEN:
    app.config['KUBERNETES_TOKEN'] = KUBERNETES_TOKEN
# Try to get the token in kubernetes service token file
if not KUBERNETES_TOKEN:
    default_token_file = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    if os.path.isfile(default_token_file):
        with open(default_token_file, "r") as f:
            app.config['KUBERNETES_TOKEN'] = f.readline()

app.config["AUTH_HEADER"] = {"Authorization": str.format("Bearer {0}", app.config['KUBERNETES_TOKEN'])}

basic_auth = BasicAuth(app)


@app.route('/purge', methods=["GET"])
@basic_auth.required
def purge():
    hostname = request.args.get('hostname', '')
    if not hostname:
        return {"error": "'hostname' not specified"}, 400
    addresses = _resolve_ingress_endpoints()
    host = {
        "Host": hostname
    }
    results = []
    status_code = 200
    for e in addresses:
        endpoint = "https://{0}/purge/*".format(str(e).strip("/"))
        r = requests.get(endpoint, headers=host, timeout=5, verify=False)
        if r.status_code == 200:
            results.append("nginx cache purged for host: {0} on instance {1}".format(hostname, e))
        else:
            results.append(
                "failed to purge nginx cache for host {0} on instance {1}, reason: {2}".format(hostname, e, r.text))
            status_code = 500
    return "\n".join(results), status_code


def _resolve_ingress_endpoints():
    endpoint = "{0}/namespaces/{1}/endpints/{2}".format(str(app.config["KUBE_API_SERVER"]).strip("/"),
                                                        str(app.config["INGRESS_NS"]).strip("/"),
                                                        str(app.config["INGRESS_SERVICE"]).strip("/"))
    r = requests.get(endpoint, headers=app.config["AUTH_HEADER"], timeout=5, verify=False)
    if r.status_code != 200:
        raise "failed to get nginx ingress's endpoint lists {0}".format(r)
    return [x["ip"] for x in r.json()["endpoint"]["addresses"]]


def _wait_endpoint_reachable():
    for retry in range(3):
        try:
            app.logger.info("wait for kubernetes api endpoint reachable round: %d", retry)
            requests.get(app.config["KUBE_API_SERVER"],
                         headers=app.config["AUTH_HEADER"],
                         timeout=5, verify=False)
            app.logger.info("kubernetes api server is reachable")
            return True
        except Exception as err:
            app.logger.warning("failed to resolve kubernetes endpoint %s", err)
            time.sleep(3)
    return False


if __name__ == '__main__':
    try:
        for req in ["KUBERNETES_TOKEN", "BASIC_AUTH_USERNAME", "BASIC_AUTH_PASSWORD", "INGRESS_NS", "INGRESS_SERVICE"]:
            if not app.config[req]:
                app.logger.error("Please ensure %s configured", req)
        if not _wait_endpoint_reachable():
            app.logger.error("give up waiting for kubernetes api server ready")
            exit(-1)
        app.run(host='0.0.0.0', port=app.config["SERVER_PORT"])
    except Exception as e:
        app.logger.error("Application server down with error %s", e)
        exit(-1)
