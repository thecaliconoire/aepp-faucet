#!/usr/bin/env python3
# version 0.2.1-DEV

import os
import sys
import logging
import argparse

# flask
from flask import Flask, jsonify

# aeternity
from aeternity.epoch import EpochClient
from aeternity.signing import KeyPair
from aeternity.config import Config


# also log to stdout because docker
root = logging.getLogger()
root.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch.setFormatter(formatter)
root.addHandler(ch)

app = Flask(__name__)

logging.getLogger("aeternity.epoch").setLevel(logging.WARNING)
# logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
# logging.getLogger("engineio").setLevel(logging.ERROR)


@app.after_request
def after_request(response):
    """enable CORS"""
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    return response


@app.route('/rest/topup/<recipient_address>')
def rest_topup(recipient_address):
    """top up an account"""
    # genesys key
    bank_wallet_key = os.environ.get('BANK_WALLET_KEY')
    kp = KeyPair.from_private_key_string(bank_wallet_key)
    # target node
    Config.set_defaults(Config(
        external_url=os.environ.get('EPOCH_URL', "https://sdk-testnet.aepps.com")
    ))
    # amount
    amount = int(os.environ.get('TOPUP_AMOUNT', 250))
    ttl = int(os.environ.get('TX_TTL', 100))
    tx = EpochClient().spend(kp, recipient_address, amount, tx_ttl=ttl)
    logging.info(f"top up accont {recipient_address} of {amount} tx_ttl:{ttl} tx_hash: {tx[1]}")
    return jsonify({"tx_hash": tx[1]})

#     ______  ____    ____  ______     ______
#   .' ___  ||_   \  /   _||_   _ `. .' ____ \
#  / .'   \_|  |   \/   |    | | `. \| (___ \_|
#  | |         | |\  /| |    | |  | | _.____`.
#  \ `.___.'\ _| |_\/_| |_  _| |_.' /| \____) |
#   `.____ .'|_____||_____||______.'  \______.'
#


def cmd_start(args=None):
    root.addHandler(app.logger)
    logging.info("topup service started")
    app.run(host='0.0.0.0')


if __name__ == '__main__':
    cmds = [
        {
            'name': 'start',
            'help': 'start the top up service',
            'opts': []
        }
    ]
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'command'
    # register all the commands
    for c in cmds:
        subp = subparsers.add_parser(c['name'], help=c['help'])
        # add the sub arguments
        for sa in c.get('opts', []):
            subp.add_argument(*sa['names'],
                              help=sa['help'],
                              action=sa.get('action'),
                              default=sa.get('default'))

    # parse the arguments
    args = parser.parse_args()
    # call the command with our args
    ret = getattr(sys.modules[__name__], 'cmd_{0}'.format(
        args.command.replace('-', '_')))(args)