import os
from urllib.parse import urlparse

ORIGIN = "https://example.com"


def parse_url(path):
    o = urlparse(path)
    print(ORIGIN + os.path.normpath(o.path) + "?" + o.query)


def main():
    parse_url("https://example.com/../hoge")


if __name__ == "__main__":
    main()
