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


def create_url(product_sku):
    product_data = load_product_data()
    if product_sku in product_data.index:
        product_info = product_data.loc[product_sku]
        catalog_id = product_info['catalog_id']
        list_id = product_info['list_id']
        item_id = product_info['item_id']
        url = f"https://www.myorderdesk.com/FormV2.asp?Provider_ID=1325030&OrderFormID=534080&CatalogID={catalog_id}&INVSYN={list_id}|{item_id}"
        return url
    else:
        return None
