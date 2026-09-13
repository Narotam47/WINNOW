#!/usr/bin/env python3
import json, urllib.request, urllib.parse

BASE = "https://agriexchange.apeda.gov.in"
URL  = f"{BASE}/India/GenerateApedaProductReport/GenerateIndExpApedaProduct"

PARAMS = {
    "ResultType":"Table","YearWiseType":"1","YearMonthType":"Year",
    "Years":"2019-20,2020-21,2021-22,2022-23,2023-24",
    "Months":"","MonthsName":"","producttype":"APEDA","SubHead":"",
    "ProductCode":"0606","countryregion":"country","CountryCodeexp":"0",
    "RegionCode":"","QuantityIn":"1","ValueIn":"1","Lacs":"0","Crore":"0",
    "USDoller":"1","USMill":"0","USBill":"0","USThousand":"0",
    "CheckCount":"0","CheckValue":"1","CheckQuantity":"1",
    "YearsName":"2019-20 to 2023-24","UnitAvg":"0",
}
headers = {
    "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With":"XMLHttpRequest",
    "Referer":f"{BASE}/India/GenerateAPEDAProductReport/Index",
    "Origin":BASE,
}
body = urllib.parse.urlencode(PARAMS).encode()
req  = urllib.request.Request(URL, data=body, headers=headers, method="POST")
with urllib.request.urlopen(req, timeout=60) as r:
    raw = r.read()

print(f"Raw response (first 500 chars): {raw[:500]}")
data = json.loads(raw)
print(f"Type: {type(data)}, Value: {data}")
