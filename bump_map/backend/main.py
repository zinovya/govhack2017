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

class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if None != re.search('/api/v1/location/*', self.path):
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'application/json':
                length = int(self.headers.getheader('content-length'))
                data = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=1)
                recordID = self.path.split('/')[-1]
                LocalData.records[recordID] = data
                print("record %s has added successfully" % recordID)
            else:
                data = {}
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
        else:
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
        return

    def do_GET(self):
        if None != re.search('/api/v1/location/*', self.path):
            recordID = self.path.split('/')[-1]
            if LocalData.records.has_key(recordID):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(LocalData.records[recordID])
            else:
                self.send_response(400, 'Bad Request: record does not exist')
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
        else:
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
        return


def handle_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cert', '-cert', dest='cert', type=str, required=False,
                        default="", help='ssl certificate to be used')
    args = parser.parse_args()
    cnf = {'cert': args.cert}
    return cnf

def create_db(db_name):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS bump_locations
             (id int, latitude real, longitude real)''')

def main():
    cnf = handle_args()
    create_db("db/location_db.sql");
    httpd = HTTPServer(('0.0.0.0', 4443), HTTPRequestHandler)
    print("started http server")

    if cnf['cert']:
        print("creating ssl socket with certificate: {}".format(cnf['cert']))
        httpd.socket = ssl.wrap_socket (httpd.socket, certfile=cnf['cert'], server_side=True)
    httpd.serve_forever()


if __name__== "__main__":
   main()
# curl -X POST --data "lat=-43&long=173" https://localhost:4443/api/v1/location/1 --header "Content-Type:application/json" --cacert keys/cert.pem
# curl -X GET https://localhost:4443/api/v1/getrecord/1 --header "Content-Type:application/json" --cacert keys/cert.pem
