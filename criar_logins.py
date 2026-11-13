from werkzeug.security import generate_password_hash
import banco


def main():
    conn = banco.conectar_banco()
    try:
        for papel in ("admin", "comum"):
            if banco.buscar_login(conn, papel) is not None:
                continue
            senha = input(f"Defina a senha local de {papel} (entrada visível): ")
            if not senha.strip():
                raise ValueError("Informe uma senha.")
            banco.criar_login(conn, papel, generate_password_hash(senha), papel)
        conn.commit()
        print("Logins disponíveis.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
