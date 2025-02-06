from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json
import pandas as pd


@dataclass
class OrderItem:
    sku: str
    quantity: int
    catalog_id: Optional[str] = None
    list_id: Optional[str] = None
    item_id: Optional[str] = None
    product_name: Optional[str] = None
    shop_id: Optional[str] = None
    mis_itm_is: Optional[str] = None
    size: Optional[str] = None
    url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], product_data: pd.DataFrame, create_url_func):
        """
        Create the order item object from the product data and the json data

        :param data: The json data to create the order item object from
        :param product_data: The dataframe to create the order item object from
        :param create_url_func: The function to create the url for the order item
        :return: The order item object
        """
        sku = data['sku']
        quantity = data['quantity']
        if sku in product_data.index:
            item_data = product_data.loc[sku]
            
            # If we have multiple rows, select the one with longer shop_id
            if isinstance(item_data, pd.DataFrame) or isinstance(item_data['shop_id'], pd.Series):
                item_data = item_data.iloc[sorted(range(len(item_data)), 
                                                key=lambda i: len(str(item_data['shop_id'].iloc[i])), 
                                                reverse=True)[0]]
            
            catalog_id = str(item_data['catalog_id'])
            list_id = str(item_data['list_id'])
            item_id = str(item_data['item_id'])
            url = create_url_func(catalog_id, list_id, item_id)
            
            return cls(
                sku=sku,
                quantity=quantity,
                catalog_id=catalog_id,
                list_id=list_id,
                item_id=item_id,
                product_name=str(item_data['product_name']),
                shop_id=str(item_data['shop_id']),
                mis_itm_is=str(item_data['mis_item_id']),
                size=str(item_data['size']),
                url=url
            )
        else:
            return None


@dataclass
class OrderGroup:
    size_group: str
    items: List[OrderItem] = field(default_factory=list)

    def add_item(self, item: OrderItem):
        """
        Add an item to the order group

        :param item: The item to add to the order group
        """
        self.items.append(item)


@dataclass
class Payload:
    order: List[OrderItem]

    @classmethod
    def from_json(cls, json_data: str, product_data: pd.DataFrame, create_url_func):
        """
        Create the payload object from the pd.Dataframe and the json_data

        :param json_data: The json data to create the payload object from
        :param product_data: The product data to create the payload object from
        :param create_url_func: The function to create the url for
        the order item
        :return: The payload object
        """
        data = json.loads(json_data)
        order_items = []
        errors = {}
        for item in data['order']:
            order_item = OrderItem.from_dict(item, product_data, create_url_func)
            if order_item:
                order_items.append(order_item)
            else:
                errors[item['sku']] = "SKU not found in product data"

        payload = cls(order=order_items)
        return payload, errors

    def group_by_size(self) -> List[OrderGroup]:
        """
        Group the order items by size

        :return: The list of order groups
        """
        size_groups: Dict[str, OrderGroup] = {}
        for item in self.order:
            # Convert item.size to a string to ensure it's hashable
            item_size = str(item.size)  # or item.size.item() if it's a single-element Series
            if item_size not in size_groups:
                size_groups[item_size] = OrderGroup(size_group=item_size)
            size_groups[item_size].add_item(item)
        return list(size_groups.values())

# Example usage:
if __name__ == "__main__":
    json_payload = '''
    {
        "order": [
            {"sku": "17523FANPBUF", "quantity": 1},
            {"sku": "18734LEDLIGHT", "quantity": 3}
        ]
    }
    '''

    # Assume product_data is loaded from somewhere else
    product_data = {
        "17523FANPBUF": {
            "catalog_id": "123",
            "list_id": "456",
            "item_id": "789",
            "product_name": "Fan Buffer",
            "shop_id": "shop1",
            "mis_itm_is": "misc1",
            "size": "medium"
        },
        "18734LEDLIGHT": {
            "catalog_id": "234",
            "list_id": "567",
            "item_id": "890",
            "product_name": "LED Light",
            "shop_id": "shop2",
            "mis_itm_is": "misc2",
            "size": "small"
        }
    }
