import os
import csv
from typing import Dict, Any, List
import pandas as pd


def load_product_data() -> pd.DataFrame:
    # Use relative path to locate the CSV file
    product_data_path = os.path.join(os.path.dirname(__file__), "./PRODUCT_DATA.csv")

    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(product_data_path)

    # Make the sku column the index
    df.set_index('sku', inplace=True)

    return df


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


def create_url(catalog_id: str, list_id: str, item_id: str) -> str:
    """
    Create the URL using the already retrieved product data
    
    :param catalog_id: The catalog ID from the product data
    :param list_id: The list ID from the product data
    :param item_id: The item ID from the product data
    :return: The formatted URL string
    """
    base_url = "https://www.myorderdesk.com/FormV2.asp"
    return f"{base_url}?Provider_ID=1325030&OrderFormID=534080&CatalogID={catalog_id}&INVSYN={list_id}|{item_id}"
