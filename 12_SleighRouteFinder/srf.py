import json
from collections import Counter


def classify(element, output=True):
    ip = element['id.orig_h']

    suspicious = False
    if "'" in element['uri'].casefold():
        if output: print(f"{ip} - SQLi uri: {element['uri']}")
        suspicious = True
    if "'" in element['user_agent'].casefold():
        if output: print(f"{ip} - SQLi user_agent: {element['user_agent']}")
        suspicious = True
    if "'" in element['username'].casefold():
        if output: print(f"{ip} - SQLi username: {element['username']}")
        suspicious = True
    if '<' in element['uri'].casefold():
        if output: print(f"{ip} - XSS uri: {element['uri']}")
        suspicious = True
    if '<' in element['host'].casefold():
        if output: print(f"{ip} - XSS host: {element['host']}")
        suspicious = True
    if '../'.casefold() in element['uri'].casefold():
        if output: print(f"{ip} - LFI uri: {element['uri']}")
        suspicious = True
    if '/etc/passwd'.casefold() in element['uri'].casefold():
        if output: print(f"{ip} - LFI uri: {element['uri']}")
        suspicious = True
    if ':;'.casefold() in element['user_agent'].casefold():
        if output: print(f"{ip} - Shell user_agent: {element['user_agent']}")
        suspicious = True

    return suspicious


# Get the ip addresses that have been misbehaving
def get_bad_ip_addresses(log_file):
    with open(log_file, 'r') as input_file:
        data = json.load(input_file)

    bad_ips = []
    for element in data:
        ip = element['id.orig_h']
        if classify(element, True):
            bad_ips.append(ip)

    print(f'Found {len(set(bad_ips))} IP addresses')
    return set(bad_ips)


# Find all entries of the pivot element belonging to the given ip addresses and
def get_bad_pivot_elements(log_file, ip_addresses, output_filename, pivot_element):
    with open(log_file, 'r') as input_file:
        data = json.load(input_file)

    bad_elements = []
    occurrences = []

    # Get the user agents used by each of the bad ip addresses
    for element in data:
        if element['id.orig_h'] in ip_addresses:
            bad_elements.append(element[pivot_element])

    # Count the occurrences of each of the user agents
    for element in data:
        if element[pivot_element] in bad_elements:
            occurrences.append(element[pivot_element])

    print(f'Number of occurrences for each {pivot_element}-value:')
    pivot_values = Counter(occurrences).most_common()
    with open(output_filename, 'w') as output_file:
        for value in pivot_values:
            print(f'{value[1]}: {value[0]}')
            output_file.write(f'{value[0]}\n')


# Get the malicious ip addresses that have a malicious version of the pivot element
def get_malicious_ips(log_file, bad_ua_filename, pivot_element):
    with open(log_file, 'r') as input_file:
        data = json.load(input_file)

    with open(bad_ua_filename, 'r') as bad_ua_file:
        user_agents = [ua.strip() for ua in bad_ua_file.readlines()]

    malicious_ips = []
    for element in data:
        if element[pivot_element] in user_agents:
            malicious_ips.append(element['id.orig_h'])

    # Print the list comma separated for easy copy-paste into the firewall rules
    print(f'The {len(set(malicious_ips))} malicious ip addresses:')
    print(','.join(set(malicious_ips)))


if __name__ == '__main__':
    print("SANS Holiday Hack Challenge 2019 - Objective 12 solution")
    print("--------------------------------------------------------")

    logfile = 'http.log.json'
    bad_pivot_elements_filename = 'bad_useragents.txt'
    pivot_element = 'user_agent'

    # Step 1, retrieve the ip addresses having suspicious patterns in the log file
    #         and get the user_agents of these ip addresses
    bad_ips = get_bad_ip_addresses(logfile)
    get_bad_pivot_elements(logfile, bad_ips, bad_pivot_elements_filename, pivot_element)

    # Step 2. After manually filtering out the false positives from the bad_useragents file, get the IP addresses that
    #         use a bad user_agent
    # get_malicious_ips(logfile, bad_pivot_elements_filename, pivot_element)
