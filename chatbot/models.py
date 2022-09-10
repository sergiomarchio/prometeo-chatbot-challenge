from . import settings


class API:
    @staticmethod
    def guest_key():
        return getattr(settings, "API_KEY")


class MessageHistory:
    messages = []

    def add_user_message(self, message):
        self.messages.append({"user": message})

    def add_bot_message(self, message):
        self.messages.append({"bot": message})
