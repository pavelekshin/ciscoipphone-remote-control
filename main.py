import asyncio
import time

import service

if __name__ == "__main__":
    cnt = 0
    for phone in service.read_phones("phones.csv"):
        cnt += service.insert_phones(phone)

    print()
    print(f"Phones inserted: {cnt}\n")
    print()

    config_dict = service.load_yaml_config("templates/keypress_templates.yaml")

    for indx, template in enumerate(list(config_dict.keys()), start=1):
        print(f"{indx}. {template}")

    try:
        template_id = int(input("\nChoice template: "))
        template = list(config_dict.keys())[template_id - 1]
    except:
        print("Ooops, wrong choice!")
        exit()

    print("Starting with " + template)
    keynavi_config = service.create_tempalte(config_dict[template])

    start = time.time()
    phones = service.get_phones(100)  # get phones per run
    asyncio.run(service.create_async_client_session(phones, keynavi_config))
    end = time.time()
    total = end - start

    print(f"=" * 80)
    print(f"Template {template} action on {len(phones)} phones is completed! Runtime {total:.4f} sec")
    print(f"Results: {service.get_phone_after_complete(phones)}")
    print(f"Check phones table on database for more information!")
