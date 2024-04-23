from textwrap import dedent
from langchain_openai import ChatOpenAI
import openai
import requests
import streamlit as st
from dotenv import load_dotenv
from crewai import Task,Agent
from crewai import Crew

from langchain.agents import tool



class TeamATasks():
    def retriever_task(self, agent,public_id,context):
        return Task(
			description=dedent(f"""\
				Just use the tool to perform the action based on given public_id.
                
                public_id: {public_id}
                context: {context}

				"""),
			expected_output=dedent("""\
				A detailed report about the profile """),
			agent=agent
		)

    

    # def zappier_task(self,agent):
    #     return Task(
	# 		description=dedent(f"""\
	# 			use the information from retriever_task and then use that information to execute this task.
	# 			"""),
	# 		expected_output=dedent("""\
	# 			"""),
	# 		agent=agent
	# 	)
    


    def writing_task(self,agent,context):
        return Task(
			description=dedent(f"""\
				use the information from retriever_task and then use that information to generate the message.
                      
                 context: {context}     
				"""),
			expected_output=dedent("""\
			    """),
			agent=agent
		)



    
    def send_task(self,agent,context):
        return Task(
			description=dedent(f"""\
				use the `provider_id` from retriever_task and then pass the provider_id as a paramtere to  `send_message` tool or `send_invitaion` tool.
                based on the context given by the user.

                 context: {context}     
				"""),
			expected_output=dedent("""\
				"""),
			agent=agent
		)


llm = ChatOpenAI(
    openai_api_base="https://api.openai.com/v1",
    openai_api_key="openai_api_key",
    model_name="gpt-3.5-turbo-0125",
)

class TeamAAgents():

 
    openai.api_key = "openai_api_key",



    def retriever_agent(self):
        return Agent(
            llm=llm,
            role='Retrieve a profile',
            goal='use the given tool accurately to fetch the data.',
            tools=[ToolSet.retrieve_a_profile],
            backstory="As a retriever agent, your mission is to uncover detailed information about the individual. Your insights will lay the ground work for writing_task.",
            verbose=True,
        )
    # def zap_agent(self):
    #     return Agent(
    #         llm=llm,
    #         role='Zappier Sender',
    #         goal='use the output of retriever task and make sure to send data to zappier platform for connecting it to CRM',
    #         tools=[ToolSet.zappier_sending],
    #         backstory="You are expert in sending the information to zappier",
    #         verbose=True,
    #     )
    def writer_agent(self):
        return Agent(
            llm=llm,
            role='Message Writer',
            goal='You have to write a personalized message based on the information from retriever_task',
            tools=[ToolSet.generate_message],
            backstory="As a Message writer, you are expert on writing comprehensive messages based on the information from retriever_task.",
            verbose=True,
        )
    def sender_agent(self):
        return Agent(
            llm=llm,
            role='Message Sender',
            goal='You have to use the provider_id and message from previous tasks to execute the  `send_message` or `send_invitaion` tool based on the given context',
            tools=[ToolSet.send_message,ToolSet.send_invitation],
            backstory="As a sender_agent, your mission is to send invitation or to send message",
            verbose=True,
        )
    

class ToolSet():
 @tool
 def retrieve_a_profile(public_id):
    """
    Retrieves data using public_id.
    """
    url = f"https://api4.unipile.com:13447/api/v1/users/{public_id}?linkedin_sections=%2A&notify=true&account_id=DvSEv59mQBWTDsjAm2M4JQ"
    headers = {
        "accept": "application/json",
        "X-API-KEY": "09n33roP.npYJeRclftCfEO5IKFl0JsV6UGe+OfteR+soYgSZ2Ag="
    }
    response = requests.get(url, headers=headers)
    data = response.json()
    headline = data['headline']
    first_name = data['first_name']
    last_name = data['last_name']
    provider_id = data['provider_id']
    return first_name,last_name, headline , provider_id 
 
 @tool
 def zappier_sending(provider_id,headline,first_name,last_name:str):
     """
    use the parameters from `retrieve_a_profile` and send it to zappier.

     """
     # Your Zapier webhook URL
     webhook_url = 'https://hooks.zapier.com/hooks/catch/15230633/3nbebxi/'

     # The data you want to send, adjust the keys and values according to your needs
     data = {
        'id': provider_id,
        'first_name': first_name,
        'last_name': last_name,
        'headline': headline,
        # 'email': email
         }

    # Make a POST request to the webhook URL with your data
     response = requests.post(webhook_url, json=data)

    # Check the response (optional)
     if response.status_code == 200:
      print('Data sent successfully!')
     else:
      print('Failed to send data:', response.text)
     return response 
 

 @tool
 def generate_message(headline,first_name,last_name):
     """
    use the parameters from `retrieve_a_profile` and generate a message.
     """

     prompt = f"Generates a personalized message based on the these: {headline,first_name,last_name}"
     response = openai.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
     message = response.choices[0].message.content.strip()
     return message
 

 @tool
 def send_invitation(message,provider_id: str):
     """
     use the information from `retrieve_a_profile` and `generate_message`  as parameters to send the invitation.
    """

     url = "https://api4.unipile.com:13447/api/v1/users/invite"

     payload = {
    "provider_id": provider_id,
    "account_id": "DvSEv59mQBWTDsjAm2M4JQ",
    "message": message
     }
     headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "X-API-KEY": "09n33roP.npYJeRclftCfEO5IKFl0JsV6UGe+OfteR+soYgSZ2Ag="
     }

     response = requests.post(url, json=payload, headers=headers)
     if response.status_code == 200:
      print('Data sent successfully!')
     else:
      print('Failed to send data:', response.text)
     
     return response


 @tool
 def send_message(message,provider_id: str):
     """
     use the information from `retrieve_a_profile` and `generate_message`  as parameters to send the message.
    """

     url = f"https://api4.unipile.com:13447/api/v1/chats"
     payload = f"-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"attendees_ids\"\r\n\r\n{provider_id}\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"account_id\"\r\n\r\nDvSEv59mQBWTDsjAm2M4JQ\r\n-----011000010111000001101001\r\nContent-Disposition: form-data; name=\"text\"\r\n\r\{message}\r\n-----011000010111000001101001--\r\n\r\n",     
     headers = {
        "accept": "application/json",
        "content-type": "multipart/form-data; boundary=---011000010111000001101001",
        "X-API-KEY": "09n33roP.npYJeRclftCfEO5IKFl0JsV6UGe+OfteR+soYgSZ2Ag="
     }
     response = requests.post(url, data=payload, headers=headers)
     if response.status_code == 200:
      print('Data sent successfully!')
     else:
      print('Failed to send data:', response.text)
     
     return response
 

 def tools():
   return [
     ToolSet.retrieve_a_profile,
     ToolSet.zappier_sending,
     ToolSet.generate_message,
     ToolSet.send_message,
   ]    



load_dotenv()

public_id = st.text_input("Enter a public_id: ")
context_prompt = st.text_input("Enter the prompt to direct agent to draft the message: ")
tasks = TeamATasks()
agents = TeamAAgents()

retriever_agent = agents.retriever_agent()
# zap_agent = agents.zap_agent()
writer_agent = agents.writer_agent()
sender_agent = agents.sender_agent()

retriever_task = tasks.retriever_task(retriever_agent, public_id,context_prompt)
# zappier_task = tasks.zappier_task(zap_agent)
writing_task = tasks.writing_task(writer_agent,context_prompt)
send_task = tasks.send_task(sender_agent,context_prompt)


writing_task.context = [retriever_task]
send_task.context = [retriever_task]

crew = Crew(
    agents=[retriever_agent,writer_agent,sender_agent],
    tasks=[retriever_task,writing_task,send_task],
)

if st.button("Run Crew"):
    result = crew.kickoff()
    st.write(result)