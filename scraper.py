"""
This script is used to automate the process of adding items to a cart
on the Stallion website.
It uses the WebAutomation class to navigate to a product page,
add the item to the cart, and then proceed to the next item.

Generate a .env file with the following variables:
USERNAME="robot_username"
PASSWORD="robot_password"

Usage:
- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt
- python3 scraper.py
"""

import os
from webautomation import WebAutomation
from models import Payload, OrderGroup
from utils import create_url, load_product_data
from typing import List
from dotenv import load_dotenv
import pyfiglet
import logging
import traceback
import json

# Setup logging and load environment variables
load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def create_order_groups(payload: Payload) -> List[OrderGroup]:
    return payload.group_by_size()


def populate_automation_response(
        automation_response: dict,
        order_groups: List[OrderGroup]) -> None:
    """
    Populate the automation response with the order groups

    :param automation_response: The automation response to populate
    :param order_groups: The order groups to populate the automation response
    with (list of OrderGroup objects)
    :return: None
    """
    for order_group in order_groups:
        automation_response["sizes"][order_group.size_group] = {
            "job_number": None,
            "pdf": None,
            "errors": {}
        }


def print_banner():
    print(pyfiglet.figlet_format("MoellerMatic"))


def main(json_payload: str):
    try:
        # Print automation name
        print_banner()

        # Load product data
        product_data = load_product_data()

        # Create Payload object from JSON
        payload = Payload.from_json(json_payload, product_data, create_url)

        # Create order groups
        order_groups = create_order_groups(payload)

        # Populate the automation_response with the order groups
        automation_response = {
            "status_code": 200,
            "sizes": {}  # key is the size, value is a dict with job_number, pdf, errors
        }
        populate_automation_response(automation_response, order_groups)

        # Set up WebAutomation with environment variables
        BASE_URL = "https://www.myorderdesk.com/SignIn/"
        USERNAME = os.getenv("USERNAME")
        PASSWORD = os.getenv("PASSWORD")

        purchase_order_number = json.loads(json_payload)['purchase_order_number']
        automation = WebAutomation(BASE_URL, USERNAME, PASSWORD, automation_response, purchase_order_number)
        # Run the automation
        automation_response = automation.run(order_groups)

        return automation_response
    except Exception as e:
        traceback.print_exc()
        logging.error(f"An error occurred in the main function: {e}")
        return {"status_code": 500, "critical_error": str(e)}


if __name__ == "__main__":
    json_payload = '''
    {
        "order": [
            {"sku": "912PR243F172", "quantity": 2},
            {"sku": "912PR101F172", "quantity": 1},
            {"sku": "1212FVRPWAS", "quantity": 1},
            {"sku": "1218CF04F3", "quantity": 1},
            {"sku": "1218CF05F3", "quantity": 1}
        ],
        "purchase_order_number": "test!123test"
    }
    '''
    return_response = main(json_payload)
    print(json.dumps(return_response, indent=2))
