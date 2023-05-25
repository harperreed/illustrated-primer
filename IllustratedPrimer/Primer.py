import logging
import os
import json
from datetime import datetime
import requests
import yaml

from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain import PromptTemplate, LLMChain
from langchain.callbacks import get_openai_callback
# from langchain.memory import ChatMessageHistory
from langchain.memory import ConversationBufferMemory

from homeassistant_api import Client

class Primer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        prompt_url = os.getenv("PRIMER_PROMPT_URL") 
        self.prompt_template = self.get_prompt(prompt_url)

        openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        openai_temperature = os.getenv("OPENAI_TEMPERATURE", "0")
        self.logger.debug(f"OpenAI Model: {openai_model}")
        self.logger.debug(f"OpenAI Temperature: {openai_temperature}")

        self.chat = ChatOpenAI(model_name=openai_model, temperature=openai_temperature)
        self.memory = ConversationBufferMemory(memory_key="chat_history")
                      

    def get_prompt(self, url):
        self.logger.debug("let's get a prompt from github")
        # Add cache-breaking query parameter
        cache_breaker = str(int(datetime.now().timestamp()))
        url_with_cache_breaker = f"{url}?cb={cache_breaker}"
        
        # Make the request
        r = requests.get(url_with_cache_breaker)
        prompt = r.text
        return prompt

    def generate_response(self, payload):
        self.logger.debug("let's make a request to openai")

        # convert the json payload to a dict
        json_payload = json.loads(payload)

        with get_openai_callback() as cb:

            prompt = PromptTemplate(
                input_variables=["chat_history", "human_input"], 
                template=self.prompt_template
            )
            
            # # get a chat completion from the formatted messages
            chain = LLMChain(llm=self.chat, prompt=prompt,   verbose=False, memory=self.memory)
            result = chain.predict(human_input=json.dumps(json_payload, separators=(',', ':')))
            # print(dir(self.memory))
            if (len(self.memory.chat_memory.messages)>10):
                self.memory.clear()
            self.logger.debug(f"OpenAI Response: {result}")
            self.logger.info(f"Total Tokens: {cb.total_tokens}")
            self.logger.info(f"Prompt Tokens: {cb.prompt_tokens}")
            self.logger.info(f"Completion Tokens: {cb.completion_tokens}")
            self.logger.info(f"Total Cost (USD): ${cb.total_cost}")


        self.logger.debug(f"OpenAI Response: {result}")
    
        
        return result
