# Running a SWaveform Application as a Service with Systemd

1. Create virtual env

```bash
# apt-get install python3-venv
python3.8 -m venv ./venv/
. ./venv/bin/activate
pip3 install flask tslearn gevent
```

/etc/systemd/system/swaveform.service

```service
[Unit]
Description=SWaveform Application
After=network.target

[Service]
User=user
WorkingDirectory=/home/user/Public/swaveform
ExecStart=/home/user/Public/swaveform/venv/bin/python server.py db:_GTT port:9915
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start swaveform
```
