#   -*- coding: utf-8 -*-
#
#   This file is part of skale-checks
#
#   Copyright (C) 2021-Present SKALE Labs
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from dataclasses import dataclass
import requests


@dataclass
class Response:
    status: str
    payload: dict

    ERROR_STATUS = 'error'
    OK_STATUS = 'ok'

    def is_status_ok(self) -> bool:
        return self.status == self.OK_STATUS


class Connector:
    def __init__(self, ip, timeout=10):
        self.ip = ip
        self.timeout = timeout

    def send_request(self, path) -> Response:
        try:
            url = f'{self.ip}{path}'
            response = requests.get(url=url, timeout=self.timeout)
            response.raise_for_status()
            raw_data = response.json()
            if raw_data['error']:
                return construct_err_response(raw_data['error'])
            return construct_ok_response(raw_data['data'])
        except requests.exceptions.RequestException as msg:
            return construct_err_response(msg=str(msg))


def construct_ok_response(data=None) -> Response:
    if data is None:
        data = {}
    return Response(Response.OK_STATUS, data)


def construct_err_response(msg=None) -> Response:
    if msg is None:
        msg = {}
    return Response(Response.ERROR_STATUS, msg)
