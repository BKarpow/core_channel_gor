from requests import get


def is_network() -> bool:
    try:
        r = get('http://localhost:8181/is')
        if r.status_code == 200:
            return r.json()['isNetwork']
        return False
    except:
        return False