import time
import requests
import json



name_pattern = "your-first-scan-name, your-second-scan-name, your-third-scan-name"
accessKey = "-your-access-key-here--replaceme-"
secretKey = "-your-secret-key-here--replaceme-"
report_format = "text/csv" # Supported values: application/json, application/pdf, text/csv, text/html, text/xml

# API user Requires BASIC [16] user permissions and CAN VIEW [16] scan permissions. 

# ######################################################################################
# 
# Disclaimer: 
# This is a very simple POC. 
# (1) Not intended for production use.
# (2) Functionally it needs to be completed by iterating the pages of the configurations, 
#     if larger data sets are returned in the responses.
#     See comment about configs_request_limit and configs_url.
#
# About/how to use:
# Run with python 3.5+
# Fill in the name of one or more WAS scan(s) in name_pattern param 
# (or a string being contained in the names of several different was scans)
# Will query the v2 WAS scan API. Generate pdf reports from latest scan instances.
#
# Using the following api calls/methods:
# https://developer.tenable.com/reference/was-v2-config-search
# https://developer.tenable.com/reference/was-v2-scans-export
# https://developer.tenable.com/reference/was-v2-scans-download-export
#
# ######################################################################################

result_poll_frequency = 5 # seconds
result_poll_timeout = 120 # seconds
configs_request_limit = 100 # Note: - to query _all_ configs, if you have more than the request_limit, you will need to iterate all pages (increment the offset param in config_urls, you will get the page limit in the first reply)

configs_url = "https://cloud.tenable.com/was/v2/configs/search?limit={}&offset=0".format(configs_request_limit)
gen_report_url = "https://cloud.tenable.com/was/v2/scans/{}/report"
get_report_url = "https://cloud.tenable.com/was/v2/scans/{}/report"
config_ids = []
scan_ids = []



# ###########################################################################
# Getting all the configs - searching for match against the name pattern 
# Note: a 'configuration' is a scan definition - a 'scan' is a scan instance
# https://developer.tenable.com/reference/was-v2-config-search
# ##########################################################################

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-ApiKeys": "accessKey={};secretKey={}".format(accessKey, secretKey)
}

response = requests.post(configs_url, headers=headers)
response_obj = json.loads(response.text)
# print(response.text) <- if you want to check out the response format with all its parameters

# Search for the name pattern among the configs
for item in response_obj['items']:
    for pattern in name_pattern.split(","):
        print("Matching against pattern: {}".format(pattern.strip()))
        if pattern.strip() in item['name']:
            print("Found match: {}".format(item['name']))
            try:
                config_ids.append(item['config_id'])
                scan_ids.append(item['last_scan']['scan_id'])
                print("...retrieved a scan_id: {}".format(item['last_scan']['scan_id']))
            except:
                print("...could not retrieve any scan_id for the matching name - probably latest run was archived.")
            break
print("Matching configs: {}".format(str(config_ids)))
print("Matching scans: {}".format(str(scan_ids)))


# #################################################################
# Generate report from the latest scan(s) matching the name pattern
# https://developer.tenable.com/reference/was-v2-scans-export
# #################################################################

# Remark: 
# To get this to work, Content-Type needs to be set to the desired
# format of the requested resource. That is an incorrect implementation according to most of this discussion:
# https://webmasters.stackexchange.com/questions/31212/difference-between-the-accept-and-content-type-http-headers
# Accept should be used for that purpose. Heck, I set both to desired format for response. Seems to be corrected in 
# API V3 though, "Accept" will alone serve that purpose.
headers = {
    "Accept": report_format,
    "Content-Type": report_format,
    "X-ApiKeys": "accessKey={};secretKey={}".format(accessKey, secretKey)
}

for scan_id in scan_ids:

    response = requests.put(gen_report_url.format(scan_id), headers=headers)
    status_code = int(response.status_code)

    if status_code == 202 or status_code==200:
        print("OK, requested report to be generated for {}".format(scan_id))
    else:
        print("Unexpected status code {} while requesting report to be generated".format(status_code))


    # ####################################################################
    # Poll for and download the report result from the scan(s)
    # https://developer.tenable.com/reference/was-v2-scans-download-export
    # ####################################################################

    generate_time = 0;
    while (generate_time < result_poll_timeout) and (status_code == 202 or status_code==200):

        response = requests.get(get_report_url.format(scan_id), headers=headers)
        if int(response.status_code == 200):
            # do something with the report here, print to file (to print in console do: print(response.text))
            report_filename="{}.{}".format(scan_id,report_format.replace("/","."))
            write_mode="wb" if "pdf" in report_format else "w" 
            write_object=response.content if "pdf" in report_format else response.text
            with open(report_filename, write_mode) as f:
                f.write(write_object)
            print("Saved the report as {}".format(report_filename))
            break
        else:
            print("Status code:{}, waiting for report for {}".format(response.status_code, scan_id))
            generate_time += result_poll_frequency
            time.sleep(result_poll_frequency)
            print("Seconds: {}".format(generate_time))

print("Done")

