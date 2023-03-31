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
    "token": "Voemjd8i.............................................hfU8Vj2wLy7z54uuajwTQ==",
    "url": "https://us-east-1-1.aws.cloud2.influxdata.com",
    "host": "us-east-1-1.aws.cloud2.influxdata.com",
    "port": 443,
    "org": "<Org>",
    "bucket": "<bucket>"
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
