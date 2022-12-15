import requests


tag_filters = ["PLACEHOLDER-REPLACE-ME","PLACEHOLDER-REPLACE-ME"]
cvss3_base_limit = 9.5
vpr_limit = 7.5
accessKey = "PLACEHOLDER-REPLACE-ME"
secretKey = "PLACEHOLDER-REPLACE-ME"
report_format = "text/csv" # Supported values: application/json, text/csv

# ######################################################################################
# Disclaimers: 
# (1) This is a simpe POC. Not intended for production use.
# (2) Does not take pagination into account. 
#     Response data will be incomplete if containing more than 200 items. You should 
#     implment a loop over the returned pages if you want to do this in production.
# (3) When this POC is made (2022) the V3 API is still in Beta and may be subject to 
#     (presumably client breaking) changes.

# About/how to use:
# Run with python 3.5+
# (1) Fill in the ID of one or more tags in tag_filters parameter (Replace the place
#     holders. You get the ID from the URL if you go to the web interface to edit a tag 
#     value). They look something like this: 2693ba5f5-67a7-46d8-939d-bffbe1049a0b
# (2) Fill in your API keys, replace the place holders in accessKey, secretKey above.
# (3) Set the score limit (cvss3 base and vpr), as lower boundaries. 
# Will query the V3 scan API. Generate json or csv file with output
# Using the following endpoint:
# https://cloud.tenable.com/api/v3/findings/vulnerabilities/host/search

# Alternatively you can query the V2 api but in that case you will have to implement 
# several requests to get a similar data set (first request an export, then query the 
# status of the export, and last download the result). Not as synchronous in other words.
# Using V2 api you can call the following api endpoints/methods:
# https://cloud.tenable.com/vulns/export
# https://cloud.tenable.com/vulns/export/{export_uuid}/status
# https://cloud.tenable.com/vulns/export/{export_uuid}/chunks/{chunk_id}
#
# The V3 api is more powerful in that you can combine filtering conditions, like in 
# this POC we download vulnerabilties in a certain "tag space" with at least a VPR 
# score condition being fulfilled OR a cvss score condition being fullfilled (see 
# "filter" in payload below). In V2 api you cannot do such combined filtering.
# ######################################################################################

url = "https://cloud.tenable.com/api/v3/findings/vulnerabilities/host/search"

payload = {
    "filter": {"and": [
            {
                "property":"last_seen",
                "operator":"gt",
                "value":"-P30D"
            },
            {
                "property":
                "risk_modified",
                "operator":"neq","value":["ACCEPTED"]
            },
            {
                "property":"state",
                "operator":"eq",
                "value":["ACTIVE","RESURFACED","NEW"]
            },
            {"or":[
                {
                    "property":"definition.cvss3.base_score",
                    "operator":"gte","value": cvss3_base_limit
                },
                {
                    "property":"definition.vpr.score",
                    "operator":"gte","value": vpr_limit
                }
                ]
            },
            {
                "property":"asset.tags",
                "operator":"eq",
                "value": tag_filters
            }
        ]},
    "limit": 200,
    "fields":[
        "id",
        "asset.id",
        "asset.name",
        "asset.display_ipv4_address",
        "severity",
        "definition.name",
        "definition.id",
        "definition.family",
        "port",
        "protocol",
        "definition.vpr.score",
        "definition.cvss3.base_score",
        "definition.cvss2.base_score",
        "definition.severity",
        "state",
        "origin",
        "first_observed",
        "last_seen",
        "risk_modified"]
}

headers = {
    "Accept": report_format,
    "Content-Type": "application/json",
    "X-ApiKeys": "accessKey={};secretKey={}".format(accessKey, secretKey)
}

response = requests.post(url, json=payload, headers=headers)

# print(response.text) 
report_filename="vulnerabilities.{}".format(report_format.replace("/","."))
write_mode="w" 
write_object= response.text
with open(report_filename, write_mode) as f:
    f.write(write_object)
print("Saved the report as {}".format(report_filename))
