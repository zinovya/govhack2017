import argparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import re
import cgi
import os
import ssl
import sqlite3
import urlparse

class LocalData(object):
    records = {}


def MakeHTTPRequestHandler(db_handler):
    class HTTPRequestHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.db_handler = db_handler
            BaseHTTPRequestHandler.__init__(self, *args, **kwargs)

        def do_POST(self):
            if re.search('/api/v1/vehicle/*', self.path) is None:
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                return

            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype != 'application/json':
                self.send_response(405, 'unsupported data type: {}'.format(ctype))
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                return

            length = int(self.headers.getheader('content-length'))
            data = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=1)
            try:
                self.db_handler.add_vehicle(data)
            except:
                self.send_response(406, 'failed to parse data: {}'.format(data))
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            return

        def do_GET(self):
            if None != re.search('/api/v1/vehicle/*', self.path):
                self.get_record()
                return

            if None != re.search('/api/v1/search', self.path):
                self.find_record()
                return
            return

        def get_record(self):
            recordID = self.path.split('/')[-1]
            if not recordID:
                self.get_all_records()
                return
            try:
                record = self.db_handler.get_record(recordID)
            except:
                self.send_response(404, 'ID: {} not found'.format(recordID))
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                return

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(record)

        def get_all_records(self):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(self.db_handler.get_all_records())

        def find_record(self):
            length = int(self.headers.getheader('content-length'))
            data = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=1)
            try:
                plate = data['plate'][0]
            except:
                self.send_response(403, 'failed to parse data:{}'.format(data))
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(self.db_handler.find_by_plate(plate))

    return HTTPRequestHandler


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cert', '-cert', dest='cert', type=str, required=False,
                        default="", help='ssl certificate to be used')
    args = parser.parse_args()
    cnf = {'cert': args.cert}
    return cnf


class DbHandler:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()
        self.create_tables()

    def __del__(self):
        self.close()

    def create_tables(self):
        self.c.execute('''CREATE TABLE IF NOT EXISTS vehicles
                       (id integer PRIMARY KEY AUTOINCREMENT, latitude real, longitude real, plate string, time text)''')

    def add_vehicle(self, vehicle_data):
        lat = float(vehicle_data['lat'][0])
        long = float(vehicle_data['long'][0])
        plate = vehicle_data['plate'][0]
        tm = vehicle_data['time'][0]
        self.c.execute("INSERT INTO vehicles (latitude, longitude, plate, time) VALUES ({}, {}, '{}', '{}')".format(lat, long, plate, tm))
        self.commit()

    def get_record(self, id):
        self.c.execute('SELECT * FROM vehicles WHERE id=?', id)
        data = self.c.fetchone()
        return {'lat':data[0],
                'long':data[1],
                'plate':data[2],
                'time':data[3]}

    def get_all_records(self):
        self.c.execute('SELECT * FROM vehicles')
        rows= self.c.fetchall()
        return [{'id':row[0],
                'lat':row[1],
                'long':row[2],
                'plate':row[3],
                'time':row[4]} for row in rows]

    def find_by_plate(self, plate):
        self.c.execute("SELECT * FROM vehicles WHERE plate = '{}'".format(plate))
        rows= self.c.fetchall()
        return [{'id':row[0],
                'lat':row[1],
                'long':row[2],
                'plate':row[3],
                'time':row[4]} for row in rows]

    def commit(self):
        self.conn.commit()

def main():
    cnf = handle_args()
    db_handler = DbHandler("db/vehicle_db.sql")
    HandlerClass = MakeHTTPRequestHandler(db_handler)
    httpd = HTTPServer(('0.0.0.0', 4443), HandlerClass)
    print("started http server")

    if cnf['cert']:
        print("creating ssl socket with certificate: {}".format(cnf['cert']))
        httpd.socket = ssl.wrap_socket (httpd.socket, certfile=cnf['cert'], server_side=True)
    httpd.serve_forever()


if __name__== "__main__":
   main()
# curl -X POST --data "lat=-43&long=173" https://localhost:4443/api/v1/location/1 --header "Content-Type:application/json" --cacert keys/cert.pem
# curl -X POST --data "lat=-43.520752&long=172.648577&plate=ZG7272&time=2017-07-27T11:30" http://localhost:4443/api/v1/vehicle/1 --header "Content-Type:application/json"

# curl -X GET http://localhost:4443/api/v1/vehicle/1 --header "Content-Type:application/json"

#curl -X POST --data "lat=-43.520752&long=172.648577&plate=ZG7272&time=2017-07-27T11:30" http://localhost:4443/api/v1/vehicle/ --header "Content-Type:application/json"
#curl -X GET http://localhost:4443/api/v1/vehicle/1 --header "Content-Type:application/json"
#curl -X GET --data "plate=ZG7272" http://localhost:4443/api/v1/search --header "Content-Type:application/json"

#docker
#curl -X POST --data "lat=-43.520752&long=172.648577&plate=ZG7272&time=2017-07-27T11:30" http://localhost/api/v1/vehicle/1 --header "Content-Type:application/json"
#curl -X POST --data "lat=-43.530752&long=172.748577&plate=ZG7272&time=2017-07-27T11:30" http://localhost/api/v1/vehicle/1 --header "Content-Type:application/json"
#curl -X POST --data "lat=-43.520752&long=172.648577&plate=GUL508&time=2017-07-27T11:30" http://localhost/api/v1/vehicle/1 --header "Content-Type:application/json"

#curl -X GET --data "plate=ZG7272" http://localhost/api/v1/search --header "Content-Type:application/json"
#curl -X GET http://localhost/api/v1/vehicle/1 --header "Content-Type:application/json"