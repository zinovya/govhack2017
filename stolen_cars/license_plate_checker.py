#!/usr/bin/env python
"""
Look up license plate in stolen car db in Canterbury / NZ
By Team Woo-Hoogle for Govhack 2017
"""

import argparse
import csv
import urllib

class StolenCars(object):

    def __init__(self, url=None):
        if url is None:
            # Canterbury Region
            self.url = 'http://www.police.govt.nz/stolenwanted/vehicles/csv/download?tid=119&all=false&gzip=false'
        else:
            self.url = url
        self.update()

    def update(self):

        csv_data = urllib.urlopen(self.url)
        reader = csv.DictReader(csv_data, fieldnames=['plate', 'color', 'brand', 'description', 'year', 'type', 'date', 'location'])
        self.plates = []
        self.stolen_cars = []

        for row in reader:
            self.plates.append(row['plate'])
            self.stolen_cars.append([row])

    def test(self, license_plate=None):
        if license_plate is not None and license_plate in self.plates:
                return True
        return False

    def print_all_plates(self):
        for p in self.plates:
            print p

def parse_args():
    parser = argparse.ArgumentParser(description='Lookup license plate status')
    parser.add_argument('--plate', dest='lp',
                        help='Define the license plate',
                        default=None, type=str)
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    
    args = parse_args()
    cars = StolenCars()
    if args.lp is None or len(args.lp) < 1: # Test mode
        stolen_plate = 'Z999G'
        regular_plate = 'GUL508'
        cars.print_all_plates()
        print cars.test(stolen_plate)
        print cars.test(regular_plate)
    else:
        print cars.test(args.lp)
