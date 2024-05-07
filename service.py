from asyncio import Future, Task
from operator import or_, and_

import progressbar as pb
import yaml
import csv
import asyncio
import datetime
import ipaddress

from lxml import etree
from typing import Optional, Awaitable, Iterable, Any, Generator
from sqlalchemy import Update, Select, Executable, Delete
from aiohttp import ClientSession, BasicAuth, ClientTimeout

from models.phone import Phone, StatusEnum
from data import session_factory
from settings import USER, USER_PWD, PAUSE, CHUNK_SIZE
from more_itertools import chunked


def create_template(template: list[str]):
    """
    Create list of keypress for selected phone template.
    :param template: List with keypress command
    :return: list with xml keypress command
    """

    keynavi = []

    for keypress in template:
        root = etree.Element('CiscoIPPhoneExecute')
        child_key_execute = etree.SubElement(root, 'ExecuteItem')
        child_key_execute.set('Priority', '0')
        child_key_execute.set('URL', keypress)
        xml = etree.tostring(root, pretty_print=True, encoding="unicode")
        keynavi.append(xml)
    return keynavi


def load_yaml_config(path: str) -> dict[str, list[str]]:
    """
    Read phone YAML keypress file and convert it to dict.
    :param path: path to .yaml file with template
    :return: dict with keypress template
    """

    with open(path, "r") as f:
        try:
            yaml_dict = yaml.safe_load(f)
        except yaml.YAMLError as err:
            print(err)
    return yaml_dict


def read_phones(path: str) -> Generator[str, None, None]:
    """
    Read phones from CSV
    :param path: path to .csv with phones list
    :return: generator with phone ip address
    """
    with open(path, 'r', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            ip = ''.join(row)
            try:
                if ipaddress.ip_address(ip):
                    yield ip
            except ipaddress.AddressValueError as err:
                print(err)
            except ValueError as err:
                print(err)


async def insert_phones(ip_address: str) -> int:
    """
    Insert phone into DB
    :param ip_address: phone ip address
    :return: number of inserted phones
    """
    cnt = 0
    phone = await find_phone(ip_address)
    if not phone:
        await create_phone(ip_address)
        cnt += 1
    return cnt


async def find_phone(ip_address: str) -> str | None:
    """
    Find phone ip address in DB
    :param ip_address: phone ip address
    :return: phone ip address
    """
    async with session_factory.async_get_session() as session:
        phone = await session.execute(
            Select(Phone).
            filter(Phone.ip_address == ip_address)
        )
    return phone.scalars().first()


async def create_phone(ip_address: str) -> None:
    """
    Add phone into DB table
    :param ip_address: phone ip address
    """
    phone = Phone()
    phone.ip_address = ip_address
    async with session_factory.async_get_session() as session, session.begin():
        session.add(phone)


async def get_phones() -> list[str]:
    """
    Get list of phones which not have "SUCCESS" status code
    :return: list of phones which status not "SUCCESS"
    """
    filters = [Phone.status != "SUCCESS", Phone.status.is_(None)]
    async with session_factory.async_get_session() as session, session.begin():
        phones = await session.execute(
            Select(Phone.ip_address).filter(or_(*filters)))
    return phones.scalars().all()


async def get_phone_after_complete(phones: list[str]) -> dict[str, list[str] | int] | None:
    """
    Get results from DB
    :param phones: get initial phones list for this session
    :return:  dict with SUCCESS and ERROR phones list
    """

    result = {}

    result["Success"] = await _get_phones(
        Select(Phone.ip_address)
        .filter(
            and_(
                Phone.status == "SUCCESS", Phone.ip_address.in_(phones))
        )
    )

    result["Error"] = await _get_phones(
        Select(Phone.ip_address)
        .filter(
            and_(
                Phone.status != "SUCCESS", Phone.ip_address.in_(phones)
            )
        )
    )

    result["Devices"] = len(result["Success"] + result["Error"])
    return result


async def _get_phones(stmt: Select[tuple[Any, ...]]) -> list[str]:
    async with session_factory.async_get_session() as session:
        result = await session.execute(stmt)
    return result.scalars().all()


async def send_keypress(session: ClientSession, ip: str, keynavi_config: list[str]) -> dict[str, Any]:
    """
    Send keypress to phone
    :param session: asyncio.ClientSession
    :param ip: phone ip address for connection
    :param keynavi_config: key navigation list sending to phone
    :return: dict with ip address and response code
    """
    url = f"http://{ip}/CGI/Execute"
    headers = {'Content-Type': 'text/xml;charset=utf-8'}  # application/xml

    responses = []

    for xml in keynavi_config:
        async with session.post(url,
                                auth=BasicAuth(USER, USER_PWD),
                                headers=headers,
                                data={"XML": xml}
                                ) as resp:
            responses.append(resp.status)
        await asyncio.sleep(PAUSE)
    return {
        "ip": ip,
        "response": 200 if all(i <= 400 for i in responses) else responses[-1],
    }


async def create_async_client_session(phones: list[str], keynavi_config: list[str]):
    """
    Create async ClientSession and run send keypress
    :param phones: list of phones
    :param keynavi_config: list of key navigation for loaded phones
    """
    print("Passed phones: ", phones)

    session_timeout = ClientTimeout(sock_read=3, sock_connect=3, connect=3)
    async with ClientSession(timeout=session_timeout) as session:
        for number, chunk in enumerate(chunked(phones, CHUNK_SIZE), start=1):
            pending = [
                asyncio.create_task(
                    send_keypress(session, ip, keynavi_config), name=f"Task-{ip}"
                ) for ip in chunk
            ]
            print(f"Chunk: {number}, contains ip address: {chunk}")
            with pb.ProgressBar(max_value=len(chunk), term_width=120, max_error=False) as bar:
                complete = 0
                while pending:
                    done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                    complete += len(done)
                    bar.update(complete)
                    await asyncio.create_task(tasks_action(done))


async def tasks_action(done: Iterable[Task]) -> None:
    """
    Get complete task and run according DB query
    :param done:  Iterable[Task]
    """
    for task in done:
        ip_addr = task.get_name().removeprefix("Task-")  # substring ip address from task name
        if task.exception() is None:
            task_result: dict = task.result()
            if task_result.get("response") <= 400:  # If response code below 400, we mark this result as SUCCESS
                await update_phones(
                    ip=ip_addr,
                    status=StatusEnum.SUCCESS,
                    error=f"Response {task_result.get('response')}",
                )
            else:  # Mark other response code as ERROR
                await update_phones(
                    ip=ip_addr,
                    status=StatusEnum.ERROR,
                    error=f"Response {task_result.get('response')}",
                )
        else:  # If task complete with exception we mark this result as ERROR and write ERROR message in DB
            await update_phones(
                ip=ip_addr,
                status=StatusEnum.ERROR,
                error=str(task.exception()),
            )


async def update_phones(ip: str, status: StatusEnum, error: str = None) -> int:
    """
    Update phone status in DB
    :param ip:  phone ip
    :param status:  phone status
    :param error:  phone error
    :return:  return count of updated rows
    """
    async with session_factory.async_get_session() as session, session.begin():
        update = await session.execute(
            Update(Phone)
            .filter(Phone.ip_address == ip)
            .values(
                status=status,
                updated=datetime.datetime.now(),
                error=error
            ))
    return update.rowcount


async def clear_table() -> None:
    async with session_factory.async_get_session() as session, session.begin():
        await session.execute(Delete(Phone))
