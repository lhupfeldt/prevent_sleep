# Linux systemd service to prevent a server from going to sleep when there are (active) clients.

Supports SSH and NFS clients.
Uses D-Bus inhibit to prevent sleep/suspend.

**Note**:
For full functionality you must run this as root to allow access to /proc/.... in order to determine if SSH sessions are active or idle.
Depending on Linux configuration, access to the system D-Bus may also require root. In this case the program **must** be run as root.
Installation instructions are for a service running as root.

Tested on Fedora 39 with NFSv4.


## Installation

### Install OS package dependencies

```bash
sudo dnf install python3-pystemd
```

### Create a python virtual environment and install `prevent-sleep`

```bash
cd /opt
sudo python -m venv prevent_sleep --system-site-packages --upgrade-deps
sudo prevent_sleep/bin/python -m pip install --upgrade prevent-sleep  # or use path to sourcedir
prevent_sleep/bin/prevent-sleep --version
```

### Setup systemd service

```bash
sudo prevent_sleep/bin/prevent-sleep --install-service
sudo systemctl daemon-reload
sudo systemctl enable --now prevent-sleep
```

### Verify

**Note**: Use `systemd-inhibit` to check if this or other programs are preventing suspend.

```text
[xxx@yyy opt]$ systemd-inhibit
WHO            UID USER PID  COMM           WHAT              WHY                                                           MODE
ModemManager   0   root 1197 ModemManager   sleep             ModemManager needs to reset devices                           delay
NetworkManager 0   root 1239 NetworkManager sleep             NetworkManager needs to turn off networks                     delay
UPower         0   root 1794 upowerd        sleep             Pause device polling                                          delay
prevent-sleep  0   root 4678 prevent-sleep  sleep             SSH: 2 active clients [(3567, 'john'), (4007, 'jane')]        block
gdm            42  gdm  1846 gsd-power      handle-lid-switch External monitor attached or configuration changed recently   block
gdm            42  gdm  1846 gsd-power      sleep             GNOME needs to lock the screen                                delay

6 inhibitors listed.
```

```text
[xxx@yyy opt]$ systemd-inhibit
WHO            UID USER PID  COMM           WHAT              WHY                                                             MODE
ModemManager   0   root 1197 ModemManager   sleep             ModemManager needs to reset devices                             delay
NetworkManager 0   root 1239 NetworkManager sleep             NetworkManager needs to turn off networks                       delay
UPower         0   root 1794 upowerd        sleep             Pause device polling                                            delay
prevent-sleep  0   root 4678 prevent-sleep  sleep             NFS: 1 clients [('4', '192.168.4.107, Linux NFSv4.2 mylaptop')] block
prevent-sleep  0   root 4678 prevent-sleep  sleep             SSH: No activity. Will remove block at 2024-01-28T19:36:51      block
gdm            42  gdm  1846 gsd-power      handle-lid-switch External monitor attached or configuration changed recently     block
gdm            42  gdm  1846 gsd-power      sleep             GNOME needs to lock the screen                                  delay

7 inhibitors listed.
```

Note that only SSH clients with traffic during the last check period will prevent sleep!


## Development

```bash
sudo dnf install systemd-devel python3{.10,.11,.12}-devel  # For all python versions listen in noxfile.py
pip install nox
nox  # In root of checked out sources
```

Note that the test is rather rudimentary. It is *not* mocked (yet) so running it will require D-Bus access and it will fail if
being run on a server with NFS clients (if not run as root).


## More
This program [https://pypi.org/project/sleep-inhibitor/], which I found after writing `prevent-sleep`, does a similar thing.
