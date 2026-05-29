import os
from CTFd import create_app
from CTFd.models import Users, db
from CTFd.utils.crypto import hash_password

app = create_app()

def secure_admin_setup():
    with app.app_context():
        # Maelezo ya akaunti yako
        email = "frankkarani280@gmail.com"
        username = "RootMaster_Frank"
        
        # CHAGUO: Unaweza kuandika password hapa au kuitolea kwenye environment variable
        # Kwa usalama zaidi, itumie hivi: os.environ.get("ADMIN_PASS", "Z3ro-Day-Expl0it_Admin")
        password = "Z3ro-Day-Expl0it_Admin"

        # Tafuta kama mtumiaji yupo
        user = Users.query.filter_by(email=email).first()

        if user:
            # Kama yupo, tunahakikisha ana sifa za Admin na Password mpya
            user.type = "admin"
            user.name = username
            user.password = hash_password(password)
            db.session.commit()
            print(f"[*] Mamlaka ya ADMIN yameimarishwa kwa: {email}")
        else:
            # Kama hayupo (kwa mfano database ni mpya), tunamtengeneza
            new_admin = Users(
                name=username,
                email=email,
                password=hash_password(password),
                type="admin"
            )
            db.session.add(new_admin)
            db.session.commit()
            print(f"[+] Akaunti mpya ya ADMIN imetengenezwa kwa: {email}")

if __name__ == "__main__":
    # Tekeleza ulinzi wa akaunti pekee
    secure_admin_setup()
    print("[*] Usanidi wa akaunti ya ADMIN umekamilika kikamilifu kwenye Database!")
