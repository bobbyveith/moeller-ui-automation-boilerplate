import json
from typing import List

from models import Payload, OrderGroup
from utils import create_url, load_product_data


def create_order_groups(payload: Payload) -> List[OrderGroup]:
    # Group items by size using the new method in Payload
    order_groups = payload.group_by_size()

    # Print the order groups for verification
    for group in order_groups:
        print(f"Size Group: {group.size_group}")
        for item in group.items:
            print(f"  SKU: {item.sku}, Quantity: {item.quantity}, Name: {item.product_name}, Size: {item.size}, URL: {item.url}")

    return order_groups

def main(order_groups: List[OrderGroup]):
    confirmation_data = {} # some way of storing the confirmation data, maybe even update order_group object and save it directly to the object
    for order_group in order_groups:
        for item in order_group.items:
            # Run ui automation and add each item to the cart
        
            # place the order (do not actuall do this during testing) just do some mock stuff for now
            # after placing the order, there should be a printer icon that prints the page as pdf, get this pdf and save it
            # on this order confirmation page there is also a "Job #" this should be saved

            job_number = "" # get job number from order confirmation page
            order_group_confirmation_pdf = "" # download the order confirmation page and save it as base64 encoded string

            confirmation_data = {
                "job_number": job_number,
                "order_group_confirmation_pdf": order_group_confirmation_pdf
            }
            confirmation_data[order_group.size_group] = {
                "job_number": job_number,
                "order_group_confirmation_pdf": order_group_confirmation_pdf
            }
    failed_orders = [] # save detaled failure data log

    # think about keeping track of products that could not be ordered, found, added to cart, etc.
    response_payload = generate_response_payload(confirmation_data, failed_orders)

    send_response_payload(response_payload) # create some func to send back response payload to en endpoint ill give you
    pass




# Update the __main__ block to test the main function
if __name__ == "__main__":
    # Example JSON payload
    json_payload = {
        "order": [
            {"sku": "1823CF33F4", "quantity": 2},
            {"sku": "1218CF33F3", "quantity": 3},
            {"sku": "1823CF34F4", "quantity": 1},
            {"sku": "1218CF34F3", "quantity": 4},
            {"sku": "1823CF35F4", "quantity": 2},
            {"sku": "1823KOBE07F4", "quantity": 3},
            {"sku": "1218KOBE07F3", "quantity": 1},
            {"sku": "1823MJFTF4", "quantity": 5},
            {"sku": "1218MJFTF3", "quantity": 2},
            {"sku": "17523FANPARI", "quantity": 3},
            {"sku": "1218FANPARI", "quantity": 1},
            {"sku": "17523FANPATL", "quantity": 4},
            {"sku": "1218FANPATL", "quantity": 2},
            {"sku": "17523FANPBAL", "quantity": 3},
            {"sku": "1218FANPBAL", "quantity": 1},
            {"sku": "17523FANPBUF", "quantity": 2}
        ]
    }
    
    # Create a Payload object from the JSON data
    product_data = load_product_data()
    received_payload = Payload.from_json(json.dumps(json_payload), product_data, create_url)
    
    # Call the main function with the received payload
    order_groups = create_order_groups(received_payload)

    print(order_groups)