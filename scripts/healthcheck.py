'''Check one local HTTP service by port and path.
Usage: python scripts/healthcheck.py <port> [path]
Exit 0 on HTTP 200, exit 1 otherwise. Standard library only.
'''

import sys
import urllib.error
import urllib.request


def main(argv):
    if len(argv) < 2 or len(argv) > 3:
        print('usage: healthcheck.py <port> [path]', file=sys.stderr)
        return 2
    port = argv[1]
    path = argv[2] if len(argv) == 3 else '/health'
    if not path.startswith('/'):
        path = '/' + path
    url = 'http://127.0.0.1:' + port + path
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status == 200:
                print('healthcheck: ok: ' + url)
                return 0
            print('healthcheck: fail: ' + url + ' status ' + str(response.status), file=sys.stderr)
            return 1
    except (urllib.error.URLError, OSError) as exc:
        print('healthcheck: fail: ' + url + ' ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
