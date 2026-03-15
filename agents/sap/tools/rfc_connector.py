"""agents/sap/tools/rfc_connector.py — mock RFC/BAPI connector."""
from shared import new_id,utc_now
BAPI_CATALOGUE={"MM":["BAPI_PO_GETITEMS","BAPI_GOODSMVT_CREATE"],"FI":["BAPI_ACC_DOCUMENT_POST"],"SD":["BAPI_SALESORDER_GETLIST"],"HR":["BAPI_EMPLOYEE_GETDATA"]}
class RFCConnector:
    def __init__(self,config=None): self.config=config or {}
    def call_bapi(self,bapi_name:str,params:dict)->dict:
        return {"RETURN":[{"TYPE":"S","MESSAGE":f"BAPI {bapi_name} executed successfully","ID":"00","NUMBER":"000"}],
                "DOCUMENT_NUMBER":new_id("sap"),"STATUS":"S","DATA":[{"PO_NUMBER":"4500001234","VENDOR":"0000100045",
                "DELIVERY_DATE":"20250115","NET_VALUE":"12500.00","CURRENCY":"GBP","STATUS":"A"}]}
