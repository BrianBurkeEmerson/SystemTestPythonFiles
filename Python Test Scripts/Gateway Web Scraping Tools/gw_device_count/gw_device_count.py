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
INDEX_SEPARATOR = " - "

# These are used to identify the four tabs along the top of the devices page
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

# hostname: The device you are connecting to
# user: Username for gateway login
# password: Password for gateway login
# supports_isa: Whether the gateway supports ISA devices (if set to True when the gateway doesn't support ISA, the program will crash)
# factory_enabled: Whether or not factory accounts are enabled (program will wait to close the dialog box if they are)
# old_login_fields: Old versions of the gateway firmware used different names for the login and password fields
class GwDeviceCounter():
    def __init__(self, hostname = "192.168.1.10", user = "admin", password = "default", supports_isa = False, factory_enabled = True, old_login_fields = False, open_devices = True):

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

        # Call the default open function which brings the browser to the devices page
        if open_devices:
            self.open()


    # If the browser if closed and needs to be reopened, call the gateway_login() function
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
    

    def open(self):
        # Open the gateway's login page and enter credentials
        self.gateway_login()

        # After logging in, close the factory accounts dialog if factory accounts are enabled
        if self.factory_enabled:
            self.retry_until_success(self.close_factory_account_dialog)

        # Finally, open the device tab before giving control back to the user/application
        self.retry_until_success(self.open_devices_tab)
        self.wait_for_count_updates()
    

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


    # After retrieving the correct elements from the webpage, parse the strings and return integers
    def parse_results(self, results_text):
        start_index = results_text.find(TEXT_BEFORE_COUNT) + len(TEXT_BEFORE_COUNT)
        end_index = results_text.find(TEXT_AFTER_COUNT)
        return int(results_text[start_index:end_index])
    

    # Returns which devices are displayed (example "6 - 10 of x results" returns start as 6, end as 10, and length as 5)
    def get_displayed_device_indices(self):
        dgrid_statuses = self.driver.find_elements_by_class_name(DEVICE_COUNT_STATUS)

        return_dict = {
            "HART" : self.parse_displayed_device_text(dgrid_statuses[0].text)
        }

        if self.supports_isa:
            return_dict["ISA"] = self.parse_displayed_device_text(dgrid_statuses[1].text)

        return return_dict


    # Takes the text from get_display_device_indices() and parses it
    def parse_displayed_device_text(self, results_text):
        start_device = int(results_text[0:results_text.find(INDEX_SEPARATOR)])
        end_device = int(results_text[results_text.find(INDEX_SEPARATOR) + len(INDEX_SEPARATOR):results_text.find(TEXT_BEFORE_COUNT)])

        return_dict = {
            "Start" : start_device,
            "End" : end_device,
            "Length" : end_device - start_device + 1
        }

        return return_dict
    

    # Wait until Javascript on page updates counts of WirelessHART and ISA devices to match what is show on the four devices tabs
    # current_tab: Which tab is selected for counting devices
    # ---- Options are "All", "Live", "Unreachable", and "Low Battery"
    def wait_for_count_updates(self):
        time.sleep(0.5)

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
                time.sleep(REPEAT_ACTION_DELAY)


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
        buttons_unsorted = self.driver.find_elements_by_class_name(class_name)

        buttons = {
            "HART" : buttons_unsorted[0]
        }

        if self.supports_isa:
            buttons["ISA"] = buttons_unsorted[1]

        return buttons


    def get_first_page_buttons(self):
        return self.get_page_buttons(FIRST_PAGE_CLASS)
    

    def get_last_page_buttons(self):
        return self.get_page_buttons(LAST_PAGE_CLASS)

    
    def get_next_page_buttons(self):
        return self.get_page_buttons(NEXT_PAGE_CLASS)


    def get_previous_page_buttons(self):
        return self.get_page_buttons(PREVIOUS_PAGE_CLASS)
    

    # Takes the tables displayed on the devices page and converts them into dictionaries embedded in a list
    # Before use, the application should have already selected the desired tab
    # device_type: Should be "HART" or "ISA" to specify which devices are being converted into a table.
    # fields: The fields to record can be specified if not all are needed which can decrease the time to collect the data
    def convert_table_into_dicts(self, device_type = "HART", fields = (TABLE_NAME_FIELD, TABLE_PV_FIELD, TABLE_SV_FIELD, TABLE_TV_FIELD, TABLE_QV_FIELD, TABLE_LAST_UPDATE_FIELD)):
        # Go to the first page of devices
        self.get_first_page_buttons()[device_type].click()

        # Check if any devices/table entries are available and return an empty list if none are present
        if self.get_counts()[device_type] <= 0:
            return []
        else:
            # Create the list that will be returned
            return_table = []
            row_num = 1

            while row_num <= self.get_counts()[device_type]:
                # Check if the next page button needs to be pressed
                if row_num > self.get_displayed_device_indices()[device_type]["End"]:
                    self.get_next_page_buttons()[device_type].click()

                # Create the dictionary appended to the list for a given row
                row_dict = {}

                # Determine the row index for the given device
                # ISA devices are offset by the number of displayed HART devices
                # Multiple devices are returned by find_elements_by_class_name()
                css_row_index = row_num - self.get_displayed_device_indices()[device_type]["Start"]
                if (device_type == "HART"):
                    css_row_index += 1 # HART devices have an offset of 1 (Column header rows have index 0)
                elif (device_type == "ISA"):
                    css_row_index += (1 + self.get_displayed_device_indices()["HART"]["Length"] + 1) # ISA devices are offset by the number of HART devices and 2 header rows

                for cell in fields:
                    try:
                        row_cell = self.driver.find_elements_by_class_name(cell)[css_row_index] # Get the correct cell for a given row
                        
                        # Getting the element that displays the text is different depending on the field type
                        cell_text_element = None
                        if cell == TABLE_NAME_FIELD:
                            cell_text_element = row_cell.find_elements(By.XPATH, ".//div//*")[2]
                        elif cell == TABLE_LAST_UPDATE_FIELD:
                            cell_text_element = row_cell.find_elements(By.XPATH, ".//span//*")[0]
                        else:
                            cell_text_element = row_cell.find_elements(By.XPATH, ".//span//*")[1]

                        row_dict[cell] = cell_text_element.get_attribute("innerHTML") # Get the text inside the cell
                    except:
                        row_dict[cell] = "" # If nothing is entered in the cell, an exception is raised, so handle the empty entry here
                
                return_table.append(row_dict) # Add the row converted to a dict to the returned list

                # Increment the row count and check if all rows were added
                row_num += 1
            
            return return_table


    # Closes the web browser
    def close(self):
        self.driver.close()
