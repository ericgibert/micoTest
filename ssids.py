try:
    from micropython import const
    SSIDs = const((
        ("ssid1", 'passwd123'),
        ("ssid2", 'passwd222')
        ))
except ModuleNotFoundError:
    pass

# influxDb on the CLoud
influxDBsecrets = {
    "token": "Voemjd8iRFpigEaDcBPB_EwKgBy_5W7YSnogsCkRvSIrA-EB7RXEky-TgM9jbZCXOhfU8Vj2wLy7z54uuajwTQ==",
    "url": "https://us-east-1-1.aws.cloud2.influxdata.com",
    "host": "us-east-1-1.aws.cloud2.influxdata.com",
    "port": 443,
    "org": "Perso",
    "bucket": "Pico/autogen"
}

# local database on Linux server
# influxDBsecrets = {
#     "token": "lfpFxGZ0..................................................PRVA3antbZeKEw==",
#     "host": "192.168.18.3",
#     "port": "8086",
#     "org": "<Org>",
#     "bucket": "<bucket>"
# }

try:
    LOCALTZ = const(+8)
except NameError:
    LOCALTZ = +8
