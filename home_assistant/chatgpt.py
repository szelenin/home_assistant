import os
import openai
from datetime import datetime, timedelta
import json
import sys

# Add src directory to Python path for logger import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils.logger import setup_logging

class ChatGPT:
    def __init__(self):
        self.messages = []
        self.model_name = "gpt-3.5-turbo"
        self.api_token = None
        self.customizations = {}
        self.log_path = "./messages.msg"
        self.client = None
        self.logger = setup_logging("home_assistant.chatgpt")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            open(self.log_path, 'w').close()

    def model(self, model_name):
        self.model_name = model_name

    def token(self, token):
        self.api_token = token
        self.client = openai.OpenAI(api_key=token)

    def customiseResponse(self, customizations):
        self.customizations = customizations

    def prompt(self, user_prompt):
        if not self.api_token or not self.client:
            raise Exception("API token not set.")
        
        self.messages.append({"role": "user", "content": user_prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.messages,
                **self.customizations
            )
            
            reply = response.choices[0].message.content
            self.messages.append({"role": "assistant", "content": reply})
            
            self._log_message(user_prompt, reply)
            return reply
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {e}")

    def clearMessages(self):
        self.messages = []
        self._clean_old_logs()

    def _log_message(self, user, reply):
        now = datetime.now()
        timestamp = f"[{now.strftime('%Y-%m-%d')}, {now.strftime('%H:%M:%S')}]"
        log_entry = f"{timestamp}\nUser: {user}\nChatGPT: {reply}\n\n"
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def _clean_old_logs(self):
        if not os.path.exists(self.log_path):
            return
        new_lines = []
        cutoff = datetime.now() - timedelta(days=30)
        with open(self.log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            if lines[i].startswith('['):
                date_str = lines[i].split(",")[0][1:]
                try:
                    log_date = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    i += 1
                    continue
                block = lines[i:i+4]
                if log_date >= cutoff:
                    new_lines.extend(block)
                i += 4
            else:
                i += 1

        with open(self.log_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
