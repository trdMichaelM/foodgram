#!/bin/bash

sudo docker run --rm --name foodgram_db -p 5432:5432 -e POSTGRES_PASSWORD=postgres -d -v $HOME/foodgram_db:/var/lib/postgresql/data postgres
