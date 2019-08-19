# Simply deploy pwn

> A tool help you to deploy multi pwns with custom version libc in a single docker container use chroot.

## [README.md](https://github.com/bulletforkiller/simple_deploy_pwn/blob/master/README.md)

## Preparetory work
1. Install the newest version docker
   - Help yourself with [Docker docs](https://docs.docker.com/install/)
2. Makesure your python3 version >= 3.6
   - ```python3 --version```
   - If not, you can use miniconda to manage your python version.
3. Install python requirements
   - ```pip3 install -r requirements.txt```

## Usage
1. Just put up your pwn program(s) in ./bin folder.
2. If you need custom version libc control, both ld.so and libc.so.6 is needed. Change the libc(ld) name in config.py if you need.
   - Name is to distinguish the arch(x86 or x64), then put them into ./libc folder.
3. Then run the deploy.py and have fun.
   - ```python3 deploy.py```
4. All infomation about pwn is stored in secret.json.

## Reference
https://github.com/giantbranch/pwn_deploy_chroot

## Attention
1. If you feel confused about this program's behavior, please contact me soon or write issues.
2. I'm very glad if you help me develop and perfect this project.
