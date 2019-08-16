#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import json
import uuid
import random

import yaml

import config


class Deploy(object):
    def __init__(self):
        self._uid = config.UID_START
        self.port_range = [x for x in range(config.PORT_START, 65536)]

    def _gen_uid(self):
        uid = self._uid
        self._uid += 1
        return uid

    def _gen_port(self):
        port = random.choice(self.port_range)
        self.port_range.remove(port)
        return port

    def _gen_flag(self):
        return f'flag{{{uuid.uuid4()}}}'

    def _user_staff(self):
        add_users = [
            f"useradd -m {pcg['name']} -u {pcg['uid']} && "
            f"mkdir /home/{pcg['name']}/pwn && "
            f"echo '{pcg['flag']}' > /home/{pcg['name']}/pwn/flag.txt"
            for pcg in self.pwn_configs
        ]
        add_users = f"RUN {' && '.join(add_users)}"
        return add_users

    def _pwn_staff(self):
        copy_pwn = [
            f"COPY {os.path.join(config.PWN_BIN_PATH, pcg['name'])} /home/{pcg['name']}/pwn/"
            for pcg in self.pwn_configs
        ]
        copy_pwn = '\n'.join(copy_pwn)
        return copy_pwn

    def _chroot_staff(self):
        chroot = [
            f"cp -R /lib* /home/{pcg['name']} && "
            f"cp -R /usr/lib* /home/{pcg['name']} && "
            f"cp -R /usr/bin /home/{pcg['name']} && "
            f"mkdir /home/{pcg['name']}/dev && "
            f"mknod /home/{pcg['name']}/dev/null c 1 3 && "
            f"mknod /home/{pcg['name']}/dev/zero c 1 5 && "
            f"mknod /home/{pcg['name']}/dev/random c 1 8 && "
            f"mknod /home/{pcg['name']}/dev/urandom c 1 9 && "
            f"chmod 666 /home/{pcg['name']}/dev/* && "
            f"chown {pcg['name']}:{pcg['name']} /home/{pcg['name']}/pwn/* && "
            f"chmod 440 /home/{pcg['name']}/pwn/flag.txt && "
            f"chmod 750 /home/{pcg['name']}/pwn/{pcg['name']}"
            for pcg in self.pwn_configs
        ]
        chroot = f"RUN {' && '.join(chroot)} && chmod +x /service.sh"
        return chroot

    def detect_pwn(self):
        if not os.path.exists(config.PWN_BIN_PATH):
            os.makedirs(config.PWN_BIN_PATH)
        pwn_bin = [
            f for f in os.listdir(config.PWN_BIN_PATH)
            if os.path.isfile(os.path.join(config.PWN_BIN_PATH, f))
        ]
        pwn_bin.sort()
        self.pwns = pwn_bin

    def generate_flag(self):
        self.pwn_configs = [{
            'name': pwn,
            'uid': self._gen_uid(),
            'port': self._gen_port(),
            'flag': self._gen_flag(),
        } for pwn in self.pwns]
        with open(config.SAVED_INFO) as f:
            json.dump(self.pwn_configs, f)

    def generate_xinetd(self):
        with open(config.XINETD_CONF_FILENAME, 'w') as f:
            for pcg in self.pwn_configs:
                f.write(
                    config.XINETD_TEMPLATE.format(pwn=pcg['name'],
                                                  port=pcg['port'],
                                                  uid=pcg['uid']))

    def generate_dockerfile(self):
        template = config.DOCKER_BASE.format(
            XINETD_CONF_FILENAME=config.XINETD_CONF_FILENAME,
            user_flag=self._user_staff(),
            copy_pwn=self._pwn_staff(),
            chroot_yet=self._chroot_staff(),
        )
        with open('Dockerfile', 'w') as f:
            f.write(template)

    def generate_dockercompose(self):
        compose = yaml.safe_load(config.DOCKER_COMPOSE_BASE)
        compose['services']['my_pwnable']['ports'] = [
            f"{pcg['port']}:{pcg['port']}" for pcg in self.pwn_configs
        ]
        with open('docker-compose.yml', 'w') as f:
            yaml.safe_dump(compose, f)

    def run(self):
        self.detect_pwn()
        self.generate_flag()
        self.generate_xinetd()
        self.generate_dockerfile()
        self.generate_dockercompose()
        print(os.popen('docker-compose build --no-cache').read())
        print(os.popen('docker-compose up -d').read())


if __name__ == "__main__":
    test = Deploy()
    test.run()
