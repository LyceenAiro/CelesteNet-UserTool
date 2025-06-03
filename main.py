from web.WebApi import app
from script.UserManageAPI import GiveSuperOP, DeSuperOP
from util.YamlRead import WebHost, WebPort, SuperAdmin, RemoveSuperAdmin, CelesteNetWebRedirect
from util.log import _log
from util.app_data import app_data
from waitress import serve
from flask import request
import logging

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
    _log._INFO(f"[Version]CelesteNet-UserTool v{app_data.version}")
    if RemoveSuperAdmin != None:
        DeSuperOP(RemoveSuperAdmin)
    if SuperAdmin != None:
        GiveSuperOP(SuperAdmin)
    _log._INFO(f"[waitress]Web服务已开启, 请在 {WebHost}:{WebPort} 访问")
    _log._INFO(f"[waitress]前端重定向CelesteNetAPI为 {CelesteNetWebRedirect}/api")
    serve(
        app,
        host=WebHost,
        port=WebPort,
        ident=None,
        threads=4,
    )