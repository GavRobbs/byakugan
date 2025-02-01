import subprocess

if __name__ == "__main__":
    answered = False
    choice = 0
    while not answered:
        result = str(input("Do you want to just (S)hutdown Byakugan or (C)lean everything, including removing Docker images? ")).lower()

        if result in ['s', 'c']:
            choice = 1 if result == 's' else 2
            answered = True
        else:
            print("Please enter either 'S' or 'C'. ")        

    if choice == 1:
        subprocess.run(["docker", "compose", "down"], check=True)
        print("Byakugan shutdown")
    elif choice == 2:
        subprocess.run(["docker", "compose", "down", "--volumes"], check=True)
        subprocess.run(["docker", "rmi", "byakugan-byakugan"], check=True)
        print("The current instance of Byakugan was shut down.")
        print("All the associated volumes and images for Byakugan were removed.")
