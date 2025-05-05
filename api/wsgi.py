from sys import argv
from __init__ import init_app

print(len(argv))

flag = None
if len(argv) > 1:
    flag = argv[1]

# Return hardcoded test JSON data
if flag == "--test":
    print("Running test version of API; hardcoded JSON will be returned from calls.")
    is_test = True

# Return actual database data
else:
    print("Running non-test API; actual data will be returned. Pass --test as argument to run test version instead.")
    is_test = False

app = init_app(is_test)

if __name__ == "__main__":
    app.run(host='127.0.0.1')