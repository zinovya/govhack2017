#!/usr/bin/env python
from alpr import AlprCaller
from license_plate_checker import StolenCars

def call_police(lpn, gps_tuple):
    print 'Reporting stolen car with license plate number {} at location {}'.format(license_plate_number,gps_tuple)

blastring = 'stolen_car.png'

gps_tuple = (-43.532000, 172.636847)

caller = AlprCaller(image_name=blastring)
license_plate_number = caller.get_license_plate_text()
cars = StolenCars()

if cars.test(license_plate_number) or True:
    call_police(license_plate_number, gps_tuple)

