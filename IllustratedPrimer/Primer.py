import logging
import os
from datetime import datetime
import requests

from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback

from langchain import PromptTemplate, LLMChain
from homeassistant_api import Client
from langchain.prompts import (
    PromptTemplate,
)


class Primer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        prompt_url = os.getenv("PRIMER_PROMPT_URL") 
        self.prompt_template = self.get_prompt(prompt_url)

        openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        openai_temperature = os.getenv("OPENAI_TEMPERATURE", "0")

        self.chat = ChatOpenAI(model_name=openai_model, temperature=openai_temperature)

    def get_hass_data(self):
        self.logger.debug("let's get some data from hass")
        with Client(
            f'{os.getenv("HASS_URL")}/api/',
            os.getenv("HASS_TOKEN")
        ) as client:

            weather = client.get_entity(entity_id="weather.tomorrow_io_reedazawa_daily")
            state = weather.get_state()
            # print(state.attributes)

        return weather

    def get_prompt(self, url):
        self.logger.debug("let's get a prompt from github")
        # Add cache-breaking query parameter
        cache_breaker = str(int(datetime.now().timestamp()))
        url_with_cache_breaker = f"{url}?cb={cache_breaker}"
        
        # Make the request
        r = requests.get(url_with_cache_breaker)
        prompt = r.text
        return prompt

    def generate_response(self, current_state):
        self.logger.debug("let's make a request to openai")

        weather = self.get_hass_data()
        time = datetime.now().time()
        with get_openai_callback() as cb:
            prompt = PromptTemplate(template=self.prompt_template, input_variables=["weather", "time"])
            # get a chat completion from the formatted messages
            chain = LLMChain(llm=self.chat, prompt=prompt)
            result = chain.run(weather=weather, time=time)
            self.logger.debug(f"OpenAI Response: {result}")
            self.logger.info(f"Total Tokens: {cb.total_tokens}")
            self.logger.info(f"Prompt Tokens: {cb.prompt_tokens}")
            self.logger.info(f"Completion Tokens: {cb.completion_tokens}")
            self.logger.info(f"Total Cost (USD): ${cb.total_cost}")

        self.logger.debug(f"OpenAI Response: {result}")
    
        
        return result
