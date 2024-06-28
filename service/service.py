import asyncio
import csv
import datetime
import ipaddress
from asyncio import Task
from operator import and_, or_
from typing import Any, Generator

import progressbar as pb
import yaml
from lxml import etree
from more_itertools import chunked
from sqlalchemy import Delete, Select, Update

from data import session_factory
from models.model import Phone, StatusEnum
from service.client import Client
from settings import settings

background_tasks = set()


def create_template(template: list[str]):
    """
    Create list of keypress for selected phone template
    :param template: List with keypress command
    :return: list with xml keypress command
    """

    keynavi = []

    for keypress in template:
        root = etree.Element("CiscoIPPhoneExecute")
        child_key_execute = etree.SubElement(root, "ExecuteItem")
        child_key_execute.set("Priority", "0")
        child_key_execute.set("URL", keypress)
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
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            ip = "".join(row)
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
        select_phone = await session.execute(
            Select(Phone.ip_address).filter(Phone.ip_address == ip_address)
        )
    return select_phone.scalars().first()


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
    async with session_factory.async_get_session() as session:
        select_phones = await session.execute(
            Select(Phone.ip_address).filter(or_(*filters))
        )
    return select_phones.scalars().all()


async def get_phone_after_complete(
    phones: list[str],
) -> dict[str, list[str] | int] | None:
    """
    Get results from DB
    :param phones: get initial phones list for this session
    :return:  dict with SUCCESS and ERROR phones list
    """

    result_dict = {
        "Success": await _get_phones(
            Select(Phone.ip_address).filter(
                and_(Phone.status == "SUCCESS", Phone.ip_address.in_(phones))
            ),
        ),
        "Error": await _get_phones(
            Select(Phone.ip_address).filter(
                and_(Phone.status != "SUCCESS", Phone.ip_address.in_(phones))
            ),
        ),
    }
    result_dict["Devices"] = len(result_dict["Success"] + result_dict["Error"])
    return result_dict


async def _get_phones(select_query: Select[tuple[Any, ...]]) -> list[str]:
    """
    Run select query
    :param select_query - query statement
    """
    async with session_factory.async_get_session() as session:
        stmt = await session.execute(select_query)
    return stmt.scalars().all()


async def create_async_client_session(phones: list[str], keynavi_config: list[str]):
    """
    Create async ClientSession and run send keypress
    :param phones: list of phones
    :param keynavi_config: list of key navigation for loaded phones
    """
    print("Passed phones: ", phones)
    client = Client()
    for number, chunk in enumerate(chunked(phones, settings.CHUNK_SIZE), start=1):
        pending = [
            asyncio.create_task(
                client.send_keypress(ip, keynavi_config), name=f"Task-{ip}"
            )
            for ip in chunk
        ]
        print(f"Chunk: {number}, contains ip address: {chunk}")
        with pb.ProgressBar(
            max_value=len(chunk), term_width=120, max_error=False
        ) as bar:
            complete = 0
            while pending:  # continue while we have pending tasks
                done, pending = await asyncio.wait(
                    pending, return_when=asyncio.FIRST_COMPLETED
                )
                complete += len(done)
                bar.update(complete)
                for task in done:
                    bg_task = asyncio.create_task(tasks_action(task))
                    background_tasks.add(bg_task)  # noqa: E501, keep reference for 'fire-and-forget' background tasks
                    bg_task.add_done_callback(background_tasks.remove)


async def tasks_action(task: Task) -> None:
    """
    Get complete task and run according DB query
    :param task:  Task
    """
    ip_addr = task.get_name().removeprefix("Task-")  # noqa: E501, substring ip address from task name
    if task.exception() is None:
        task_result: dict = task.result()
        await update_phones(
            ip=ip_addr,
            status=StatusEnum.SUCCESS
            if (task_result.get("response") <= 400)
            else StatusEnum.ERROR,
            error=f"Response {task_result.get('response')}",
        )
    else:  # noqa: E501, If task complete with exception we mark this result as ERROR and write ERROR message in DB
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
        update_query = await session.execute(
            Update(Phone)
            .filter(Phone.ip_address == ip)
            .values(status=status, updated=datetime.datetime.now(), error=error),
        )
    return update_query.rowcount


async def clear_table() -> int:
    """
    Clear phone table
    """
    async with session_factory.async_get_session() as session, session.begin():
        delete_query = await session.execute(Delete(Phone))
    return delete_query.rowcount
