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
import csv
from config import TEST_MODE
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
        payload, errors = Payload.from_json(json_payload, product_data, create_url)

        # If there are errors, print SKUs and their quantities
        if errors:
            print("\nThe following SKUs were not found in product data:")
            order_data = json.loads(json_payload)['order']
            for sku, error in errors.items():
                # Find the quantity for this SKU in the original order
                sku_lower = sku.lower()
                for item in order_data:
                    if item['sku'].lower() == sku_lower:
                        print(f"SKU: {sku} | Quantity: {item['quantity']} | Error: {error}")
                        errors[sku] = {'Error': "SKU not found in product data", 'Quantity': item['quantity']}

        # Create order groups
        order_groups = create_order_groups(payload)

        # Populate the automation_response with the order groups
        automation_response = {
            "status_code": 200,
            "sizes": {},  # key is the size, value is a dict with job_number, pdf, errors
            "errors": errors
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
        return {
            "status_code": 500,
            "critical_error": str(e),
            "sizes": automation_response.get("sizes", {}),
            "errors": automation_response.get("errors", {})
        }

def csv_to_json_payload(csv_path: str) -> str:
    """
    Convert a CSV file to a JSON payload string.

    :param csv_path: The path to the CSV file.
    :return: A JSON payload string.
    """
    try:
        with open(csv_path, mode='r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            order = [{"sku": row[0], "quantity": int(row[1])} for row in csv_reader]

        # Extract the purchase order number from the file name
        purchase_order_number = os.path.splitext(os.path.basename(csv_path))[0]
        
        # Create the JSON payload
        json_payload = {
            "order": order,
            "purchase_order_number": purchase_order_number
        }

        return json.dumps(json_payload)
    except Exception as e:
        logging.error(f"An error occurred while converting CSV to JSON payload: {e}")
        return None

if __name__ == "__main__":
    # json_payload = '''
    # {
    #     "order": [
    #         {"sku": "912PR243F172", "quantity": 2},
    #         {"sku": "912PR101F172", "quantity": 1},
    #         {"sku": "1212FVRPWAS", "quantity": 1},
    #         {"sku": "1218CF04F3", "quantity": 1},
    #         {"sku": "1218CF05F3", "quantity": 1}
    #     ],
    #     "purchase_order_number": "test!123test"
    # }
    # '''
    csv_path = input("Enter the path to the CSV file: ")
    json_payload = csv_to_json_payload(csv_path)

    if json_payload:
        payload_data = json.loads(json_payload)
        print(f"Number of orders in payload: {len(payload_data['order'])}")
    else:
        raise SystemExit("End Test")

    return_response = main(json_payload)
    if TEST_MODE:
        print("============ TEST MODE =============")
    print(json.dumps(return_response, indent=2))

#TODO: Add function to save skus that are not in product data to a local file
#TODO: create a function to recieve json payload and return the automation response
#TODO: migrate code to the flask app
#TODO: create logic to finish purchasing when there are no erros, but stop when there are errors
#TODO: create function to take in raw product data from moeller and transform to our internal product data
#TODO: create db table for moeller product data
#TODO: create db table for moeller url id numbers
#TODO: make it possible to upload csv files to the server and run the automation on them
#TODO: think about how to give feedback to the user about the status of the automation