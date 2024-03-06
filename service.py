from asyncio import Future

import yaml
import csv
import asyncio
import datetime
import re

from lxml import etree
from typing import List, Optional, Awaitable, Iterable, Dict
from sqlalchemy import Update, Select
from aiohttp import ClientSession, BasicAuth, ClientTimeout

from models.phone import Phone, StatusEnum
from utils import async_timed
from data import session_factory
import settings


def create_tempalte(template):
    keynavi = []

    for keypress in template:
        root = etree.Element('CiscoIPPhoneExecute')
        child_key_execute = etree.SubElement(root, 'ExecuteItem')
        child_key_execute.set('Priority', '0')
        child_key_execute.set('URL', keypress)
        xml = etree.tostring(root, pretty_print=True, encoding="unicode")
        keynavi.append(xml)
    return keynavi


def load_yaml_config(path: str) -> Dict[str, str]:
    with open(path, "r") as f:
        try:
            yaml_dict = yaml.safe_load(f)
        except yaml.YAMLError as err:
            print(err)
    return yaml_dict


def read_phones(path: str) -> str:
    with open(path, 'r', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            phoneIP = ''.join(row)
            yield phoneIP


def insert_phones(ip_address: str) -> int:
    cnt = 0
    phone = find_phone(ip_address)
    if not phone:
        create_phone(ip_address)
        cnt += 1
    return cnt


def find_phone(ip_address: str) -> Optional[str]:
    session = session_factory.get_session()
    with session as session:
        phone = session.scalars(
            Select(Phone).
            filter(Phone.ip_address == ip_address)
        ).first()
    return phone


def create_phone(ip_address: str):
    session = session_factory.get_session()
    phone = Phone()
    phone.ip_address = ip_address
    with session as session, session.begin():
        session.add(phone)


def get_phones(rows: int) -> List[str]:
    session = session_factory.get_session()
    with session as session, session.begin():
        phones = session.scalars(
            Select(Phone.ip_address).where((Phone.status != "SUCCESS") | (Phone.status == None))).all()
    return phones


def get_phone_after_complete(phones: List[str]) -> Dict[str, List[str | None]]:
    session = session_factory.get_session()

    result = {}

    with session as session, session.begin():
        result["Success"] = session.scalars(
            Select(Phone.ip_address).where(Phone.status == "SUCCESS").filter(Phone.ip_address.in_(phones))).all()
        result["Error"] = session.scalars(
            Select(Phone.ip_address).where(Phone.status != "SUCCESS").filter(Phone.ip_address.in_(phones))).all()
    result["Devices"] = len(result["Success"] + result["Error"])
    return result


async def send_keypress(session: ClientSession, ip: str, keynavi_config: List[str]) -> Dict[str, str | int]:
    url = f"http://{ip}/CGI/Execute"
    headers = {'Content-Type': 'text/xml;charset=utf-8'}  # application/xml

    responses = []

    for xml in keynavi_config:
        async with session.post(url, auth=BasicAuth(settings.AXL_USER, settings.AXL_USER), headers=headers,
                                data={"XML": xml}) as resp:
            responses.append(resp.status)
        await asyncio.sleep(settings.PAUSE)
    return {
        "ip": ip,
        "response": 200 if all(i <= 400 for i in responses) else responses[-1],
    }


async def create_async_client_session(phones: List[str], keynavi_config: List[str]):
    print("Passed phones: ", phones)

    session_timeout = ClientTimeout(sock_read=3, sock_connect=3, connect=3)
    async with ClientSession(timeout=session_timeout) as session:
        pending = [asyncio.create_task(send_keypress(session, ip, keynavi_config)) for ip in phones]

        total = len(pending)
        complete = 0

        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            complete += len(done)

            print(f"Total tasks complete: {complete}/{total}")
            print(f"Pending tasks: {len(pending)}")
            await async_action_on_tasks(done)


async def async_action_on_tasks(done: Future[Awaitable, Iterable]):
    for task in done:
        if task.exception() is None:
            task = task.result()
            if task["response"] <= 400:
                await async_update_phones(ip=task["ip"], status=StatusEnum.SUCCESS,
                                          error=f"Response {task['response']}", )
            else:
                await async_update_phones(ip=task["ip"], status=StatusEnum.ERROR,
                                          error=f"Response {task['response']}", )
        else:
            reg = re.search(r"(\d+.\d+.\d+.\d+)", str(task.exception()))
            if reg:
                await async_update_phones(ip=str(reg.group()), status=StatusEnum.ERROR,
                                          error=str(task.exception()), )


async def async_update_phones(ip: str, status: StatusEnum, error: str = None) -> int:
    session = session_factory.async_get_session()
    async with session as session, session.begin():
        update = await session.execute(Update(Phone).where(Phone.ip_address == ip). \
            values(
            status=status,
            updated=datetime.datetime.now(),
            error=error
        ))
    return update.rowcount
