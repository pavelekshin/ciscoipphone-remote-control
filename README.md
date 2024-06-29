# Cisco IP Phone remote control

### Description:

This app used for remotely delete ITL/CTL certificates and restarts the Cisco IP Phones sending to them keypress
execution command (CiscoIPPhoneExecute). For concurrency used asyncio. The results are writing to SQLite/PostgresSQL
database.

[Cisco IP Phone Programmobility Guide](https://www.cisco.com/c/en/us/td/docs/voice_ip_comm/cuipph/all_models/xsi/9-1-1/CUIP_BK_P82B3B16_00_phones-services-application-development-notes.html)


```shell
.
├── README.md
├── config
│   └── config.py
├── data
│   └── session_factory.py
├── db
│   ├── db_folder.py
│   └── phonedb.sqlite
├── models
│   └── model.py
├── service
│   ├── __init__.py
│   ├── client.py
│   └── service.py
├── settings.py
├── templates
│   └── keypress_templates.yaml
├── utils.py
├── phones.csv
├── requirements.txt
├── ruff.toml
├── .env
└── main.py
```

phones.csv - list of phones ip address <br>
templates/keypress_templates.yaml - phone templates with keypress <br>
.env.example - settings <br>
config/config.py - db config factory

### Requirements:

On CUCM cluster activate Cisco CTIManager services, it's required for remote control.
For remote control you need to create End User on CUCM with Standard CTI Enabled role and associate them with IP phones.

### Run PostgreSQL in Docker:

```shell
docker run --name db -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16-alpine3.19
```

### IP Phone Information Access:

> [!NOTE]
> Cisco Unified IP Phones have an embedded web server to provide a programming interface for external applications, and
> a debugging and management interface for system administrators.
> You can access the administrative pages using a standard web browser and pointing to the IP address of the phone
> with: http://phoneIP/, where phoneIP is the IP address of the specific phone.
> These device information pages are available in either HTML format for manual debugging purposes, or in XML format for
> automation purposes. The following table lists the available URLs and their purpose.
>
> | URL                                          | Description                                         | 
> |----------------------------------------------|-----------------------------------------------------|
> | /CGI/Execute (password-protected CGI script) | The target URL of a phone push (HTTP POST) request. |

> [!NOTE]
> Supported URIs by Phone Model. Detailed
> on [Cisco](https://www.cisco.com/c/en/us/td/docs/voice_ip_comm/cuipph/all_models/xsi/9-1-1/CUIP_BK_P82B3B16_00_phones-services-application-development-notes/CUIP_BK_P82B3B16_00_phones-services-application-development-notes_chapter_0101.html#CUIP_RF_S66EDF62_00)
