import yaml


with open('chatbot/api.key', 'r') as f:
    API_KEY = f.read().strip()

with open('chatbot/settings.yml', 'r') as f:
    CONFIG = yaml.safe_load(f)
