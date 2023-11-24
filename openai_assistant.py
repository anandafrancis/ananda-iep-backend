from openai import OpenAI
from json import loads
from time import sleep
from re import sub


class IEPAssistant:

    def __init__(self, api_key: str, language: str) -> None:
        self.api_key = api_key
        client = OpenAI(api_key = self.api_key)
        self.client = client
        self.language = language

    def upload_file(self, file_path: str) -> None:
        self.file = self.client.files.create(
            file=open(file_path, "rb"),
            purpose='assistants'
        )

    def _create_assistant(self) -> None:
        self.assistant = self.client.beta.assistants.create(
                      name="AI-EP",
                      description="You efficiently extract information from files and present"+
                                "a response to users that is concise, specific and sufficient.",
                      model="gpt-4-1106-preview",
                      tools=[{"type": "retrieval"}],
                      file_ids=[self.file.id]
                    )
        
    def create_message(self, message: str) -> str:

        self._create_assistant()
        
        self.thread = self.client.beta.threads.create(messages=[{"role": "user", 
                                                                 "content": message,
                                                                 "file_ids": [self.file.id]}])

        run = self.client.beta.threads.runs.create(thread_id=self.thread.id, assistant_id=self.assistant.id,
                                              instructions='Make your final output as concise as possible while'+
                                                           f'being specific and suffient. All responses must be in {self.language}')
        
        status = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)
    
        while status.completed_at is None:
            sleep(1)
            status = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id, run_id=run.id)

        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        messages_data = loads(messages.model_dump_json())
        latest_response = messages_data['data'][0]['content'][0]['text']['value']
    
        return sub(r'\【.*?\】', '', latest_response)