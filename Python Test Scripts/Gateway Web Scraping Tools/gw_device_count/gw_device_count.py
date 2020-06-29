# This module fetches data from a gateway about the number of devices connected
# It requires selenium which can be installed with "py -m pip install selenium"

# It also requires the Firefox Gecko driver which can be installed here
# https://github.com/mozilla/geckodriver/releases
# The folder containing geckodriver.exe MUST be added to your PATH to function correctly

# This driver allows the user to specify what device counts to be pulled from the device
# All/Live/Unreachable/Low Battery

# Any addresses are inputted without http:// or /page
# For instance, to connect to device rosemount1, the hostname should be "rosemount1"
# To connect to device located at 192.168.1.10, the hosename shoud be "192.168.1.10"

# The final return value will be a dictionary containing the number of devices in the following format
# {
#     "HART" : <device_count>,
#     "ISA" : <device_count>
# }

# If requesting every count (All/Live/Unreachable/Low Battery), the dictionary will be in the following format
# {
#     "All" : {
#         "HART" : <device_count>,
#         "ISA" : <device_count>
#     },
#     "Live" : {
#         "HART" : <device_count>,
#         "ISA" : <device_count>
#     },
#     "Unreachable" : {
#         "HART" : <device_count>,
#         "ISA" : <device_count>
#     },
#     "Low Battery" : {
#         "HART" : <device_count>,
#         "ISA" : <device_count>
#     }
# }

# Be sure to call the close() function after your script is finished

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
import time
import copy

# The following constants are used for identifying HTML/CSS elements
LOGIN_FIELD = "inputEmail"
PASSWORD_FIELD = "inputPassword"
OLD_LOGIN_PASSWORD_FIELD = "checking"
FACTORY_NO_BUTTON = "btnAlertDialogNo"
DEVICES_BUTTON = "devicesMenu"
DEVICE_COUNT_STATUS = "dgrid-status"
TEXT_BEFORE_COUNT = "of "
TEXT_AFTER_COUNT = " results"

# These are used to identify the four tabs along the top of the devices page
# ALL_DEVICES_TEXT = "txtAllDevices"
# LIVE_DEVICES_TEXT = "txtLive"
# UNREACHABLE_DEVICES_TEXT = "txtUnreachable"
# LOW_BATTERY_TEXT = "txtPowerModuleLow"
ALL_DEVICES_SPAN = "allDevices"
LIVE_DEVICES_SPAN = "liveDevices"
UNREACHABLE_DEVICES_SPAN = "unreachableDevices"
LOW_BATTERY_SPAN = "powerModuleLowDevices"

# These are for page navigation in the devices page
FIRST_PAGE_CLASS = "dgrid-first"
LAST_PAGE_CLASS = "dgrid-last"
NEXT_PAGE_CLASS = "dgrid-next"
PREVIOUS_PAGE_CLASS = "dgrid-previous"

# These are for table elements
TABLE_NAME_FIELD = "field-Name"
TABLE_PV_FIELD = "field-PV"
TABLE_SV_FIELD = "field-SV"
TABLE_TV_FIELD = "field-TV"
TABLE_QV_FIELD = "field-QV"
TABLE_LAST_UPDATE_FIELD = "field-lastUpdate"

# The following constants are used for delays/waits
REPEAT_ACTION_DELAY = 0.1
NUM_SECONDS_BEFORE_REFRESH = 10
REPEAT_ACTION_COUNT_BEFORE_REFRESH = NUM_SECONDS_BEFORE_REFRESH / REPEAT_ACTION_DELAY
DELAY_AFTER_CLOSING_FACTORY_DIALOG = 3
TAB_CHANGE_DELAY = 3 # Tabs can take an unnecessarily long time to update counts properly, so this may need to be increased

# hostname: The device you are connecting to
# user: Username for gateway login
# password: Password for gateway login
# supports_isa: Whether the gateway supports ISA devices (if set to True when the gateway doesn't support ISA, the program will crash)
# factory_enabled: Whether or not factory accounts are enabled (program will wait to close the dialog box if they are)
# old_login_fields: Old versions of the gateway firmware used different names for the login and password fields
class GwDeviceCounter():
    def __init__(self, \
        hostname = "192.168.1.10", user = "admin", password = "default", \
        supports_isa = False, factory_enabled = True, old_login_fields = False):

        # Store initialization variables
        self.login_url = "http://" + hostname + "/login"
        self.user = user
        self.password = password
        self.supports_isa = supports_isa
        self.factory_enabled = factory_enabled
        self.old_login_fields = old_login_fields
        self.current_devices_tab = ""

        # Create a profile that allows invalid security certificates (gateways have self-signed certificates)
        profile = webdriver.FirefoxProfile()
        profile.accept_untrusted_certs = True

        # Create the driver that controls the browser
        self.driver = webdriver.Firefox(firefox_profile = profile)

        # Open the gateway's login page and enter credentials
        self.gateway_login()

        # After logging in, close the factory accounts dialog if factory accounts are enabled
        if factory_enabled:
            self.retry_until_success(self.close_factory_account_dialog)

        # Finally, open the device tab before giving control back to the user/application
        self.retry_until_success(self.open_devices_tab)
        self.wait_for_count_updates()
        #time.sleep(TAB_CHANGE_DELAY)


    def gateway_login(self):
        # Open the login page
        self.driver.get(self.login_url)

        # Enter the username
        user_element = None
        if self.old_login_fields:
            user_element = self.driver.find_elements_by_id(OLD_LOGIN_PASSWORD_FIELD)[0]
        else:
            user_element = self.driver.find_element_by_id(LOGIN_FIELD)
        user_element.send_keys(self.user)

        # Enter the password and press Enter
        password_element = None
        if self.old_login_fields:
                password_element = self.driver.find_elements_by_id(OLD_LOGIN_PASSWORD_FIELD)[1]
        else:
            password_element = self.driver.find_element_by_id(PASSWORD_FIELD)
        password_element.send_keys(self.password)
        password_element.send_keys(Keys.RETURN)
    

    # Continuously retries a function until it finishes with a short delay between attempts
    # If the page doesn't respond after a certain amount of time, it will be refreshed
    def retry_until_success(self, function):
        count = 0
        retry = True

        while retry:
            retry = False

            try:
                function()
            except:
                retry = True
                count += 1
                time.sleep(REPEAT_ACTION_DELAY)
                
                if count > REPEAT_ACTION_COUNT_BEFORE_REFRESH:
                    count = 0
                    self.driver.refresh()


    # Closes the popup asking if the user wants to disable factory accounts
    def close_factory_account_dialog(self):
        no_button = self.driver.find_element_by_id(FACTORY_NO_BUTTON)
        no_button.click()

        # The page refreshes after closing the dialog, so wait until the refresh is done
        time.sleep(DELAY_AFTER_CLOSING_FACTORY_DIALOG)
    

    # Changes from the Home to Devices tab
    def open_devices_tab(self):
        devices_menu = self.driver.find_element_by_id(DEVICES_BUTTON)
        devices_menu.click()
        self.current_devices_tab = "All"
    

    # Changes the devices tab between All/Live/Unreachable/Low Battery
    def change_device_tab(self, tab = ALL_DEVICES_SPAN):
        # Manipulate the cursor to change tabs since the device tabs are not WebElements
        tab_to_set = self.driver.find_element_by_id(tab)
        cursor = ActionChains(self.driver).move_to_element(tab_to_set).click(tab_to_set)
        cursor.perform()

        # Update the current_tab to make waiting for Javascript work as intended
        if tab == ALL_DEVICES_SPAN:
            self.current_devices_tab = "All"
        elif tab == LIVE_DEVICES_SPAN:
            self.current_devices_tab = "Live"
        elif tab == UNREACHABLE_DEVICES_SPAN:
            self.current_devices_tab = "Unreachable"
        elif tab == LOW_BATTERY_SPAN:
            self.current_devices_tab = "Low Battery"

        # Sleep after changing tabs to let the counts update
        self.wait_for_count_updates()
        #time.sleep(TAB_CHANGE_DELAY)


    # After retrieving the correct elements from the webpage, parse the strings and return integers
    def parse_results(self, results_text):
        start_index = results_text.find(TEXT_BEFORE_COUNT) + len(TEXT_BEFORE_COUNT)
        end_index = results_text.find(TEXT_AFTER_COUNT)
        return int(results_text[start_index:end_index])
    

    # Wait until Javascript on page updates counts of WirelessHART and ISA devices to match what is show on the four devices tabs
    # current_tab: Which tab is selected for counting devices
    # ---- Options are "All", "Live", "Unreachable", and "Low Battery"
    def wait_for_count_updates(self):
        tab_span_definition = ""
        if self.current_devices_tab == "All":
            tab_span_definition = ALL_DEVICES_SPAN
        elif self.current_devices_tab == "Live":
            tab_span_definition = LIVE_DEVICES_SPAN
        elif self.current_devices_tab == "Unreachable":
            tab_span_definition = UNREACHABLE_DEVICES_SPAN
        elif self.current_devices_tab == "Low Battery":
            tab_span_definition = LOW_BATTERY_SPAN

        not_equal = True
        while not_equal:
            current_counts_dict = self.get_counts()
            current_count = current_counts_dict["HART"] + current_counts_dict["ISA"]

            expected_count = int(self.driver.find_element_by_id(tab_span_definition).get_attribute("innerHTML"))

            if current_count == expected_count:
                not_equal = False
            else:
                time.sleep(0.1)


    # After selecting the type of count to report, search the page and return them as a dictionary
    def get_counts(self):
        dgrid_statuses = self.driver.find_elements_by_class_name(DEVICE_COUNT_STATUS)

        # Assume the device only supports HART devices first
        counts = {
            "HART" : self.parse_results(dgrid_statuses[0].text),
            "ISA" : 0
        }

        # Update the ISA count if ISA devices are supported
        if self.supports_isa:
            counts["ISA"] = self.parse_results(dgrid_statuses[1].text)
        
        return counts


    # Reports the total number of devices connected and disconnected
    def get_all_devices_count(self):
        self.change_device_tab(tab = ALL_DEVICES_SPAN)
        return self.get_counts()
    

    # Reports the total number of live devices
    def get_live_devices_count(self):
        self.change_device_tab(tab = LIVE_DEVICES_SPAN)
        return self.get_counts()
    

    # Reports the total number of unreachable devices
    def get_unreachable_devices_count(self):
        self.change_device_tab(tab = UNREACHABLE_DEVICES_SPAN)
        return self.get_counts()
    

    # Reports the total number of devices with low batteries
    def get_low_battery_devices_count(self):
        self.change_device_tab(tab = LOW_BATTERY_SPAN)
        return self.get_counts()
    

    # Gets all four types of device counts
    def get_every_type_devices_count(self):
        counts = {
            "All" : self.get_all_devices_count(),
            "Live" : self.get_live_devices_count(),
            "Unreachable" : self.get_unreachable_devices_count(),
            "Low Battery" : self.get_low_battery_devices_count()
        }

        return counts
    

    def get_page_buttons(self, class_name):
        buttons = {
            "HART" : self.driver.find_elements_by_class_name(class_name)[0]
        }

        if self.supports_isa:
            buttons["ISA"] : self.driver.find_elements_by_class_name(class_name)[1]

        return buttons


    def get_first_page_buttons(self):
        return self.get_page_buttons(FIRST_PAGE_CLASS)
    

    def get_last_page_buttons(self):
        return self.get_page_buttons(LAST_PAGE_CLASS)

    
    def get_next_page_buttons(self):
        return self.get_page_buttons(NEXT_PAGE_CLASS)


    def get_previous_page_buttons(self):
        return self.get_page_buttons(PREVIOUS_PAGE_CLASS)
    

    def count_hart_device_types(self):
        self.change_device_tab(LIVE_DEVICES_SPAN)
        self.get_first_page_buttons()["HART"].click()

        a = self.driver.find_elements_by_class_name(TABLE_NAME_FIELD)[1].find_elements(By.XPATH, ".//div//*")[2].get_attribute("innerHTML")
        return a


    # Destroys the instance and closes the web browser
    def close(self):
        self.driver.close()
