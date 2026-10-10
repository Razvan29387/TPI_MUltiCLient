# TPI_MUltiCLient

## Pornire

Pornește serverul într-un terminal:

```bash
python multiclient_server.py
```

Pornește fiecare client într-un terminal separat:

```bash
python multiclient_client1.py
python multiclient.client2.py
```

Serverul ascultă implicit pe portul `5000`, iar clienții se conectează la `127.0.0.1`. Pentru altă adresă sau alt port, serverul acceptă `--host` și `--port`, iar clienții acceptă aceleași opțiuni:

```bash
python multiclient_server.py --host 0.0.0.0 --port 5000
python multiclient_client1.py --host 127.0.0.1 --port 5000
```

Mesajele sunt retransmise tuturor clienților conectați. Scrie `/quit` pentru deconectare; oprește serverul cu `Ctrl+C`. Serverul și clienții gestionează I/O fără threading.