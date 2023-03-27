#!/usr/bin/env bash
# exit on error
set -o errexit  # exit on error

pip install -r ./__setup/requirements.txt

python init_env.py

python ./scripts/timedrived.py -d

python manage.py collectstatic --no-input
python manage.py migrate
