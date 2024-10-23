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
from pathlib import Path

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
        print(payload)

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


def csv_to_json_payload(csv_path: str) -> str:
    """
    Reads a CSV file and transforms it into a JSON payload string.
    
    :param csv_path: Path to the CSV file
    :return: JSON payload as a string
    """
    order_items = []
    csv_file = Path(csv_path)
    
    with csv_file.open('r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            sku = row[0]
            quantity = row[1]
            order_items.append({
                "sku": sku,
                "quantity": int(quantity)
            })

    payload = {
        "order": order_items,
        "purchase_order_number": csv_file.stem  # Use filename without extension as purchase_order_number
    }
    
    return json.dumps(payload, indent=4)  # Convert the dictionary to a formatted JSON string


if __name__ == "__main__":
    input_csv = input("Enter the CSV path: ")
    
    # Transform CSV to JSON payload
    json_payload = csv_to_json_payload(input_csv)

    # Run the automation
    return_response = main(json_payload)
    print(json.dumps(return_response, indent=2))
