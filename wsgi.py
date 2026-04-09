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
    # Tekeleza ulinzi wa akaunti
    secure_admin_setup()
    
    print("--- [ LOGS ] ---")
    print("Starting CTFd Development Server...")
    print("Access locally at http://0.0.0.0:4000")
    
    # Inawaka kwenye debug mode kwa ajili ya maendeleo (Development)
    app.run(debug=True, threaded=True, host="0.0.0.0", port=4000)