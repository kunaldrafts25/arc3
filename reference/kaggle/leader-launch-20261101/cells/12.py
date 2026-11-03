import time

def await_client(printing: bool = False):
    for _ in range(15 * 60):
        time.sleep(1)
        try:
            model_list = client.models.list()
            if printing:
                print(model_list)
        except NameError:
            raise  # maybe you did not run the cell initializing client
        except Exception:
            continue
        break
    else:
        raise

await_client()