from .inbox import InboxProcessor
from .processor import Processor
from .readlist import ReadingListProcessor

DEFAULT_PROCESSORS = {
    "inboxes": InboxProcessor,
    "reading_lists": ReadingListProcessor,
}
