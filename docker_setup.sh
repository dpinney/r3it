#!/bin/sh

# build image
docker-compose build

# start container
# docker-compose up -d

# stop and delete container
docker-compose down

# cleanup
docker image prune -f