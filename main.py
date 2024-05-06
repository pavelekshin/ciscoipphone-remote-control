import asyncio
import time

import service


async def run():
    try:
        clear = input("\nClear destination phones table before insert?\nPress [Y] or any: ")
        if clear.lower() == "y":
            await service.clear_table()
    except ValueError:
        print("Ooops, wrong choice!")
        exit()

    cnt = 0
    for phone in service.read_phones("phones.csv"):
        cnt += await service.insert_phones(phone)

    print()
    print(f"Phones inserted: {cnt}\n")

    config_dict = service.load_yaml_config("templates/keypress_templates.yaml")

    for indx, template in enumerate(list(config_dict.keys()), start=1):
        print(f"{indx}. {template}")

    try:
        template_id = int(input("\nChoice template: "))
        template = list(config_dict.keys())[template_id - 1]
    except ValueError:
        print("Ooops, wrong choice!")
        exit()

    print("Starting with " + template)

    command = config_dict[template]
    keynavi_config = service.create_template(command)

    start = time.time()
    phones = await service.get_phones()  # get all new and not successful phone result
    await service.create_async_client_session(phones, keynavi_config)
    end = time.time()
    total = end - start

    print(f"=" * 80)
    print(f"Template {template} action on {len(phones)} phones is completed! Runtime {total:.4f} sec")
    print(f"Results: {await service.get_phone_after_complete(phones)}")
    print(f"Check phones table on database for more information!")


if __name__ == "__main__":
    try:
        asyncio.run(run(), debug=False)
    except KeyboardInterrupt:
        print("\nProgram is canceled by user")
