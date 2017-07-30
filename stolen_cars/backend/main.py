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

            if None != re.search('search', self.path):
                self.show_markers()
                return


            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html=HtmlGenerator(self.wfile)
            html.add_search_button()
            html.write()
            return

        def show_markers(self):
            try:
                plate = self.path.split('/')[-1].split('=')[-1]
            except:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = HtmlGenerator(self.wfile)
            html.add_markers(self.db_handler.find_by_plate(plate))
            html.add_search_button(plate)
            html.write()

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


class HtmlGenerator:
    def __init__(self, writer):
        self.header = """<head>
<meta name="viewport" content="initial-scale=1.0, width=device-width" />
<link rel="stylesheet" type="text/css" href="https://js.cit.api.here.com/v3/3.0/mapsjs-ui.css" />
<script type="text/javascript" src="https://js.cit.api.here.com/v3/3.0/mapsjs-core.js"></script>
<script type="text/javascript" src="https://js.cit.api.here.com/v3/3.0/mapsjs-service.js"></script>
<script type="text/javascript" src="https://js.cit.api.here.com/v3/3.0/mapsjs-ui.js"></script>
<script type="text/javascript" src="https://js.cit.api.here.com/v3/3.0/mapsjs-mapevents.js"></script>
</head>\n"""
        self.body = '<div id="map" style="width: 100%; height: 90%; background: grey" />\n'
        print("update location\n")
        self.map_script="""
function addMarkerToGroup(group, coordinate, html) {
  var marker = new H.map.Marker(coordinate);
  // add custom data to the marker
  marker.setData(html);
  group.addObject(marker);
}

function moveMapToChristchurch(map){
  map.setCenter({lat:-43.531058, lng:172.636085});
  map.setZoom(14);
}
var platform = new H.service.Platform({
  app_id: 's7QOoL9tDOPBZCIQDGk3',
  app_code: 'DiyEvL8t86GTKYwjvt0iHg',
  useCIT: true,
  useHTTPS: true
});
var defaultLayers = platform.createDefaultLayers();
var map = new H.Map(document.getElementById('map'),
  defaultLayers.normal.map);
var behavior = new H.mapevents.Behavior(new H.mapevents.MapEvents(map));
var ui = H.ui.UI.createDefault(map, defaultLayers);
moveMapToChristchurch(map);

function addInfoBubble(map) {
  var group = new H.map.Group();

  map.addObject(group);

  // add 'tap' event listener, that opens info bubble, to the group
  group.addEventListener('tap', function (evt) {
    // event target is the marker itself, group is a parent event target
    // for all objects that it contains
    var bubble =  new H.ui.InfoBubble(evt.target.getPosition(), {
      // read custom data
      content: evt.target.getData()
    });
    // show info bubble
    ui.addBubble(bubble);
  }, false);

"""
        self.writer=writer

    def write(self):
        self.writer.write("<html>\n{}{}\n</html>".format(self.header, self.get_body()))

    def get_body(self):
        return "<body>\n" + self.body + self.get_map_script() + self.get_search_button() + "\n</body>\n"

    def add_search_button(self, plate=''):
        self.button="""\n<form action="/search">
Find Vehicle By Licence Plate: <input type="text" name="plate" value="{}"><br>
<input type="submit" value="Find" onclick="window.location='/my/link/location';" />
</form>""".format(plate)

    def get_search_button(self):
        return self.button

    def get_map_script(self):
        return '<script  type="text/javascript" charset="UTF-8" > \n{}}}\naddInfoBubble(map);\n</script>'.format(self.map_script)


    def add_markers(self, locations):
        markers = ""
        for location in locations:
            markers += """addMarkerToGroup(group, {{lat:{}, lng:{}}},
    '<div >Licence Plate: {}</div></div><div >When observed: {}</div><img width="480px" height="360px" src="{}">');\n""".format(
                location['lat'], location['long'], location['plate'], location['time'], location['img'])

        self.map_script += markers


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
                       (id integer PRIMARY KEY AUTOINCREMENT, latitude real, longitude real, plate string, time text, img text)''')

    def add_vehicle(self, vehicle_data):
        lat = float(vehicle_data['lat'][0])
        long = float(vehicle_data['long'][0])
        plate = vehicle_data['plate'][0]
        tm = vehicle_data['time'][0]
        img = vehicle_data['img'][0]
        self.c.execute("INSERT INTO vehicles (latitude, longitude, plate, time, img) VALUES ({}, {}, '{}', '{}', '{}')".format(lat, long, plate, tm, img))
        self.commit()

    def get_record(self, id):
        self.c.execute('SELECT * FROM vehicles WHERE id=?', id)
        data = self.c.fetchone()
        return {'lat':data[0],
                'long':data[1],
                'plate':data[2],
                'time':data[3],
                'img':data[4]}

    def get_all_records(self):
        self.c.execute('SELECT * FROM vehicles')
        rows= self.c.fetchall()
        return [{'id':row[0],
                'lat':row[1],
                'long':row[2],
                'plate':row[3],
                'time':row[4],
                 'img': row[5]} for row in rows]

    def find_by_plate(self, plate):
        self.c.execute("SELECT * FROM vehicles WHERE plate = '{}'".format(plate))
        rows= self.c.fetchall()
        return [{'id':row[0],
                'lat':row[1],
                'long':row[2],
                'plate':row[3],
                'time':row[4],
                 'img': row[5]} for row in rows]

    def commit(self):
        self.conn.commit()

def main():
    cnf = handle_args()
    db_handler = DbHandler("vehicle_db.sql")
    HandlerClass = MakeHTTPRequestHandler(db_handler)
    httpd = HTTPServer(('0.0.0.0', 3997), HandlerClass)
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