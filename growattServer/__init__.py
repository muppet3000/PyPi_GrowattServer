name = "growattServer"

import datetime
from enum import IntEnum
import hashlib
import json
import requests
import warnings

def hash_password(password):
    """
    Normal MD5, except add c if a byte of the digest is less than 10.
    """
    password_md5 = hashlib.md5(password.encode('utf-8')).hexdigest()
    for i in range(0, len(password_md5), 2):
        if password_md5[i] == '0':
            password_md5 = password_md5[0:i] + 'c' + password_md5[i + 1:]
    return password_md5

class Timespan(IntEnum):
    day = 1
    month = 2


class GrowattApi:
    server_url = 'https://server.growatt.com/'

    def __init__(self):
        self.session = requests.Session()

    def get_url(self, page):
        """
        Simple helper function to get the page url/
        """
        return self.server_url + page

    def login(self, username, password):
        """
        Log the user in.
        """
        password_md5 = hash_password(password)
        response = self.session.post(self.get_url('LoginAPI.do'), data={
            'userName': username,
            'password': password_md5
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_list(self, user_id):
        """
        Get a list of plants connected to this account.
        """
        response = self.session.get(self.get_url('PlantListAPI.do'),
                                    params={'userId': user_id},
                                    allow_redirects=False)
        if response.status_code != 200:
            raise RuntimeError("Request failed: %s", response)
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def plant_detail(self, plant_id, timespan, date):
        """
        Get plant details for specified timespan.
        """
        assert timespan in Timespan
        if timespan == Timespan.day:
            date_str = date.strftime('%Y-%m-%d')
        elif timespan == Timespan.month:
            date_str = date.strftime('%Y-%m')

        response = self.session.get(self.get_url('PlantDetailAPI.do'), params={
            'plantId': plant_id,
            'type': timespan.value,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data['back']

    def inverter_data(self, inverter_id, date):
        """
        Get inverter data for specified date or today.
        """
        if date is None:
            date = datetime.date.today()
        date_str = date.strftime('%Y-%m-%d')
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterData',
            'id': inverter_id,
            'type': 1,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data

    def inverter_detail(self, inverter_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterDetailData',
            'inverterId': inverter_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def inverter_detail_two(self, inverter_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newInverterAPI.do'), params={
            'op': 'getInverterDetailData_two',
            'inverterId': inverter_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def tlx_data(self, tlx_id, date):
        """
        Get inverter data for specified date or today.
        """
        if date is None:
            date = datetime.date.today()
        date_str = date.strftime('%Y-%m-%d')
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxData',
            'id': tlx_id,
            'type': 1,
            'date': date_str
        })
        data = json.loads(response.content.decode('utf-8'))
        return data

    def tlx_detail(self, tlx_id):
        """
        Get "All parameters" from PV inverter.
        """
        response = self.session.get(self.get_url('newTlxApi.do'), params={
            'op': 'getTlxDetailData',
            'id': tlx_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def mix_info(self, mix_id, plant_id = None):
        """
        Get high level values from Mix device.
        mix_id: The serial number (device_sn) of the inverter
        plant_id: Optional - The ID of the plant (the mobile app uses this but it does not appear to be necessary)
        """
        request_params={
            'op': 'getMixInfo',
            'mixId': mix_id
        }

        if (plant_id):
          request_params['plantId'] = plant_id

        response = self.session.get(self.get_url('newMixApi.do'), params=request_params)

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def mix_totals(self, mix_id, plant_id):
        """
        Get "Totals" from Mix device.
        mix_id: The serial number (device_sn) of the inverter
        plant_id: The ID of the plant
        """
        response = self.session.post(self.get_url('newMixApi.do'), params={
            'op': 'getEnergyOverview',
            'mixId': mix_id,
            'plantId': plant_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def mix_system_status(self, mix_id, plant_id):
        """
        Get "Status" from Mix device.
        mix_id: The serial number (device_sn) of the inverter
        plant_id: The ID of the plant
        """
        response = self.session.post(self.get_url('newMixApi.do'), params={
            'op': 'getSystemStatus_KW',
            'mixId': mix_id,
            'plantId': plant_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def dashboard_data(self, date, plant_id):
        """
NOTRUST   'eAcCharge': '16.1kWh': "Excess Solar" (shown incorrectly in the app as "exported to grid" as it may be used to charge batteries): Solar Production - Consumed Solar (excluding charging batteries)
TRUST     'eCharge': '21kWh': Solar Production
NOTRUST   'eChargeToday1': '4.9kWh': Consumed Solar (excluding from batteries) : eAcCharge = eCharge - eChargeToday1
TRUST     'eChargeToday2': '10.8kWh: Total Self Consumption (solar & batteries): eChargeToday2 = eChargeToday2Echarge1 + echarge1
TRUST     'eChargeToday2Echarge1': '4.2kWh': Self consumption solar contribution
TRUST     'echarge1': '6.6kWh': Self consumption battery contribution
TRUST     'elocalLoad': '19kWh': Load consumption
TRUST     'etouser': '8.2kWh': Imported from grid
TRUST     'photovoltaic': '4.2kWh': Load consumption from PV (Same as eChargeToday2Echarge1)

          #NOTE - photovoltaic, eChargeToday2Echarge1 and eChargeToday1 should all be the same, but for some reason eChargeToday1 is different
          #     Therefore - we choose not to trust the "eAcCharge" and "eChargeToday1" values instead we should calculate them ourselves using other data


          Extra value we can get from looking at the "month" view of the data:
TRUST       - export_to_grid: 10.6

          Extra value we can get from the other function calls:
TRUST       - Total battery discharge: 6.6
TRUST       - Total battery charge: 6.2

          Therefore:
            #This value can only be calculated (all other metrics only give total charge & discharge for the day
            Battery Charging from Solar (5.5) = Excess Solar (eAcCharge: 16.1) - export_to_grid (10.6)

            Solar Production (eCharge: 21) = Excess Solar (eAcCharge: 16.1) + Consumed Solar (eChargeToday1: 4.9)
            Solar Production (eCharge: 21) = Battery Charging from Solar (5.5) + export_to_grid (10.6) + Consumed Solar (eChargeToday1: 4.9)

            Load consumption (19) = Imported from grid (etouser: 8.2) + Self consumption battery contribution (6.6) + Consumption from Panels (photovoltaic: 4.2)
            #NOTE - "photovoltaic" is what makes this add up, but "photovoltaic" and "eChargeToday1" should align, but they don't.


          If we don't trust "Excess Solar" then we can calculate it as follows:
SAME      Excess Solar (16.1) = Solar Production (eCharge: 21) - Consumed Solar (eChargeToday1: 4.9)
          OR
DIFF      Excess Solar (16.8) = Solar Production (eCharge: 21) - Load consumption from PV (photovoltaic: 4.2)

          Therefore:
            #This value can only be calculated (all other metrics only give total charge & discharge for the day
            Battery Charging from Solar (6.2) = Excess Solar (CALC'd: 16.8) - export_to_grid (10.6)

            Solar Production (eCharge: 21) = Excess Solar (CALC'd: 16.8) + Load consumption from PV (photovoltaic: 4.2)
            Solar Production (eCharge: 21) = Battery Charging from Solar (6.2) + export_to_grid (10.6) + Load consumption from PV (photovoltaic: 4.2)

            Load consumption (19) = Imported from grid (etouser: 8.2) + Self consumption battery contribution (echarge1: 6.6) + Consumption from Panels (photovoltaic: 4.2)
        """
        date_str = date.strftime('%Y-%m-%d')
        response = self.session.post(self.get_url('newPlantAPI.do?action=getEnergyStorageData'), params={
#            'date': "2021-03-09",
            'date': date_str,
            'type': 0,
            'plantId': plant_id
        })
        data = json.loads(response.content.decode('utf-8'))
        return data


    def storage_detail(self, storage_id):
        """
        Get "All parameters" from battery storage.
        """
        response = self.session.get(self.get_url('newStorageAPI.do'), params={
            'op': 'getStorageInfo_sacolar',
            'storageId': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def storage_params(self, storage_id):
        """
        Get much more detail from battery storage.
        """
        response = self.session.get(self.get_url('newStorageAPI.do'), params={
            'op': 'getStorageParams_sacolar',
            'storageId': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data

    def storage_energy_overview(self, plant_id, storage_id):
        """
        Get some energy/generation overview data.
        """
        response = self.session.post(self.get_url('newStorageAPI.do?op=getEnergyOverviewData_sacolar'), params={
            'plantId': plant_id,
            'storageSn': storage_id
        })

        data = json.loads(response.content.decode('utf-8'))
        return data['obj']

    def inverter_list(self, plant_id):
        """
        Use device_list, it's more descriptive since the list contains more than inverters.
        """
        warnings.warn("This function may be deprecated in the future because naming is not correct, use device_list instead", DeprecationWarning)
        return self.device_list(plant_id)

    def device_list(self, plant_id):
        """
        Get a list of all devices connected to plant.
        """
        return self.plant_info(plant_id)['deviceList']

    def plant_info(self, plant_id):
        """
        Get basic plant information with device list.
        """
        response = self.session.get(self.get_url('newTwoPlantAPI.do'), params={
            'op': 'getAllDeviceList',
            'plantId': plant_id,
            'pageNum': 1,
            'pageSize': 1
        })

        data = json.loads(response.content.decode('utf-8'))
        return data
