#!/bin/bash

# Eat CPU for a few seconds
i=0
while ((i < 4000000)) ; do
    i=$((i + 1))
done


# Then sleep forever
while true ; do
    sleep 10
done

