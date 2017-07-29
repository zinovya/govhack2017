#!/bin/bash
#docker
printf "\npost data:\n"
curl -X POST --data "lat=-43.520752&long=172.648577&plate=ZG7272&time=2017-07-27T11:30" http://localhost/api/v1/vehicle/1 --header "Content-Type:application/json"
curl -X POST --data "lat=-43.530752&long=172.748577&plate=ZG7272&time=2017-07-27T11:30" http://localhost/api/v1/vehicle/1 --header "Content-Type:application/json"
curl -X POST --data "lat=-43.520752&long=172.648577&plate=GUL508&time=2017-07-27T11:30" http://localhost/api/v1/vehicle/1 --header "Content-Type:application/json"

printf "\nget one by id:\n"
curl -X GET http://localhost/api/v1/vehicle/1 --header "Content-Type:application/json"

printf "\nget all:"
curl -X GET http://localhost/api/v1/vehicle/ --header "Content-Type:application/json"

printf "\nget one by plate:\n"
curl -X GET --data "plate=ZG7272" http://localhost/api/v1/search --header "Content-Type:application/json"
printf "\n"
