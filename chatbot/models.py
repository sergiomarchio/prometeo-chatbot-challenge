from . import settings


class API:
    @staticmethod
    def guest_key():
        return getattr(settings, "API_KEY")



