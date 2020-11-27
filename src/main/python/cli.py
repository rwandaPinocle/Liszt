from database import Database

if __name__ == '__main__':
    db = Database()
    while True:
        command = input(f'({db.runCommand("where")})> ')
        if command == 'exit':
            break
        try:
            print(db.runCommand(command))
        except Exception as e:
            print('Invalid input')
            print(e)
