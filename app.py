import os
import csv
from datetime import datetime
from cadastro import cadastrar_pessoa
from verificar import verificar_acesso

def registrar_log(nome, status):
    os.makedirs("logs", exist_ok=True)
    arquivo_log = "logs/acessos.csv"
    arquivo_existe = os.path.isfile(arquivo_log)

    with open(arquivo_log, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not arquivo_existe:
            writer.writerow(["data_hora", "nome", "status"])

        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), nome, status])

def menu():
    while True:
        print("\n=== CONTROLE DE ACESSO FACIAL ===")
        print("1 - Cadastrar pessoa")
        print("2 - Verificar acesso")
        print("3 - Sair")

        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            nome = input("Digite o nome da pessoa: ").strip()
            if nome:
                cadastrar_pessoa(nome)
            else:
                print("Nome inválido.")

        elif opcao == "2":
            nome, autorizado = verificar_acesso()

            if autorizado:
                print(f"Acesso liberado para: {nome}")
                registrar_log(nome, "LIBERADO")
            else:
                print("Acesso negado.")
                registrar_log("Desconhecido", "NEGADO")

        elif opcao == "3":
            print("Encerrando sistema.")
            break

        else:
            print("Opção inválida.")

if __name__ == "__main__":
    menu()