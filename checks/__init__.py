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

import os

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECT_PATH = os.path.join(DIR_PATH, os.pardir)
REQUIREMENTS_FILE = os.path.join(PROJECT_PATH, 'requirements.yaml')
