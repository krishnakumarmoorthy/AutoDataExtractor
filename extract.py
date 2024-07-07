from appium import webdriver
import logging
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from appium.options.android import UiAutomator2Options
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
data_file_path = "charger_data.txt"

# Open the file with UTF-8 encoding
data_file = open(data_file_path, "a+", encoding="utf-8")
MAX_RETRIES = 100

def data_collect(string_lines):
    data_file.write(string_lines + "\n")
    data_file.flush()  # Ensure data is written to the file immediately

def timer():
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M")
    data_collect(f"Current date and time: {formatted_datetime}")

def initialize_driver():
    capabilities = dict(
        platformName='Android',
        automationName='uiautomator2',
        deviceName='OPPO A38',
        appPackage='com.namp.zeon',
        appActivity='com.namp.zeon.MainActivity',
        platformVersion='13',
        ignoreHiddenApiPolicyError=True,
        noReset=True
    )
    appium_server_url = "http://127.0.0.1:4723/wd/hub"
    capabilities_options = UiAutomator2Options().load_capabilities(capabilities)
    driver = webdriver.Remote(command_executor=appium_server_url, options=capabilities_options)
    return driver

def restart_app(driver, capabilities):
    try:
        driver.execute_script("mobile: shell", {"command": "am", "args": ["force-stop", capabilities['appPackage']]})
    except Exception as e:
        logging.error(f"Failed to stop app: {e}")
    try:
        driver.execute_script("mobile: shell", {"command": "am", "args": ["start", "-n", f"{capabilities['appPackage']}/{capabilities['appActivity']}"]})
    except Exception as e:
        logging.error(f"Failed to start app: {e}")

def find_station_buttons(driver, wait):
    try:
        return wait.until(
            EC.presence_of_all_elements_located((AppiumBy.XPATH, '//android.view.View[@content-desc="Map Marker"]'))
        )
    except TimeoutException:
        logging.error("Timeout while waiting for station buttons")
        return []

def collect_page_contents(driver, wait):
    try:
        logging.info("Collecting contents of the current page")
        page_contents = driver.find_elements(AppiumBy.XPATH, "//android.view.View")

        for element in page_contents:
            try:
                content_desc = element.get_attribute("content-desc")
                text = element.text
                data_collect(f"Element content-desc: {content_desc}, text: {text}")
            except StaleElementReferenceException:
                logging.warning("Stale element reference for an element on the current page, skipping it...")
                continue
    except Exception as e:
        logging.error(f"Error collecting page contents: {e}")

k = 0
retries = 0
driver = None
capabilities = dict(
    platformName='Android',
    automationName='uiautomator2',
    deviceName='OPPO A38',
    appPackage='com.namp.zeon',
    appActivity='com.namp.zeon.MainActivity',
    platformVersion='13',
    ignoreHiddenApiPolicyError=True,
    noReset=True
)

try:
    while True:
        if driver is None:
            driver = initialize_driver()
            wait = WebDriverWait(driver, 10)
            restart_app(driver, capabilities)
        else:
            restart_app(driver, capabilities)

        try:
            data_collect(f"Iteration {k}")
            data_collect("WebDriver started successfully")

            logging.info("Finding all charging station buttons/icons...")
            station_buttons = find_station_buttons(driver, wait)
            for index in range(len(station_buttons)):
                try:
                    if retries >= MAX_RETRIES:
                        restart_app(driver, capabilities)
                        retries = 0

                    station_button = station_buttons[index]
                    timer()

                    # Collect contents of the station button before clicking it
                    content_desc = station_button.get_attribute("content-desc")
                    text = station_button.text
                    data_collect(f"Station button {index + 1} - content-desc: {content_desc}, text: {text}")
                    data_collect(f"Type of station button: {type(station_button)}")

                    logging.info(f"Clicking on station button {index + 1}")
                    station_button.click()

                    # Wait for the details button to ensure the page has loaded
                    details_button = wait.until(
                        EC.presence_of_element_located((AppiumBy.XPATH, "//android.widget.Button[@content-desc='Details']"))
                    )

                    collect_page_contents(driver, wait)

                    # Optionally navigate back to the previous screen
                    if driver.current_activity != capabilities['appActivity']:
                        driver.back()
                except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                    logging.warning(f"Exception encountered: {e}, retrying...")
                    retries += 1
                    if retries >= MAX_RETRIES:
                        restart_app(driver, capabilities)
                        retries = 0
                    continue
                except Exception as e:
                    data_collect(f"Error processing station button {index + 1}: {e}")
                    logging.error(f"Error processing station button {index + 1}: {e}")
                    retries += 1
                    if retries >= MAX_RETRIES:
                        restart_app(driver, capabilities)
                        retries = 0
                    continue
                finally:
                    data_collect("!@#$%^&*")
            k += 1
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            retries += 1
            if retries >= MAX_RETRIES:
                restart_app(driver, capabilities)
                retries = 0
        finally:
            logging.info("Restarting the driver...")
            driver.quit()
            driver = None

finally:
    if driver is not None:
        driver.quit()
    data_file.close()
