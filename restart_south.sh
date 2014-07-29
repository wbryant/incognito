#! /bin/bash

#Reset South and begin again!

rm -r annotation/migrations/
rm -r cogzymes/migrations/
# ./manage.py reset south
mysql bth_model -uroot -e 'drop database bth_model;'
mysql -uroot -e 'create database bth_model;'
./manage.py syncdb

./manage.py convert_to_south annotation
./manage.py migrate annotation

./manage.py convert_to_south cogzymes
./manage.py migrate cogzymes