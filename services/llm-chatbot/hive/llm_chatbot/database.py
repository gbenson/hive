from .schema import ContextID, Message


class Database:
    def update_context(self, context_id: ContextID, message: Message) -> None:
        raise NotImplementedError(dict(
            context_id=context_id,
            message=message,
        ))
