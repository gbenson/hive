from hive.reading_list_updater.entry import ReadingListEntry


def test_bad_input():
    entry = ReadingListEntry.from_email_summary({
        "date": "Tue, 03 Dec 2024 20:03:21 +0000",
        "subject": "Cryptographic Storage - OWASP Cheat Sheet Series",
        "body": "<https://cheatsheetseries.owasp.org/cheatsheets/Crypto"
        "graphic_Storage_Cheat_Sheet.html#defence-in-depth\n\nDefence i"
        "n Depth\u00b6\nApplications should be designed ... "
        "access control to prevent unauthorised access to information.>",
    })
    assert entry.as_wikitext() == (
        "{{at|Tue, 03 Dec 2024 20:03:21 +0000}} "
        "[https://cheatsheetseries.owasp.org/cheatsheets/Crypto"
        "graphic_Storage_Cheat_Sheet.html#defence-in-depth "
        "Cryptographic Storage - OWASP Cheat Sheet Series] "
        "Defence in Depth\u00b6\nApplications should be designed ... "
        "access control to prevent unauthorised access to information."
    )
