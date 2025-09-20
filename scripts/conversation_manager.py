# scripts/conversation_manager.py

class ConversationManager:
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.history = []  # list of {"role":..., "content":...}
        self.last_user_query = None
        self.last_bot_response = None

    def add_user_message(self, user_text):
        self.history.append({"role": "user", "content": user_text})

    def add_assistant_message(self, assistant_text):
        self.history.append({"role": "assistant", "content": assistant_text})

    def get_messages(self):
        return [{"role": "system", "content": self.system_prompt}] + self.history

    def reset(self):
        self.history = []

    def get_last_n_messages(self, n=10):
        return [{"role": "system", "content": self.system_prompt}] + self.history[-n:]

    def update(self, user, assistant):
        self.last_user_query = user
        self.last_bot_response = assistant
        self.history.append({"role": "user", "content": user})
        self.history.append({"role": "assistant", "content": assistant})

    def get_last_response(self):
        return self.last_bot_response
