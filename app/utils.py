import requests


def check_spelling(text: str) -> str:
    response = requests.get(
        "https://speller.yandex.net/services/spellservice.json/checkText",
        params={"text": text}
    )
    result = response.json()
    for error in result:
        if len(error['s']) > 0:
            text = text.replace(error['word'], error['s'][0])
    return text
