from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List
import uvicorn
from openai import AzureOpenAI
import configparser
from pathlib import Path

import finance_info as fi


# define Azure OpenAI settings
_endpoint = "https://dines-mmglo60u-eastus2.cognitiveservices.azure.com/"
_deployment = "gpt-4o"
_subscription_key = "A4aoNUfh2Z3IPDSSfOLwIGJs6JGgSJtU7tUpLQk564PjE2qUOkdnJQQJ99CCACHYHv6XJ3w3AAAAACOGW1e9"
_api_version = "2024-12-01-preview"
_client = None

# define the ai server variables
_messages = []
_ticker_list = []
# server configuration values (used only when running directly)
_host = ""
_port = 0
_reload = True


def load_config(section=''):
    global _endpoint, _subscription_key, _api_version, _deployment, _host, _port
    config = configparser.ConfigParser()
    config_file = Path(r"d:/Development/PythonProjects/ai-finance-server/config") / "cfg.txt"
    print(f"Loading configuration from {config_file}")
    config.read(config_file)

    if section in ('', 'azure'):
        _endpoint = config['azure']['endpoint']
        _subscription_key = config['azure']['subscription_key']
        _api_version = config['azure']['api_version']
        _deployment = config['azure']['deployment']
        print(f"azure endpoint:{_endpoint}")
        print(f"deployment:{_deployment}")
        print(f"subscription key:{_subscription_key}")
        print(f"AzureAI api version:{_api_version}")

    if section in ('', 'api'):
        _host = config['api']['ip']
        _port = int(config['api']['port'])
        print(f"api host:port:{_host}:{_port}")


def ai_test():
    global _client, _deployment
    
    print("Testing Azure OpenAI client...")
    response = _client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant.",
            },
            {
                "role": "user",
                "content": "I am going to Paris, what should I see?",
            }
        ],
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        model=_deployment
    )
    print(response.choices[0].message.content)


def set_aifinance_prompts(parts = 7):
    global _messages

    _messages = [
        {
            "role": "system",
            "content": "You are a financial analyst. Analyze the financial data provided and provide insights and recommendations.",
        },
        {
            "role": "system",
            "content": "Your response should be formated in the order i will explain.",
        },
        {
            "role": "system",
            "content": "The Financial Performance sub topics 1.Stock Performance, 2.Revenue, 3.EBITDA Margins and 4.Risk Metrics should be in separate sections with the ticker specific information under each section. I dont need the Financial Performance heade.",
        },
        {
            "role": "system",
            "content": "Followed by Investment Recommendations. Include the ticker specific information under this topic.",
        },
        {
            "role": "system",
            "content": "Followed by Risk Considerations for Investors. Include the ticker specific information under this topic.",
        },
        {
            "role": "system",
            "content": "Followed by Sector and Industry Insights",
        },
        {
            "role": "system",
            "content": "Lasty the Conclusion.",
        },
        {
            "role": "system",
            "content": "Financial data will be provided for companies identified by ticker symbols, along with industry and sector information.",
        }
    ]
    
    if parts >= 1:
        _messages.extend([
            {
                "role": "system",
                "content": f"The financial data provided has {parts} datesets.",
            },
        
            {
                "role": "system",
                "content": f"The first {parts if parts < 6 else parts - 2} dataset will have the ticker symbol to identify the company.",
            },
            {
              "role": "system",
                "content": "dataset 1 is stock prices for the companies.",
            }])

    if parts >= 2:
        _messages.extend([
            {
                "role": "system",
                "content": "dataset 2 is financials for the companies.",

            }])
    if parts >= 3:
        _messages.extend([
            {
                "role": "system",
                "content": "dataset 3 is balance sheet for the companies.",

            }])
    if parts >= 4:
        _messages.extend([
            {
                "role": "system",
                "content": "dataset 4 is cash flows for the companies.",
            }])
    if parts >= 5:
        _messages.extend([
            {
                "role": "system",
                "content": "dataset 5 is company information.",
            }])
    if parts >= 6:
        _messages.extend([
            {
                "role": "system",
                "content": "dataset 6 is related to sector information.",
            }])
    if parts == 7:
        _messages.extend([
            {
                "role": "system",
                "content": "dataset 7 is for industry information.",
            }])
    if parts >= 6:
        _messages.extend([
            {
                "role": "system",
                "content": "A company is part of an industry and industry is part of a sector.",
            }])
    

def get_aiserver_tickers():
    global _client
    response = _client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": "List the tickers you have data for. Only list the tickers as a comma separated list",
        }],
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        model=_deployment
    )
    return response.choices[0].message.content


def set_ai_finance_data():
    global _client, _deployment, _messages, _ticker_list

    # Step 1: Get financial data
    #_ticker_list = ['AAPL', 'MSFT', 'GOOGL']
    print(f"tickers:{_ticker_list}")
    tickers_data = fi.get_tickers(_ticker_list)
    prices = tickers_data['prices'].describe()
    financials = tickers_data['financials'].describe()
    balancesheets = tickers_data['balancesheets'].describe()
    cashflows = tickers_data['cashflows'].describe()
    company_infos = tickers_data['company_info']
    sectors = tickers_data['sector']
    industries = tickers_data['industry']
    
    # Step 2: set prompts for ai finance
    set_aifinance_prompts()
    print(f"Messages for Azure OpenAI:{len(_messages)}")

    # Step 3: add financial data
    _messages.extend([
        {
            "role": "user",
            "content": f"price data:\n{prices}",
        },
        {
            "role": "user",
            "content": f"financial data:\n{financials}",
        },
        {
            "role": "user",
            "content": f"balance sheet data:\n{balancesheets}",
        },
        {
            "role": "user",
            "content": f"cash flows data:\n{cashflows}",
        },
        {
            "role": "user",
            "content": f"company information data:\n{company_infos}",
        },
        {
            "role": "user",
            "content": f"sector data:\n{sectors}",
        },
        {
            "role": "user",
            "content": f"industry data:\n{industries}",
        }
    ])

    print("Running financial analysis using Azure OpenAI...")
    response = _client.chat.completions.create(
        messages=_messages,
        max_tokens=4096,
        temperature=1.0,
        top_p=1.0,
        model=_deployment
    )
    return response.choices[0].message.content


# --- FastAPI application setup ------------------------------------------------
app = FastAPI()
load_config('azure')
_client = AzureOpenAI(
        api_version=_api_version,
        azure_endpoint=_endpoint,
        api_key=_subscription_key,
        )

class TextList(BaseModel):
    """Pydantic model representing the POST payload."""
    tickers: List[str]


@app.post("/process", response_class=PlainTextResponse)
def process_items(payload: TextList):
    global _ticker_list
    """Endpoint that accepts a list of strings and returns an AI response."""

    _ticker_list = payload.tickers
    print(f"client ticker list = {_ticker_list}")
    
    #TODO: validate the ticker list and skip tickers already present
    _server_ticker_list = get_aiserver_tickers()
    print(f"tickers from ai server: {_server_ticker_list}")

    return set_ai_finance_data()
    # _server_ticker_list 


# test util to verify AxureAI client is working correctly.  Not part of the FastAPI server.
if __name__ == "__main__":
    load_config('api')
    # start FastAPI server when executed directly
    uvicorn.run("aiserver:app", host=_host, port=_port, reload=_reload)
