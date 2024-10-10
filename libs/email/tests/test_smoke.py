import os

import pytest

from hive.email import load_email


def serialized_email_filenames():
    for dirpath, dirnames, filenames in os.walk(os.path.dirname(__file__)):
        for filepath in sorted(
                os.path.join(dirpath, filename)
                for filename in filenames
                if filename.endswith(".eml")):
            yield filepath


@pytest.mark.parametrize("filename", serialized_email_filenames())
def test_load_from_named_file(filename):
    msg = load_email(filename)
    _ = msg.message_id
    _ = msg.delivered_to
    _ = msg.summary_headers

    assert msg.content_type in {
        "text/plain",
        "text/html",
        "multipart/mixed",
        "multipart/alternative",
        "multipart/related",
        "multipart/signed",
        "multipart/report",
    }

    text_body = msg.plain_body
    text_content = msg.plain_content
    got_text_content = bool(text_content)

    html_body = msg.html_body
    html_content = msg.html_content
    got_html_content = bool(html_content)

    print(f"text_body: {text_body!r}")
    print(f"got_text_content: {got_text_content}")
    print(f"msg.content_type: {msg.content_type}")
    assert (not text_body
            or got_text_content
            or msg.content_type != "text/plain"
            or msg["To"].endswith("+subscribe@googlegroups.com")
            or "X-List-Administrivia" in msg)

    # Non-multipart text/plain
    if text_body is msg:
        assert msg.content_type == "text/plain"
        assert (got_text_content
                or filename.endswith("/empty.eml")
                or msg["To"].endswith("+subscribe@googlegroups.com")
                or "X-List-Administrivia" in msg)
        assert len(msg.pdf_attachments) == 0
        return
    assert msg.content_type != "text/plain"
    assert html_body or text_body

    for att in msg.pdf_attachments:
        assert att.filename is not None
        assert (att.filename.lower().endswith(".pdf")
                or att.filename == "End of Contract's Terms and Conditions")
        pdf = att.pdf_content
        assert pdf.startswith(b"%PDF-1.") or pdf.find(b"%PDF-1.") == 27

    if not (got_text_content and got_html_content):
        return

    # XXX compare (make sure none have placeholder text content
    # XXX that we should replace with something generated from
    # XXX the HTML)
