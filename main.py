from web.WebApi import app
from script.UserManageAPI import GiveSuperOP
from util.YamlRead import WebHost, WebPort, SuperAdmin
from util.log import _log
from waitress import serve
from flask import request
import logging

from flask import request
import logging
from waitress import serve

logging.basicConfig(
    filename='CNUTlog/web/access.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

@app.after_request
def log_request(response):
    logging.info(
        '%s - %s %s - %s',
        request.remote_addr,
        request.method,
        request.path,
        response.status_code
    )
    return response

if __name__ == '__main__':
    if SuperAdmin != None:
        GiveSuperOP(SuperAdmin)
    _log._INFO(f"[waitress]web服务已开启, 请在 {WebHost}:{WebPort} 访问")
    serve(
        app,
        host=WebHost,
        port=WebPort,
        ident=None,
        threads=4,
    )