from unittest.mock import Mock, patch
from uuid import UUID

import pytest

from hive.common import utc_now
from hive.common.units import MILLISECOND

from hive.llm_chatbot.responder import Service
from hive.llm_chatbot.responder.runnables import tokens_to_sentences
from hive.llm_chatbot.responder.schema import Message, Request


def test_default_stream_consumer_group() -> None:
    service = Service(db=None)
    assert service.consumer == "hive-llm-chatbot"
    assert service.consumer_group == "responder-service"


@patch("hive.llm_chatbot.responder.Service._generate_response")
def test_generate_response(_: Mock) -> None:
    timestamp = utc_now() - 15 * MILLISECOND

    service = Service(
        db=Mock(
            zrevrangebyscore=Mock(return_value=["615"]),
            hgetall=Mock(return_value={
                "id": "fd1b8ee8-bc84-44e7-b5c4-1274c68349ec",
                "time": timestamp,
                "role": "user",
                "content.text": "what are overchoppers?",
            }),
        ),
    )
    service.on_request(Request.model_validate({
        "id": "1758756783269-0",
        "action": "generate_response",
        "context_id": "f5379245-11b3-48bb-ab88-5df9bb781fd0",
        "message_id": "fd1b8ee8-bc84-44e7-b5c4-1274c68349ec",
        "time": timestamp,
    }))
    service._generate_response.assert_called_once_with(
        UUID("f5379245-11b3-48bb-ab88-5df9bb781fd0"),
        Message.model_validate({
            "id": "fd1b8ee8-bc84-44e7-b5c4-1274c68349ec",
            "time": timestamp,
            "role": "user",
            "content.text": "what are overchoppers?",
        }),
    )


@pytest.mark.parametrize(
    "input,expect_output", (
        (("Over|chop|pers|.| A| term| used| to| describe| individuals| who| h"
          "ave| been| unfairly| accused| of| crimes| for| which| they| had| n"
          "o| prior| conviction| or| connection| to| the| alleged| offense|.|"
          " Over|chop|pers| often| face| challenges| in| proving| their| inno"
          "cence|,| and| can| find| themselves| on| trial| with| a| clear| cl"
          'aim| against| them|.|\n|\n|The| name| "|over|chop|per|"| is| deriv'
          "ed| from| the| fact| that| over|cons|umers| are| more| likely| to|"
          " be| found| guilty| of| crimes| for| which| they| had| no| prior| "
          "conviction| or| connection| to| the| alleged| offense|.| This| phe"
          "nomenon| arises| because| individuals| who| have| committed| crime"
          "s| before| often| share| common| characteristics|,| such| as| havi"
          "ng| a| history| of| public| behavior|,| violence|,| or| other| beh"
          "aviors| associated| with| their| previous| offenses|.|\n|\n|For| e"
          "xample|,| someone| accused| of| a| violent| crime| might| be| foun"
          "d| guilty| on| charges| related| to| petty| theft|,| while| anothe"
          "r| person| charged| with| a| minor| offense| might| be| convicted|"
          " on| the| charge| of| murder|.| However|,| this| doesn|'t| mean| "
          "that| the| defendant| is| innocent|;| it| means| they| have| been|"
          " unfairly| and| repeatedly| placed| in| an| uncomfortable| positio"
          "n| due| to| their| collective| actions| or| public| behavior| prio"
          "r| to| becoming| accused|.|\n|\n|The| legal| system| has| attempte"
          "d| to| address| over|chop|pers| through| various| mechanisms|,| inc"
          "luding| community|-|based| corrections| programs|,| education| init"
          "iatives|,| and| law| enforcement| efforts| aimed| at| bringing| vi"
          "ctims| back| into| the| justice| system| after| being| falsely| ac"
          "cused| of| a| crime| that| was| never| committed|.| Despite| these"
          "| measures|,| many| individuals| who| have| been| unfairly| charge"
          "d| or| convicted| remain| on| trial| with| no| clear| resolution|,"
          "| highlighting| the| need| for| more| nuanced| approaches| to| ens"
          "uring| fair| and| just| outcomes| in| cases| involving| public| be"
          "havior|.|"
          ),
         ["Overchoppers. ",
          ("A term used to describe individuals who have been"
           " unfairly accused of crimes for which they had no prior convict"
           "ion or connection to the alleged offense. "
           ),
          ("Overchoppers often face challenges in proving their innocence, "
           "and can find themselves on trial with a clear claim against them."
           "\n\n"
           ),
          ('The name "overchopper" is derived from the fact that overconsum'
           "ers are more likely to be found guilty of crimes for which they"
           " had no prior conviction or connection to the alleged offense. "
           ),
          ("This phenomenon arises because individuals who have committed c"
           "rimes before often share common characteristics, such as having"
           " a history of public behavior, violence, or other behaviors ass"
           "ociated with their previous offenses.\n\n"
           ),
          ("For example, someone accused of a violent crime might be found "
           "guilty on charges related to petty theft, while another person "
           "charged with a minor offense might be convicted on the charge o"
           "f murder. "),
          ("However, this doesn't mean that the defendant is inno"
           "cent; it means they have been unfairly and repeatedly placed in"
           " an uncomfortable position due to their collective actions or p"
           "ublic behavior prior to becoming accused.\n\n"
           ),
          ("The legal system has attempted to address overchoppers through "
           "various mechanisms, including community-based corrections progr"
           "ams, education initiatives, and law enforcement efforts aimed a"
           "t bringing victims back into the justice system after being fal"
           "sely accused of a crime that was never committed. "
           ),
          ("Despite these measures, many individuals who have been unfairl"
           "y charged or convicted remain on trial with no clear resolution"
           ", highlighting the need for more nuanced approaches to ensuring"
           " fair and just outcomes in cases involving public behavior."
           ),
          ]),
        # Don't split the trailing double quote.
        (("I|'m| an| artificial| intelligence| model| known| as| L|lama|."
          '| L|lama| stands| for| "|Large| Language| Model| Meta| AI|."|'
          ),
         ["I'm an artificial intelligence model known as Llama. ",
          'Llama stands for "Large Language Model Meta AI."',
          ]),
        # Split even if everything comes as one "token" (i.e. the
        # wrapping RunnableGenerator was invoked, not streamed).
        (("I'm an artificial intelligence model known as Llama. "
          'Llama stands for "Large Language Model Meta AI."'
          ),
         ["I'm an artificial intelligence model known as Llama. ",
          'Llama stands for "Large Language Model Meta AI."',
          ]),
    ))
def test_tokens_to_sentences(input: str, expect_output: list[str]) -> None:
    tokens = input.split("|")
    assert "".join(tokens) == "".join(expect_output)  # sanity
    assert list(tokens_to_sentences(iter(tokens))) == expect_output
