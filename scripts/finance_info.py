from distro import info
import yfinance as yf
import pandas as pd
import configparser
from pathlib import Path


_ticker = ''
_stock = None
_log_level = 'ERROR' # DEBUG, INFO, IMPORTANT, WARNING, ERROR
_company_info = []
_sector = []
_industry = []
_prices = None
_financials = None
_balancesheets = None
_cashflows = None
_period=""
_interval=""



def load_config():
    global _period, _interval
    config = configparser.ConfigParser()
    config_file = Path(r"d:/Development/PythonProjects/ai-finance-server/config") / "cfg.txt"
    print(f"Loading configuration from {config_file}")
    config.read(config_file)

    _period = str(config['yfinance']['period'])
    _interval = str(config['yfinance']['interval'])

    print(f"yfinance period:{_period}")
    print(f"yfinance interval:{_interval}")


def log(level : str, msg : str):
    if _log_level in ('DEBUG', 'INFO') or level in ('IMPORTANT', 'ERROR', 'WARNING'):
        print(msg)


def add_ticker(df : pd.DataFrame):
    if 'Ticker' not in df.columns:
        df['Ticker'] = get_ticker()
    return df


def set_ticker(ticker):
    global _ticker
    _ticker = ticker


def get_ticker():
    global _ticker
    if _ticker == '' or _ticker is None:
        log("ERROR", "Ticker not set. Please call set_ticker(ticker) first.")
        return None
    else:
        return _ticker


def set_stock():
    global _stock, _ticker
    if _ticker is None:
        log("ERROR", "Ticker not set. Please call set_ticker(ticker) first.")
        return

    if _stock is not None:
        if _ticker == _stock.info.get('symbol'):
            log("IMPORTANT", f"Stock already initialized for ticker:{_ticker()}")
            return
    
    _stock = yf.Ticker(_ticker)
    if _stock is not None:
        log("IMPORTANT", f"Initialized stock for ticker:{get_ticker()}")
    else:
        log("ERROR", f"Failed to initialize stock for ticker:{get_ticker()}")


def get_stock():
    global _stock
    if _stock is None:
        set_stock()
    return _stock


def get_prices(period='', interval=''):
    global _stock, _period, _interval

    if period == '':
        period = _period
    if interval == '':
       interval = _interval

    if _stock is None:
        log("INFO", "Stock not initialized. calling set_stock().")
        set_stock()
        if _stock is None:
            return None
    log("IMPORTANT", f"Fetching prices for ticker:{get_ticker()}, period={_period}, interval={_interval}")
    return _stock.history(period, interval)


def get_company_info():
    global _stock
    
    if _stock is None:
        log("INFO", "Stock not initialized. calling set_stock().")
        set_stock()
        if _stock is None:
            return None
    log("IMPORTANT", f"Fetching company info for ticker:{get_ticker()}")
    return _stock.info


def get_financials():
    global _stock
    
    if _stock is None:
        log("INFO", "Stock not initialized. calling set_stock().")
        set_stock()
        if _stock is None:
            return None
    log("IMPORTANT", f"Fetching financials for ticker:{get_ticker()}")
    return _stock.financials


def get_balance_sheet():
    global _stock

    if _stock is None:
        log("INFO", "Stock not initialized. calling set_stock().")
        set_stock()
        if _stock is None:
            return None
    log("IMPORTANT", f"Fetching balance sheet for ticker:{get_ticker()}")
    return _stock.balance_sheet


def get_cashflow():
    global _stock

    if _stock is None:
        log("INFO", "Stock not initialized. calling set_stock().")
        set_stock()
        if _stock is None:
            return None
    log("IMPORTANT", f"Fetching cashflow for ticker:{get_ticker()}")
    return _stock.cashflow


def get_sector():
    global _stock

    if _stock is None:
        log("INFO", "Stock not initialized. calling set_stock().")
        set_stock()
        if _stock is None:
            return None

    log("IMPORTANT", f"Fetching sector for ticker:{get_ticker()}")
    _sector = yf.Sector(_stock.info.get('sectorKey'))
    log("INFO", f"Sector: key={_sector.key}, name={_sector.name}, overview={_sector.overview}, top companies={_sector.top_companies.size}")

    return {
        'key': _sector.key, 'name': _sector.name,
        'overview': _sector.overview,
        'top_companies': _sector.top_companies
    }


def get_industry():
    global _stock

    if _stock is None:
        log("INFO", "Stock not initialized. calling set_stock().")
        set_stock()
        if _stock is None:
            return None
    log("IMPORTANT", f"Fetching industry for ticker:{get_ticker()}")
    _industry = yf.Industry(_stock.info.get('industryKey'))
    log("INFO", f"Industry: key={_industry.sector_key}, name={_industry.sector_name}, top companies={_industry.top_performing_companies.size}, growth companies={_industry.top_growth_companies.size}")

    return {
        'key': _industry.key, 'name': _industry.name, 
        'sector_key': _industry.sector_key, 'sector_name': _industry.sector_name, 
        'overview': _industry.overview,
        'top_companies': _industry.top_companies
    }


def get_ticker_data():
    global _ticker, _prices, _financials, _balancesheets, _cashflows, _company_info, _sector, _industry
    
    if _ticker is None or _ticker == '':
        log("ERROR", "Invalid ticker symbol.")
        return

    prices = get_prices()
    add_ticker(prices)
    if _prices is None:
        _prices = prices
    else:
        _prices = pd.concat([_prices, prices], ignore_index=True)
    log("INFO", f"Prices:\n{_prices.head(3)}\n{_prices.tail(2)}")

    financials = get_financials()
    add_ticker(financials)
    if _financials is None:
        _financials = financials
    else:
        _financials = pd.concat([_financials, financials], ignore_index=True)
    log("INFO", f"Financials:\n{_financials.head(3)}\n{_financials.tail(2)}")

    balance_sheet = get_balance_sheet()
    add_ticker(balance_sheet)
    if _balancesheets is None:
        _balancesheets = balance_sheet
    else:
        _balancesheets = pd.concat([_balancesheets, balance_sheet], ignore_index=True)
    log("INFO", f"Balance Sheet:\n{_balancesheets.head(3)}\n{_balancesheets.tail(2)}")

    cashflow = get_cashflow()
    add_ticker(cashflow)
    if _cashflows is None:
        _cashflows = cashflow
    else:
        _cashflows = pd.concat([_cashflows, cashflow], ignore_index=True)
    log("INFO", f"Cash Flow:\n{_cashflows.head(3)}\n{_cashflows.tail(2)}")

    company_info = get_company_info()
    log("INFO", f'company info:\n{company_info["symbol"]}')
    if company_info['symbol'] not in [info.get('symbol') for info in _company_info]:
        log("IMPORTANT", f"Adding company info for symbol:{company_info['symbol']}")
        _company_info.append(company_info)
    log("INFO", f"symbols:\n{[info['symbol'] for info in _company_info]}")

    sector = get_sector()
    log("INFO", f"sector: name={sector['name']}")
    if sector['key'] not in [sector.get('key') for sector in _sector]:
        log("IMPORTANT", f"Adding sector info for sector:{sector['key']}")
        _sector.append(sector)
    log("INFO", f"sectors\n{[sector['key'] for sector in _sector]}")

    industry = get_industry()
    log("INFO", f"Industry: name={industry['name']}")
    if industry['key'] not in [industry.get('key') for industry in _industry]:
        log("IMPORTANT", f"Adding industry info for key:{industry['key']}")
        _industry.append(industry)
    log("INFO", f"industries\n{[industry['key'] for industry in _industry]}")
    

def get_tickers(tickers : list):
    for ticker in tickers:
        set_ticker(ticker)
        set_stock()
        get_ticker_data()
        
    return {
        'prices': _prices, 'financials': _financials, 'balancesheets': _balancesheets, 'cashflows': _cashflows,
        'company_info': _company_info, 'sector': _sector, 'industry': _industry
    }


if __name__ == "__main__":
    load_config()
    get_tickers(['AAPL', 'MSFT', 'GOOGL'])

