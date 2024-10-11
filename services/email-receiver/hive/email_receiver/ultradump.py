from itertools import count as counter

from imapclient import IMAPClient

from hive.common.units import SECONDS
from hive.config import read_config

from .imap import Client as IMAPConfig


def main(test=False):
    c = IMAPConfig(read_config("email")["email"]["imap"])
    c.timeout = 30 * SECONDS
    with IMAPClient(host=c.host, port=c.port, timeout=c.timeout) as imap:
        imap.login(c.user, c.password)
        index = counter()
        for flags, delimiter, name in imap.list_folders():
            select_info = imap.select_folder(name)
            count = select_info[b"EXISTS"]
            print(f"{count:>8} {name}")
            if not count:
                continue
            if test and count > 1:
                continue
            for data in imap.fetch("1:*", ["RFC822"]).values():
                filename = f"UNSORTED-RAW-EMAILS/{next(index):04d}.eml"
                with open(filename, "wb") as fp:
                    fp.write(data[b"RFC822"])
                print(f"\t\t{filename}")
                if test:
                    return
