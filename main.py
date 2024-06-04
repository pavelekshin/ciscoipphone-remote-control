import asyncio
import time

from service import service


async def run():
    await input_clear_action()
    await insert_phones()

    config_dict = service.load_yaml_config("templates/keypress_templates.yaml")
    template = input_phone_template(config=config_dict)

    print("Starting with " + template)
    commands = config_dict[template]
    keynavi_config = service.create_template(commands)
    start = time.time()
    phones = await service.get_phones()  # get all new and not successful phone result
    await service.create_async_client_session(phones, keynavi_config)
    end = time.time()
    total = end - start
    print("=" * 80)
    print(
        f"Template {template} action on {len(phones)} phones is completed! Runtime {total:.4f} sec"
    )
    print(f"Results: {await service.get_phone_after_complete(phones)}")
    print("Check phones table on database for more information!")


async def input_clear_action():
    cnt: int = 0
    try:
        clear = input(
            "\nClear destination phones table before insert?\nPress [Y] or any: "
        )
        if clear.lower() == "y":
            cnt = await service.clear_table()
    except ValueError:
        print("Oops, wrong choice!")
    else:
        print(f"Cleared records : {cnt}\n")


def input_phone_template(*, config: dict[str, list[str]] = None) -> str:
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
    cnt = 0
    for phone in service.read_phones("phones.csv"):
        cnt += await service.insert_phones(phone)
    print(f"Phones inserted: {cnt}\n")


if __name__ == "__main__":
    try:
        asyncio.run(run(), debug=False)
    except KeyboardInterrupt:
        print("\nProgram is canceled by user")
