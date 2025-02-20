import asyncio
import json
import socket
import ssl

from cryptography import x509
from decouple import config, Csv
from nio import AsyncClient

from celery_app import app


@app.task
def check_cert(cert):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        if ":" in cert:
            port = int(cert.split(":")[1])
            cert = str(cert.split(":")[0])
        else:
            port = 443
        with socket.create_connection((cert, port)) as sock:
            with context.wrap_socket(
                sock,
                server_hostname=cert,
            ) as ssock:
                certificate = ssock.getpeercert(True)
                pem_data = ssl.DER_cert_to_PEM_cert(certificate)
                cert_data = x509.load_pem_x509_certificate(str.encode(pem_data))
                exp_date = cert_data.not_valid_after_utc.date()
                data = [str(exp_date), cert]
    except Exception as e:
        print(e)
        data = [str("couldn't connect"), cert]
    return data


@app.task
def check_all():
    cert_list = config("CERT_LIST", default="google.com", cast=Csv())

    results = [check_cert.delay(cert) for cert in cert_list]

    data = [result.get(disable_sync_subtasks=False) for result in results]

    updates = []
    for date in sorted(data, key=lambda date: date[0]):
        updates.append(" -> ".join(date))
    rooms = config("ROOMS", cast=Csv())

    for room in rooms:
        asyncio.run(
            send2matrix(config("MATRIX_HOST"), config("ACCESS_TOKEN"), room, updates)
        )



async def send2matrix(homeserver, access_token, room_id, updates):
    config = {
        "homeserver": homeserver,
        "access_token": access_token,
    }
    client = AsyncClient(config["homeserver"])
    client.access_token = config["access_token"]
    await client.room_send(
        room_id,
        message_type="m.room.message",
        content={"msgtype": "m.text", "body": json.dumps(updates, indent=2)},
    )
    await client.close()
