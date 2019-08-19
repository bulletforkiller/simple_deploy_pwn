#!/usr/bin/python3
# -*- coding:utf-8 -*-

import os
import json
import uuid
import random
import shutil

import yaml

import config
from utils import clean_before


class Deploy(object):
    def __init__(self):
        self._uid = config.UID_START
        self.port_range = [x for x in range(config.PORT_START, 65536)]
        self.exec_x86 = set()
        self.exec_x64 = set()
        self._work_ready()

    def __del__(self):
        self._work_clean()

    def _work_ready(self):
        self._temp_work = f'_tmp_{random.randint(100000, 999999)}'
        os.mkdir(self._temp_work)

    def _work_clean(self):
        shutil.rmtree(self._temp_work)

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

    def pwn_ready(self):
        pwn_bin = [[
            f,
            os.path.join(config.PWN_BIN_PATH, f),
            os.popen(f'file {os.path.join(config.PWN_BIN_PATH, f)}').read()
        ] for f in os.listdir(config.PWN_BIN_PATH)
                   if os.path.isfile(os.path.join(config.PWN_BIN_PATH, f))]
        pwn_bin = list(filter(lambda x: 'ELF' in x[2], pwn_bin))
        for index in range(len(pwn_bin)):
            pwn_dst = os.path.join(
                os.path.join(self._temp_work, pwn_bin[index][0]), 'pwn')
            if 'ELF 32' in pwn_bin[index][2]:
                self.exec_x86.add(pwn_dst)
            if 'ELF 64' in pwn_bin[index][2]:
                self.exec_x64.add(pwn_dst)
            os.makedirs(pwn_dst)
            shutil.copy(pwn_bin[index][1], os.path.join(pwn_dst, 'pwn'))
            pwn_bin[index][1] = pwn_dst
        self.pwns = pwn_bin

    def libc_ready(self):
        sepcify_x86_libc = True if (os.path.isfile(
            os.path.join(config.LIBC_PATH, 'x86_ld.so')) and os.path.isfile(
                os.path.join(config.LIBC_PATH, 'x86_libc.so.6'))) else False
        sepcify_x64_libc = True if (os.path.isfile(
            os.path.join(config.LIBC_PATH, 'x64_ld.so')) and os.path.isfile(
                os.path.join(config.LIBC_PATH, 'x64_libc.so.6'))) else False
        for pwn in self.exec_x86:
            pwn_path = f"/pwn/{os.path.split(pwn)[-1]}"
            runsh = os.path.join(pwn, 'run.sh')
            with open(runsh, 'w') as f:
                f.write('#!/bin/sh\n')
                f.write('cd /pwn\n')
                if sepcify_x86_libc:
                    shutil.copy(
                        os.path.join(config.LIBC_PATH, config.X86_LD_NAME),
                        os.path.join(pwn, config.X86_LD_NAME))
                    shutil.copy(
                        os.path.join(config.LIBC_PATH, config.X86_LIBC_NAME),
                        os.path.join(pwn, config.TARGET_LIBC_NAME))
                    f.write(
                        f"LD_PRELOAD=/pwn/{config.TARGET_LIBC_NAME} /pwn/{config.X86_LD_NAME} {pwn_path}"
                    )
                else:
                    f.write(pwn_path)
            os.chmod(runsh, 0o550)
        for pwn in self.exec_x64:
            pwn_path = f"/pwn/{os.path.split(pwn)[-1]}"
            runsh = os.path.join(pwn, 'run.sh')
            with open(runsh, 'w') as f:
                f.write('#!/bin/sh\n')
                f.write('cd /pwn\n')
                if sepcify_x64_libc:
                    shutil.copy(
                        os.path.join(config.LIBC_PATH, config.X64_LD_NAME),
                        os.path.join(pwn, config.X64_LD_NAME))
                    shutil.copy(
                        os.path.join(config.LIBC_PATH, config.X64_LIBC_NAME),
                        os.path.join(pwn, config.TARGET_LIBC_NAME))
                    f.write(
                        f"LD_PRELOAD=/pwn/{config.TARGET_LIBC_NAME} /pwn/{config.X64_LD_NAME} /pwn/{os.path.split(pwn)[-1]}"
                    )
                else:
                    f.write(pwn_path)
            os.chmod(runsh, 0o550)

    def secret_ready(self):
        self.pwn_configs = []
        for pwn in self.pwns:
            flag = self._gen_flag()
            self.pwn_configs.append({
                'name': pwn[0],
                'uid': self._gen_uid(),
                'port': self._gen_port(),
                'flag': flag,
                'local_path': pwn[1],
            })
            flag_file = os.path.join(pwn[1], config.FLAG_FILE_NAME)
            with open(flag_file, 'w') as f:
                f.write(flag)
            os.chmod(flag_file, 0o440)
        with open(config.SAVED_INFO, 'w') as f:
            json.dump(self.pwn_configs, f)

    def _user_staff(self):
        add_users = [
            f"useradd -m {pcg['name']} -u {pcg['uid']} && "
            f"mkdir /home/{pcg['name']}/pwn" for pcg in self.pwn_configs
        ]
        add_users = f"RUN {' && '.join(add_users)}"
        return add_users

    def _pwn_staff(self):
        copy_pwn = [
            f"COPY {pcg['local_path']} /home/{pcg['name']}/pwn"
            for pcg in self.pwn_configs
        ]
        copy_pwn = '\n'.join(copy_pwn)
        return copy_pwn

    def _chroot_staff(self):
        chroot = [
            f"cp -R /lib* /home/{pcg['name']} && "
            f"cp -R /usr/lib* /home/{pcg['name']} && "
            f"cp -R /bin /home/{pcg['name']} && "
            f"mkdir /home/{pcg['name']}/dev && "
            f"mknod /home/{pcg['name']}/dev/null c 1 3 && "
            f"mknod /home/{pcg['name']}/dev/zero c 1 5 && "
            f"mknod /home/{pcg['name']}/dev/random c 1 8 && "
            f"mknod /home/{pcg['name']}/dev/urandom c 1 9 && "
            f"chmod 666 /home/{pcg['name']}/dev/* && "
            f"chown {pcg['name']}:{pcg['name']} /home/{pcg['name']}/pwn/*"
            for pcg in self.pwn_configs
        ]
        chroot = f"RUN {' && '.join(chroot)} && chmod +x /service.sh"
        return chroot

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
            create_user=self._user_staff(),
            copy_file=self._pwn_staff(),
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
        self.pwn_ready()
        self.libc_ready()
        self.secret_ready()
        self.generate_xinetd()
        self.generate_dockerfile()
        self.generate_dockercompose()
        print(os.popen('docker-compose build --no-cache').read())
        print(os.popen('docker-compose up -d').read())


if __name__ == "__main__":
    clean_before()
    test = Deploy()
    test.run()
