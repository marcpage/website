#!/bin/bash

docker run --detach --restart always -p 8088:80 -v $PWD:/usr/share/nginx/html nginx:alpine
