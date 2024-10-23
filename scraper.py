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
import pandas as pd
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


def main(json_payload: str):
    try:
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

        automation = WebAutomation(BASE_URL, USERNAME, PASSWORD, automation_response)
        # Run the automation
        automation.run(order_groups)

        return automation_response
    except Exception as e:
        traceback.print_exc()
        logging.error(f"An error occurred in the main function: {e}")
        return {"status_code": 500, "critical_error": str(e)}


if __name__ == "__main__":
    # Example JSON payload
    # 1. Group by size DONE
    # 2. Iterate over each sizer group until the end of the process of adding items to the cart
    # Before clicking on the checkout button, on the cart page, make a check to see if all the items from the payload are in the cart
    # If not, make while loop that will retry those items that are not in the cart and redo the process of checking them in the cart -> If the retry count is > 3, just continue with the flow and save that missing items in a list, so we can report it to the user.
    # If yes, continue with the flow DONE
    # checkout id ->  DONE
    # Purchase Order Number XPATH -> //*[@id="paymentCustom5982_1"] DONE
    # PX Priority -> JS dropdown menu with XPATH -> //*[@id="paymentCustom5982_2"]/option[2] DONE
    # I acknowledge and agree -> Same dropdown menu with XPATH -> //*[@id="paymentCustom5982_5"]/option[2] DONE
    # Place order button Id -> checkout-2 DONE
    # On the order confirmation page, get the confirmation number and save the pdf (prob at an S3 bucket) DONE
    # Confirmation number its the only div strong inside the section with id OrderMeta DONE
    # 3. Once the request is complete, get the confirmation number and save the pdf (prob at an S3 bucket)
    # 4. RETURNING RESPONSE JSON
    # response = {
    #     status_code: 200
    #     sizes: {
    #         "1": {
    #             "job_number": "123456",
    #             "pdf": "base64 encoded pdf",
    #             "errors": {
    #                 "sku_number_1": "error message",
    #                 "sku_number_2": "error message"
    #             }
    #         },
    #         "2": {
    #             "job_number": "123456",
    #             "pdf": "base64 encoded pdf"
    #         },
    #     }
    # }
    json_payload = '''
    {
        "order": [
            {"sku": "912PR243F172", "quantity": 2},
            {"sku": "912PR101F172", "quantity": 1},
            {"sku": "1212FVRPWAS", "quantity": 1},
            {"sku": "1218CF04F3", "quantity": 1},
            {"sku": "1218CF05F3", "quantity": 1}
        ]
    }
    '''
    return_response = main(json_payload)
    # print(json.dumps(return_response, indent=2))
