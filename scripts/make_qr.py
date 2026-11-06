"""Offline QR generation; do not submit the public URL to a third-party QR service."""
import argparse
from pathlib import Path
from urllib.parse import urlparse
def main():
    parser=argparse.ArgumentParser();parser.add_argument('url');args=parser.parse_args()
    if urlparse(args.url).scheme!='https' or not urlparse(args.url).hostname:parser.error('请输入已验证的HTTPS公网地址')
    try:import qrcode
    except ImportError:parser.error('请先安装可选依赖：python -m pip install qrcode[pil]')
    target=Path(__file__).resolve().parents[1]/'output/access-qr.png';target.parent.mkdir(exist_ok=True)
    qrcode.make(args.url).save(target);print(target)
if __name__=='__main__':main()
