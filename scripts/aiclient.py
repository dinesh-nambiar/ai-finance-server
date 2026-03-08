"""Simple client for calling the FastAPI server defined in aiserver.py."""

import sys
import requests


_url = 'http://192.168.0.2:8000/process'


def send_items(items, url=_url):
    """POST a list of strings to the server and print the plain-text response."""
    payload = {"tickers": items}
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
    except requests.RequestException as exc:
        print(f"Error calling {url}: {exc}")
        return None

    print(resp.text)
    return resp.text


def main():
    """Main function to read items from command line and send to server."""
    items = ['AAPL', 'MSFT', 'GOOGL']
    if not items:
        print("No items provided, exiting.")
        sys.exit(1)

    send_items(items)


if __name__ == "__main__":
    main()
