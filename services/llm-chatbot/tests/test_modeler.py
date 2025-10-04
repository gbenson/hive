from unittest.mock import Mock

from hive.llm_chatbot.modeler import Service


def test_default_stream_consumer_group() -> None:
    service = Service(db=None)
    assert service.consumer == "hive-llm-chatbot"
    assert service.consumer_group == "modeler-service"


def test_insert_message() -> None:
    service = Service(db=Mock(
        get=Mock(return_value=None),
        incr=Mock(return_value=5271),
    ))
    service.on_request("1750185137395-2", {
        "action": "upsert_message",
        "context_id": "f5379245-11b3-48bb-ab88-5df9bb781fd0",
        "message_id": "6d8dc228-073e-45d7-8756-1a553fd81fb1",
        "time": "2025-06-17T18:32:17.395Z",
        "role": "user",
        "content.text": "https://youtu.be/lSoEI8jia3Q",
    })

    service.db.get.assert_called_once_with(
        "msg:6d8dc228-073e-45d7-8756-1a553fd81fb1:msgid",
    )
    service.db.incr.assert_called_once_with("last_msgid")
    service.db.hset.assert_called_once_with(
        "msg:5271",
        mapping={
            "id": "6d8dc228-073e-45d7-8756-1a553fd81fb1",
            "time": "2025-06-17T18:32:17.395Z",
            "role": "user",
            "content.text": "https://youtu.be/lSoEI8jia3Q",
        },
    )
    service.db.set.assert_called_once_with(
        "msg:6d8dc228-073e-45d7-8756-1a553fd81fb1:msgid",
        5271,
    )
    service.db.zadd.assert_called_once_with(
        "ctx:f5379245-11b3-48bb-ab88-5df9bb781fd0:msgs",
        {"5271": 1750185137395.2},
    )


def test_update_message() -> None:
    service = Service(db=Mock(get=Mock(return_value="3846")))
    service.on_request("1750185137395-0", {
        "action": "upsert_message",
        "context_id": "f5379245-11b3-48bb-ab88-5df9bb781fd0",
        "message_id": "6d8dc228-073e-45d7-8756-1a553fd81fb1",
        "time": "2025-06-17T18:32:17.395Z",
        "role": "user",
        "content.text": "https://youtu.be/lSoEI8jia3Q",
    })

    service.db.get.assert_called_once_with(
        "msg:6d8dc228-073e-45d7-8756-1a553fd81fb1:msgid",
    )
    service.db.incr.assert_not_called()
    service.db.hset.assert_called_once_with(
        "msg:3846",
        mapping={
            "id": "6d8dc228-073e-45d7-8756-1a553fd81fb1",
            "time": "2025-06-17T18:32:17.395Z",
            "role": "user",
            "content.text": "https://youtu.be/lSoEI8jia3Q",
        },
    )
    service.db.set.assert_not_called()
    service.db.zadd.assert_not_called()


def test_update_with_set_model() -> None:
    service = Service(db=Mock(get=Mock(return_value="3846")))
    service.on_request("1750185137395-0", {
        "action": "upsert_message",
        "context_id": "f5379245-11b3-48bb-ab88-5df9bb781fd0",
        "message_id": "6d8dc228-073e-45d7-8756-1a553fd81fb1",
        "time": "2025-06-17T18:32:17.395Z",
        "role": "user",
        "content.use_model_command": "ollama:gemma3:270m",
    })

    service.db.get.assert_called_once_with(
        "msg:6d8dc228-073e-45d7-8756-1a553fd81fb1:msgid",
    )
    service.db.incr.assert_not_called()
    service.db.hset.assert_called_once_with(
        "msg:3846",
        mapping={
            "id": "6d8dc228-073e-45d7-8756-1a553fd81fb1",
            "time": "2025-06-17T18:32:17.395Z",
            "role": "user",
            "content.use_model_command": "ollama:gemma3:270m",
        },
    )
    service.db.set.assert_called_once_with(
        "ctx:f5379245-11b3-48bb-ab88-5df9bb781fd0:model",
        "ollama:gemma3:270m",
    )
    service.db.zadd.assert_not_called()
