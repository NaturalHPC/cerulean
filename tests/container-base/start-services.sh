#!/bin/bash
echo -e "\nstarting syslog-ng..."
syslog-ng

echo -e "\nstarting sshd..."
/usr/sbin/sshd -De > /var/log/sshd.out.log 2> /var/log/sshd.err.log &

echo -e "\nStartup complete"

sleep infinity
