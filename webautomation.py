import logging
import time
import os
import base64
from models import OrderGroup, OrderItem
from typing import List
from datetime import datetime, timedelta
from config import TEST_MODE

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select


class WebAutomation:
    def __init__(self, base_url, username, password, automation_response, purchase_order_number):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.automation_response = automation_response
        self.purchase_order_number = purchase_order_number
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self.setup_logging(purchase_order_number)

    def setup_logging(self, purchase_order_number):
        """
        Setup the logging for the web automation
        """
        # Make sure the logs directory exists
        if not os.path.exists("./logs"):
            os.makedirs("./logs")

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            filename=f"./logs/{purchase_order_number}-{datetime.now().strftime('%m-%d-%Y')}.log",
            filemode="w"
        )

    def initialize_driver(self):
        """
        Initialize the web driver
        """
        try:
            service = Service(ChromeDriverManager().install())
            chrome_options = Options()

            # Make sure the job_confirmations directory exists
            if not os.path.exists("./job_confirmations"):
                os.makedirs("./job_confirmations")

            prefs = {
                "download.default_directory": os.path.abspath("./job_confirmations/"),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False
            }
            chrome_options.add_experimental_option('prefs', prefs)
            #chrome_options.add_argument("--headless=new") # Comment this out if you want to see the browser
            chrome_options.add_argument("--kiosk")
            chrome_options.add_argument("--kiosk-printing")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.get(self.base_url)
            self.logger.info("[+] WebDriver initialized and navigated to base URL.")
        except WebDriverException as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def login(self):
        """
        Login to the web application
        """
        try:
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "Email"))
            )
            password_field = self.driver.find_element(By.ID, "Password")
            login_button = self.driver.find_element(By.XPATH, '//*[@id="SignIn"]/div/div[4]/div[1]/button')

            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            login_button.click()
            self.logger.info("[+] Login submitted.")

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="catalogMain"]/section/article/a/h3'))
            )
            self.logger.info("[+] Login successful.")
        except (NoSuchElementException, TimeoutException) as e:
            self.logger.error(f"Login failed: {e}")
            raise

    def add_to_cart(self, item: OrderItem):
        """
        Add an item to the cart

        :param item: The item to add to the cart
        """
        try:
            self.driver.get(item.url)
            time.sleep(3)
            quantity_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "qty_DocMartPrompt2"))
            )
            quantity_input.clear()
            quantity_input.send_keys(str(item.quantity))

            add_to_cart_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="Save"]'))
            )
            add_to_cart_button.click()
            time.sleep(3)
            self.logger.info(f"[+] Added product to cart: {item.sku}, Quantity: {item.quantity}")
        except (NoSuchElementException, TimeoutException) as e:
            self.logger.error(f"Failed to add product to cart: {e}")
            raise

    def process_order_group(self, order_group: OrderGroup):
        """
        Process an order group

        :param order_group: The order group to process
        """
        try:
            for item in order_group.items:
                self.logger.info(f"[+] Adding product to cart: {item.sku}, Quantity: {item.quantity}")
                self.add_to_cart(item)

            self.logger.info(f"[+] Processed order group: {order_group.size_group}")
        except Exception as e:
            self.logger.error(f"Failed to process order group: {e}")
            raise

    def order_confirmation_page(self):
        """
        Download the PDF by executing JavaScript to print the page and rename it
        """
        try:
            order_confirmation_number = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="OrderMeta"]/div[1]/strong'))
            )
            order_confirmation_number = order_confirmation_number.text

            pdf = self.driver.execute_cdp_cmd("Page.printToPDF", {
                "printBackground": True,
                "format": "A4"
            })

            # Decode the PDF base64 and save the file
            pdf_data = base64.b64decode(pdf['data'])

            # Rename the downloaded file TODO: CHANGE THIS IMPLEMENTATION TO S3 BUCKET
            new_file_path = f"./job_confirmations/{self.purchase_order_number}-{order_confirmation_number}.pdf"
            with open(new_file_path, 'wb') as f:
                f.write(pdf_data)

            self.logger.info(f"[+] PDF downloaded and renamed successfully to {order_confirmation_number}.pdf")
            time.sleep(3)

            return new_file_path, order_confirmation_number

        except Exception as e:
            self.logger.error(f"[-] Error downloading PDF: {e}")
            return None

    def check_cart_items(self, order_group: OrderGroup):
        """
        Check if all items from the order group are in the cart

        :param order_group: The order group to check the cart items for
        :return: The list of missing items
        """
        self.driver.get("https://www.myorderdesk.com/Cart.asp")
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.ID, "cart"))
        )
        cart_items = self.driver.find_elements(By.CSS_SELECTOR, "#cart tbody tr")
        cart_skus = {}
        for item in cart_items:
            product_name = item.find_element(By.CSS_SELECTOR, "a.SafeUnload").text
            sku = product_name.split('-')[0].strip().split()[-1]
            quantity = int(item.find_element(By.CSS_SELECTOR, "td.colQuantity").text)
            cart_skus[sku] = quantity

        missing_or_incorrect_items = []
        for item in order_group.items:
            if item.sku not in cart_skus:
                missing_or_incorrect_items.append(item)
            elif cart_skus[item.sku] != item.quantity:
                missing_or_incorrect_items.append(item)

        return missing_or_incorrect_items

    def retry_add_to_cart(self, missing_items: List[OrderItem]):
        """
        Retry to add the missing items to the cart

        :param missing_items: The list of missing items
        :return: The list of remaining missing items
        """
        for item in missing_items:
            try:
                self.add_to_cart(item)
            except Exception as e:
                self.logger.warning(f"Failed to add {item.sku} to cart: {e}")

        return self.check_cart_items(OrderGroup(size_group="retry", items=missing_items))

    def select_next_available_date(self):
        """
        Select the next available date from the calendar
        based on the current date (tomorrow) and the current time in UTC.
        """
        try:
            # Click on the date input to open the calendar
            date_input = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "DueDate"))
            )
            date_input.click()

            # Wait for the calendar to appear
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "datepicker-days"))
            )

            # Calculate the next available business day in UTC
            tomorrow_utc = datetime.utcnow() + timedelta(days=1)
            while tomorrow_utc.weekday() >= 5:  # 5 = Saturday, 6 = Sunday, 0 = Monday
                tomorrow_utc += timedelta(days=1)

            day_tomorrow = tomorrow_utc.strftime("%d")
            month_tomorrow = tomorrow_utc.strftime("%B")

            # Find and click on the next available business day
            next_day = self.driver.find_element(By.XPATH, f"//table[@class='table-condensed']//td[contains(@class, 'day') and not(contains(@class, 'disabled')) and text()='{day_tomorrow}']")
            next_day.click()

            self.logger.info(f"[+] Selected the next available date: {day_tomorrow} of {month_tomorrow}")
        except Exception as e:
            self.logger.error(f"Error selecting the next available date: {e}")
            raise

    def clear_cart(self):
        """
        Clear the cart

        Steps:
        1. Navigate to the cart page
        2. Check if the cart has items
        3. If it does, click the clear cart button
        4. Wait for the confirmation dialog
        5. Click the "OK" button to confirm deletion
        """
        try:
            self.logger.info("[+] Checking cart")
            self.driver.get("https://www.myorderdesk.com/Cart.asp")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "frmCart"))
            )

            cart_wrapper = self.driver.find_elements(By.ID, "cart_wrapper")
            if cart_wrapper:
                self.logger.info("[+] Cart has items, clearing...")
                clear_cart_button = self.driver.find_element(By.XPATH, '//*[@id="frmCart"]/div[1]/div[2]/a[1]')
                clear_cart_button.click()

                # Wait for the confirmation dialog
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "w3-modal"))
                )

                # Click the "OK" button to confirm deletion
                ok_button = self.driver.find_element(By.CSS_SELECTOR, "button.dlgbtn-ok")
                ok_button.click()

                self.logger.info("[+] Cart cleared successfully")
            else:
                self.logger.info("[+] Cart is already empty")
        except Exception as e:
            self.logger.error(f"[-] Error clearing cart: {e}")
            raise

    def checkout(self):
        """
        Checkout from the cart.

        Steps:
        1. Click on the checkout button
        2. Select the next available date
        3. Input the Purchase Order Number
        4. Select the PX Priority
        5. Select "I acknowledge and agree"
        6. Click on the Place Order button
        7. Wait for the order confirmation page
        """
        try:
            self.driver.get(f"https://www.myorderdesk.com/Cart.asp")
            time.sleep(3)

            checkout_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'checkout'))
            )
            checkout_button.click()
            time.sleep(3)

            # Input Purchase Order Number
            purchase_order_number = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'paymentCustom5982_1'))
            )
            purchase_order_number.send_keys(self.purchase_order_number)

            # Select PX Priority (ASAP)
            px_priority_select = Select(self.driver.find_element(By.ID, "paymentCustom5982_2"))
            px_priority_select.select_by_visible_text("ASAP")

            # Select "I acknowledge and agree"
            acknowledge_select = Select(self.driver.find_element(By.ID, "paymentCustom5982_5"))
            acknowledge_select.select_by_visible_text("to the terms shown in the PX catalog welcome page and the policies linked at the bottom of the site.")

            # Select requested by date
            self.select_next_available_date()

            time.sleep(3)

            if not TEST_MODE:
                # Click the Place Order button
                place_order_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, 'checkout-2'))
                )
                place_order_button.click()
                time.sleep(3)

                # Wait for the order confirmation page
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.ID, "OrderMeta"))
                )

                pdf_file_path, order_confirmation_number = self.order_confirmation_page()
            else:
                order_confirmation_number = "1234567890"
                pdf_file_path = f"{self.purchase_order_number}.pdf"

            return pdf_file_path, order_confirmation_number
        except Exception as e:
            self.logger.error(f"[-] Error checking out: {e}")
            raise

    def run(self, order_groups: List[OrderGroup]):
        """
        Run the web automation

        :param order_groups: The list of order groups to process
        """
        try:
            self.initialize_driver()
            self.login()

            for order_group in order_groups:
                try:
                    self.clear_cart()
                    self.process_order_group(order_group)

                    print(f"Problematic SKUs: {[sku for size in self.automation_response['sizes'].values() for sku, error in size.get('errors', {}).items() if sku != 'group_error']}")
                    raise SystemExit("End Test")
                    # retry_count = 0
                    # while retry_count < 3:
                    #     missing_or_incorrect_items = self.check_cart_items(order_group)
                    #     if not missing_or_incorrect_items:
                    #         break
                    #     self.retry_add_to_cart(missing_or_incorrect_items)
                    #     retry_count += 1

                    # if missing_or_incorrect_items:
                    #     for item in missing_or_incorrect_items:
                    #         self.automation_response["sizes"][order_group.size_group]["errors"][item.sku] = "Failed to add to cart or incorrect quantity"

                    pdf_file_path, order_confirmation_number = self.checkout()
                    if order_confirmation_number and pdf_file_path:
                        self.automation_response["sizes"][order_group.size_group]["job_number"] = order_confirmation_number
                        self.automation_response["sizes"][order_group.size_group]["pdf"] = pdf_file_path
                        # TODO: Implement S3 bucket storage for PDF      

                    #break
                except Exception as e:
                    self.logger.error(f"Error processing order group {order_group.size_group}: {e}")
                    self.automation_response["sizes"][order_group.size_group]["errors"]["group_error"] = str(e)
                    continue

            self.automation_response["status_code"] = 200
            return self.automation_response
        except Exception as e:
            self.logger.error(f"An error occurred during automation: {e}")
            self.automation_response["status_code"] = 500
            self.automation_response["error"] = str(e)
        finally:
            if self.driver:
                self.driver.quit()
            return self.automation_response


