#!/bin/sh

# re-build and start container
# docker-compose up --build -d

# stop and delete container
docker-compose down

# cleanup
docker image prune -f