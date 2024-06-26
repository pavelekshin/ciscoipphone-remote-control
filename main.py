import asyncio
import time

from service import service


async def run():
    """
    Main program
    """
    await input_clear_action()
    await insert_phones()

    config_dict = service.load_yaml_config("templates/keypress_templates.yaml")
    template = input_phone_template(config=config_dict)

    print("Starting with " + template)
    commands = config_dict[template]
    keynavi_config = service.create_template(commands)
    start = time.perf_counter()
    phones = await service.get_phones()  # get all new and not successful phone result
    await service.create_async_client_session(phones, keynavi_config)
    await asyncio.wait(service.background_tasks)
    end = time.perf_counter()
    total = end - start
    print("=" * 80)
    print(
        f"Template {template} action on {len(phones)} phones is completed! Runtime {total:.3f} sec"
    )
    print(f"Results: {await service.get_phone_after_complete(phones)}")
    print("Check phones table on database for more information!")


async def input_clear_action():
    """
    Choice phone table clear action
    """
    cnt: int = 0
    try:
        clear = input(
            "\nClear destination phones table before insert?\nPress [Y] or any: "
        )
    except ValueError:
        print("Oops, wrong choice!")
    else:
        if clear.lower() == "y":
            cnt = await service.clear_table()
    print(f"Cleared records : {cnt}\n")


def input_phone_template(*, config: dict[str, list[str]] = None) -> str:
    """
    Choice phone template
    :param config - keypress template (keypress_templates.yaml)
    """
    for indx, template in enumerate(list(config.keys()), start=1):
        print(f"{indx}. {template}")

    try:
        template_id = int(input("\nChoice template: "))
        template = list(config.keys())[template_id - 1]
    except ValueError:
        print("Oops, wrong choice!")
    else:
        return template


async def insert_phones():
    """
    Insert phones into DB phone table
    """
    cnt = 0
    for phone in service.read_phones("phones.csv"):
        cnt += await service.insert_phones(phone)
    print(f"Phones inserted: {cnt}\n")


if __name__ == "__main__":
    try:
        asyncio.run(run(), debug=False)
    except KeyboardInterrupt:
        print("\nProgram is canceled by user")
