import os

import pytest

from hive.email import load_email


def load_test_email(filename):
    testdir = os.path.dirname(__file__)
    return load_email(os.path.join(testdir, "resources", filename))


@pytest.mark.parametrize(
    "filename,expected_value",
    (("bad-message-id.eml", "gary@gbenson.net"),
     ("empty.eml", None),
     ))
def test_delivered_to(filename, expected_value):
    msg = load_test_email(filename)
    assert msg.delivered_to == expected_value


@pytest.mark.parametrize(
    "filename,expected_value",
    (("bad-message-id.eml",
      "<[b3ba1083d5b440b8b44217eaa0b28327-JFBVALKQOJXWILKNK4YVA7CDIR"
      "XECRLNMFUWYUDMMF2GM33SNV6EGRDOIF6EK6DPKNWXI4A=@microsoft.com]>",
      ),
     ("empty.eml", None),
     ("text-plain.eml",
      "<1323103880.2113116.1706840737638@outbound.mail.linode.com>"),
     ))
def test_message_id(filename, expected_value):
    msg = load_test_email(filename)
    assert msg.message_id == expected_value


@pytest.mark.parametrize(
    "filename,expected_value",
    (("bad-message-id.eml", "multipart/alternative"),
     ("empty.eml", "text/plain"),
     ("text-plain.eml", "text/plain"),
     ))
def test_content_type(filename, expected_value):
    msg = load_test_email(filename)
    assert msg.content_type == expected_value


def test_empty_body():
    msg = load_test_email("empty.eml")
    assert msg.summary == {}
    assert msg.plain_body is msg
    assert msg.plain_content == ""
    assert msg.html_body is None
    assert msg.html_content is None
    assert len(msg.pdf_attachments) == 0


def test_plain_body():
    msg = load_test_email("text-plain.eml")
    assert msg.summary_headers == {
        "date": "Thu, 01 Feb 2024 21:25:37 -0500",
        "from": "billing@linode.com",
        "to": "linode@gbenson.net",
        "subject": "Linode.com: Payment Receipt [16911140]",
        "message_id":
        "<1323103880.2113116.1706840737638@outbound.mail.linode.com>",
        "delivered_to": "linode@gbenson.net",
    }
    assert msg.plain_body is msg
    text = msg.plain_content
    assert text.startswith("Company Name:\nPayment Number: 16911140\nP")
    assert text.endswith('inode*Akamai" with your bank or credit card.')
    assert msg.html_body is None
    assert msg.html_content is None
    assert len(msg.pdf_attachments) == 0


def test_html_body():
    msg = load_test_email("bad-message-id.eml")
    assert msg.summary_headers == {
        "date": "Tue, 05 Sep 2023 12:32:26 -0700",
        "from": "Microsoft <msa@communication.microsoft.com>",
        "to": "gary@gbenson.net",
        "subject": "Updates to our terms of use",
        "message_id":
        "<[b3ba1083d5b440b8b44217eaa0b28327-JFBVALKQOJXWILKNK4YVA7CDIRX"
        "ECRLNMFUWYUDMMF2GM33SNV6EGRDOIF6EK6DPKNWXI4A=@microsoft.com]>",
        "delivered_to": "gary@gbenson.net",
    }
    assert msg.plain_body is not msg
    text = msg.plain_content
    assert text.startswith("*Your Services Agreement made clearer*\n\n")
    assert text.endswith("rosoft.com/fwlink/?LinkId=271181&clcid=0x809")
    assert msg.html_body is not msg
    html = msg.html_content
    assert html.startswith('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1')
    assert html.endswith("</html><!-- cV: cL1/AI4T/EeEQSjv.4.1.1.2 -->")
    assert len(msg.pdf_attachments) == 0


def test_empty_html_body():
    msg = load_test_email("empty-html.eml")
    assert msg.summary_headers == {}
    assert msg.summary == {"body": "Hello!"}
    assert msg.plain_body is not msg
    assert msg.plain_content == "Hello!"
    assert msg.html_body is not None
    assert msg.html_body is not msg
    assert msg.html_content is None
    assert len(msg.pdf_attachments) == 0


def test_related_html_body():
    msg = load_test_email("multipart-related.eml")
    assert msg.summary_headers == {
        "date": "Sun, 09 Jan 2022 07:05:11 -0700",
        "from": "NHS Test and Trace <noreply@email"
        ".survey.test-and-trace.nhs.uk>",
        "to": "Gary Benson <gary@gbenson.net>",
        "subject": "Your feedback on the contact tracing service",
        "message_id":
        "<1585960195.2533579.1641737111760@jwm10-app.fra1.qprod.net>",
        "delivered_to": "gary@gbenson.net",
    }
    assert msg.plain_body is not msg
    text = msg.plain_content
    assert text.startswith("Dear Gary,\n\nYou are receiving this invit")
    assert text.endswith("EMD_EkF2lgzg86vCHvQ&BT=dGVzdGFuZHRyYWNl&_=1>")
    assert msg.html_body is not msg
    html = msg.html_content
    assert html.startswith('<html><head></head><body><p dir="ltr">Dear')
    assert html.endswith('gm&amp;SV=SV_8cbxz9vj1RlHiYu"></body></html>')
    assert len(msg.pdf_attachments) == 0


def test_generated_plain_body():
    msg = load_test_email("text-html.eml")
    assert msg.summary_headers == {
        "date": "Sat, 03 Feb 2024 20:33:04 +0000",
        "from": "Samsung account <sa.noreply@samsung-mail.com>",
        "to": "Mark Zuckerberg <zuck@gbenson.net>",
        "subject": "Welcome to Samsung services.",
        "message_id":
        "<801490728.5311067.1706992384281@messagegw-98bbd4b84-hb5c9>",
        "delivered_to": "zuck@gbenson.net",
    }
    assert msg.plain_body is None
    text = msg.plain_content
    assert text.startswith("![Samsung Account](https://account.samsung")
    assert text.endswith("ht © 1995-2024 Samsung. All Rights Reserved.")
    html = msg.html_content
    assert html.startswith("<!doctype html>\n<html>\n<head>\n  <meta c")
    assert html.endswith("</div>\n  </div>\n</div>\n\n</body>\n</html>")
    assert len(msg.pdf_attachments) == 0


def test_just_a_pdf():
    msg = load_test_email("just-a-pdf.eml")
    assert msg.summary == {
        "date": "Sat, 08 Jun 2024 21:16:39 +0100",
        "from": "Gary Benson <gary@gbenson.net>",
        "to": "Bill Gates <bill_gates@live.co.uk>",
        "subject": "Finger print thing ",
        "message_id": "<1574AA31-0687-463F-9FFF-87CC74411763@gbenson.net>",
    }
    assert msg.plain_body is not msg
    assert msg.plain_content == ""
    assert msg.html_body is None
    assert msg.html_content is None
    assert len(msg.pdf_attachments) == 1
    atta = msg.pdf_attachments[0]
    assert atta.content_type == "application/pdf"
    assert atta.filename == "Biometrics_Guidance_July_2022.pdf"
    pdf = atta.pdf_content
    assert len(pdf) == 253385
    assert pdf.startswith(b"%PDF-1.6\r")
    assert pdf.endswith(b"\r\n%%EOF\r\n")
