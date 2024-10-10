import os
import csv
from typing import Dict, Any, List

def load_product_data() -> Dict[str, Dict[str, str]]:
    # Use relative path to locate the CSV file
    product_data_path = os.path.join(os.path.dirname(__file__), "PRODUCT_DATA.csv")
    
    # Create a hashmap to store the product data
    product_data: Dict[str, Dict[str, str]] = {}
    
    # Read the CSV file and populate the hashmap
    with open(product_data_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            sku = row.pop('sku')  # Remove 'sku' from row and use it as the key
            product_data[sku] = row
    
    return product_data

def get_product_info(product_sku: str, product_data: Dict[str, Dict[str, str]]):
    # Search for the product_sku in the hashmap
    if product_sku in product_data:
        product_info = product_data[product_sku]
        return (
            product_info.get('catalog_id'),
            product_info.get('list_id'),
            product_info.get('item_id'),
            product_sku,
            product_info.get('product_name'),
            product_info.get('shop_id'),
            product_info.get('mis_itm_is'),
            product_info.get('size')
        )
    else:
        return None, None, None, None, None, None, None, None  # Return None values if SKU not found

def create_url(product_sku):
    catalog_id, list_id, item_id, *_ = get_product_info(product_sku, load_product_data())

    url = f"https://www.myorderdesk.com/FormV2.asp?Provider_ID=1325030&OrderFormID=534080&CatalogID={catalog_id}&INVSYN={list_id}|{item_id}"
    return url