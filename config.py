#!/usr/bin/env python3
# -*- coding:utf-8 -*-

UID_START = 1000
PORT_START = 8848
PWN_BIN_PATH = './bin'
SAVED_INFO = 'secret.json'
FLAG_FILE_NAME = 'flags.txt'
XINETD_CONF_FILENAME = "pwn.xinetd"

XINETD_TEMPLATE = """service {pwn}
{{
    disable = no
    socket_type = stream
    protocol    = tcp
    wait        = no
    user        = root
    type        = UNLISTED
    port        = {port}
    bind        = 0.0.0.0
    server      = /usr/sbin/chroot
    server_args = --userspec={uid}:{uid} /home/{pwn} /pwn/{pwn}
    # safety options
    per_source  = 10 # the maximum instances of this service per source IP address
    rlimit_cpu  = 20 # the maximum number of CPU seconds that the service may use
    rlimit_as  = 100M # the Address Space resource limit for the service
    #access_times = 2:00-9:00 12:00-24:00
}}

"""

DOCKER_BASE = """
FROM ubuntu:16.04

RUN echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial main restricted universe multiverse" > /etc/apt/sources.list \\
&& echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial-updates main restricted universe multiverse" >> /etc/apt/sources.list \\
&& echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial-backports main restricted universe multiverse" >> /etc/apt/source.list \\
&& echo "deb http://mirrors.tuna.tsinghua.edu.cn/ubuntu/ xenial-security main restricted universe multiverse" >> /etc/apt/sources.list \\
&& apt update && apt install xinetd lib32z1 -y && apt clean \\
&& rm -rf /var/lib/apt/lists/ && rm -rf /root/.cache && rm -rf /tmp/* /var/lib/apt/* /var/cache/* /var/log/*

COPY ./{XINETD_CONF_FILENAME} /etc/xinetd.d/pwn
COPY ./service.sh /service.sh

# Add user and handle file
{user_flag}

# Copy pwn file
{copy_pwn}

# Chroot
{chroot_yet}


CMD ["/service.sh"]

"""

DOCKER_COMPOSE_BASE = """version: '3'
services:
 my_pwnable:
   image: pwn_deploy:latest
   build:
    context: ./
   container_name: pwn_deploy
   ports:
"""
