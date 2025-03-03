from sys import argv

if len(argv) > 0:
    flag = argv[1]

# Return hardcoded test JSON data
if flag == "--test":
    print("Running test version of API; hardcoded JSON will be returned from calls.")
    from apitest_init import init_app

# Return actual database data
else:
    print("Running non-test API; actual data will be returned. Pass --test as argument to run test version instead.")
    from __init__ import init_app

app = init_app()

if __name__ == "__main__":
    app.run(host='127.0.0.1')