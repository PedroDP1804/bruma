from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
#from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
import ctypes
from twilio.rest import Client
from dotenv import dotenv_values



## ========================================================= ##
#                            Iniciar
## ========================================================= ##

# Config chrome driver
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)
wait = WebDriverWait(driver, 3)
actions = ActionChains(driver)

# Configs gerais
env = dotenv_values(".env")
usuario = env["sigaa_usuario"]
senha = env["sigaa_senha"]
mandar_mensagem = True if (env["mandar_mensagem"] == "sim") else False
abrir_janela = True if (env["abrir_janela"] == "sim") else False

materias_de_interesse = {
        "ENE0306":  {
                        "nome":"PRINCÍPIOS DE COMUNICAÇÃO",
                        "turmas":
                            [
                                {"turma":"02", "professor":"TESTE", "confirmacao":True},
                            ],
                    }

        # "LABORATÓRIO DE ELETRÔNICA": [
        #     {"turma":"01", "professor":"ADSON FERREIRA DA ROCHA", "matricular":0},
        # ],

}



## ========================================================= ##
#                          Funções
## ========================================================= ##


# ----------------------------------- #
def mandarMensagem(texto):

    client = Client(env["twilio_sid"], env["twilio_auth"])
    try:
        client.messages.create(
            from_=f'whatsapp:{env["twilio_sender"]}',
            body=texto,
            to=f'whatsapp:{env["twilio_receiver"]}'
        )

    except Exception as e:
        print(e)
# ----------------------------------- #


# ----------------------------------- #
def janela(titulo:str, texto:str):
    ctypes.windll.user32.MessageBoxW(0, texto, titulo, 0)
# ----------------------------------- #


# ----------------------------------- #
def notificar(departamento, materia, index):
    
    turma = materias_de_interesse[departamento][materia][index]

    texto = f"A matéria {materia} tem vagas com o(a) professor(a) {turma['professor']}!!"
    texto1 = f">>{turma['msgs_enviadas'] + 1}º Aviso: A matéria {materia} tem vagas com o(a) professor(a) {turma['professor']}!!"
    
    if turma["msgs_enviadas"] == 2:
        texto1 += "\n\nLimite de 3 mensagens enviadas atingido. Não serão mais enviadas mensagens desta matéria."

    if turma["msgs_enviadas"] <= 2 and mandar_mensagem:
        materias_de_interesse[departamento][materia][index]["msgs_enviadas"] += 1
        mandarMensagem(texto1)

    else:
        print("Limite de 3 mensagens excedido.")

    if abrir_janela:
        janela("Vaga Encontrada!", texto)
    
    print(f" >>{texto}")
# ----------------------------------- #


# ----------------------------------- #
def confirmarMatricula():
    pass
# ----------------------------------- #




## ========================================================= ##
#                       Primeiro acesso
## ========================================================= ##

# abrir o sigaa
driver.get("https://sigaa.unb.br/sigaa")
wait.until(lambda d: d.execute_script("return document.readyState") == "complete")

# fazer login
input = driver.find_element(By.ID, "username")
input.clear()
input.send_keys(usuario)

input = driver.find_element(By.ID, "password")
input.clear()
input.send_keys(senha)

botao = wait.until(
    EC.element_to_be_clickable((By.NAME, "submit"))
)
botao.click()

# pular comunicados, se tiver
while 1:
    try:
        continuar = driver.find_element(By.NAME, "j_id_jsp_933481798_1:j_id_jsp_933481798_3")
        if continuar.get_attribute("value") == "Continuar >>":
            continuar.click()
            time.sleep(0.5)
    except NoSuchElementException as e:
        print(e.msg)
        break

# aceitar cookies
try:
    botao = driver.find_element(By.ID, "sigaa-cookie-consent").find_element(By.TAG_NAME, "button")
    if botao.text == "Ciente":
        botao.click()
        time.sleep(0.1)

except NoSuchElementException as e:
    print(e.msg)

# Ensino >
menus = driver.find_elements(By.CLASS_NAME, "ThemeOfficeMainItem")
for menu in menus:
    if menu.find_element(By.CLASS_NAME, "ThemeOfficeMainFolderText").text == "Ensino":
        actions.move_to_element(menu).perform()
        break
time.sleep(0.5)

# Matrícula On-Line >
menus = driver.find_element(By.ID, "cmSubMenuID1").find_elements(By.CLASS_NAME, "ThemeOfficeMenuItem")
for menu in menus:
    try:
        texto = menu.find_element(By.CLASS_NAME, "ThemeOfficeMenuFolderText").text
        if texto == "Matrícula On-Line":
            actions.move_to_element(menu).perform()
            break
    except NoSuchElementException:
        continue
time.sleep(0.5)

# > Realizar Matrícula Extraordinária
menus = driver.find_element(By.ID, "cmSubMenuID3").find_elements(By.CLASS_NAME, "ThemeOfficeMenuItem")
for menu in menus:
    try:
        texto = menu.find_element(By.CLASS_NAME, "ThemeOfficeMenuItemText").text
        if texto == "Realizar Matrícula Extraordinária":
            menu.click()
            break
    except NoSuchElementException:
        continue
time.sleep(0.5)




## ========================================================= ##
#                       Loop principal
## ========================================================= ##

for materia_de_interesse in materias_de_interesse.keys():

    nome_materia_interesse = materias_de_interesse[materia_de_interesse]["nome"]

    input = wait.until(
        EC.element_to_be_clickable((By.ID, "form:txtCodigo"))
    )
    input.clear()
    input.send_keys(materia_de_interesse)

    botao = driver.find_element(By.ID, "form:buscar")
    botao.click()
    time.sleep(0.5)

    menus = driver.find_elements(By.TAG_NAME, "tbody")
    for menu in menus:
        try:
            # confirmar se é a matéria correta
            botao = menu.find_element(By.TAG_NAME, "a")
            if not (
                (materia_de_interesse in botao.text) and (nome_materia_interesse in botao.text)
            ):
                continue

            # turmas desejadas em formato ["01", "02"...]
            turmas_de_interesse:list = list(map(
                lambda m : m["turma"],
                materias_de_interesse[materia_de_interesse]["turmas"]
            ))

            # iterar pelas turmas encontradas
            try:
                turmas = menu.find_elements(By.TAG_NAME, "tr")
                for turma in turmas:

                    # pular cabeçalhos de matérias
                    if not ("turma" in turma.get_attribute("id")):
                        continue

                    # verificar turma
                    desejada = False
                    infos = turma.find_elements(By.TAG_NAME, "td")
                    for info in infos:

                        # Pula campos que não sejam "Turma XX"
                        texto = info.text
                        if not "Turma" in texto:
                            continue

                        # Verifica se a turma é desejada
                        for turma_de_interesse in turmas_de_interesse:
                            if texto == f"Turma {turma_de_interesse}":
                                desejada = True

                    if not desejada:
                        continue

                    # Selecionar turma
                    botao = turma.find_element(By.CSS_SELECTOR, "a[title='Selecionar turma']")
                    botao.click()
                    time.sleep(0.5)
                    confirmarMatricula()
                                


            except NoSuchElementException:
                print(f"Sem turmas encontradas para {nome_materia_interesse}")


        except NoSuchElementException as e:
            # print(e.msg)
            continue



    time.sleep(5)




# janela("Sucesso!", "Foi caralho!!!")



# a = driver.find_element(By.ID, "cmSubMenuID3")
# opcoes = a.find_elements(By.TAG_NAME, "tr")
# for opcao in opcoes:
#     botao = opcao.find_element(By.CLASS_NAME, "ThemeOfficeMenuItemText")
#     if botao.get_attribute("textContent") == "Realizar Matrícula":
#         driver.execute_script("arguments[0].click();", opcao)
# time.sleep(5)













# # escolher Nível de Ensino
# nivel = wait.until(
#     EC.element_to_be_clickable((By.ID, "formTurma:inputNivel"))
# )
# nivel.click()
# time.sleep(0.5)

# opcoes = nivel.find_elements(By.TAG_NAME, "option")
# for opcao in opcoes:
#     if opcao.text == "GRADUAÇÃO":
#         opcao.click()
#         time.sleep(0.5)
#         break



## ========================================================= ##
#                       Loop principal
## ========================================================= ##

# while True:
#     try:
#         os.system("cls") # limpar terminal

#         # percorrer departamentos das materias de interesse
#         for departamento in turmas_de_interesse.keys():

#             # escolher Unidade (departamento)
#             unidade = wait.until(
#                 EC.element_to_be_clickable((By.ID, "formTurma:inputDepto"))
#             )
#             unidade.click()
#             time.sleep(0.5)

#             opcoes = unidade.find_elements(By.TAG_NAME, "option")
#             for opcao in opcoes:
#                 if departamento in opcao.text:
#                     opcao.click()
#                     time.sleep(0.5)
#                     break

#             # clicar em Buscar
#             buscar = wait.until(
#                 EC.element_to_be_clickable((By.NAME, "formTurma:j_id_jsp_1370969402_11"))
#             )
#             buscar.click()
#             wait.until(
#                 EC.presence_of_element_located((By.ID, "turmasAbertas"))
#             )

#             # percorrer turmas de interesse
#             linhas = wait.until(EC.visibility_of_all_elements_located((By.TAG_NAME, "tr")))
#             length = len(linhas)

#             i = 0
#             while i < length:
#                 try:
#                     nome_da_materia = linhas[i].find_element(By.CLASS_NAME, "tituloDisciplina").text

#                     for materia in turmas_de_interesse[departamento].keys():
#                         if materia in nome_da_materia:

#                             i += 1
#                             turmas_sigaa = [linhas[i]]

#                             while (i+1 < length) and ( linhas[i+1].get_attribute("class") in ["linhaPar", "linhaImpar"] ):
#                                 turmas_sigaa.append(linhas[i+1])
#                                 i += 1

#                             for turma_sigaa in turmas_sigaa:
#                                 numero_da_turma = turma_sigaa.find_element(By.CLASS_NAME, "turma").text

#                                 for index, turma_de_interesse in enumerate(turmas_de_interesse[departamento][materia]):
#                                     if ( turma_de_interesse["turma"] in numero_da_turma ):

#                                         vagas = turma_sigaa.find_elements(By.CSS_SELECTOR, "[style='text-align: center;']")

#                                         print(f"{materia} está com {vagas[1].text}/{vagas[0].text} vagas preenchidas na turma {turma_de_interesse['turma']} com o professor {turma_de_interesse['professor']}")

#                                         if int(vagas[1].text) < int(vagas[0].text):

#                                             notificar(departamento, materia, index)

#                                         elif turma_de_interesse["msgs_enviadas"] > 0:

#                                             turmas_de_interesse[departamento][materia][index]["msgs_enviadas"] = 0
                        
#                 except NoSuchElementException:
#                     continue

#                 finally:
#                     i += 1

#         try:
#             tempo = 5
#             print(f"Esperando {tempo} segundos até a próxima iteração.\nAperte Ctrl + C para encerrar o programa.")
#             time.sleep(tempo)

#         except KeyboardInterrupt:
#             print("Encerrando o programa...")
#             driver.quit()
#             print("Programa finalizado.")
#             break

#     except Exception as e:
#         t_msg = time.strftime("<!> O sistema parou de funcionar às %H:%M:%S.", time.localtime())
#         print(t_msg)

#         if mandar_mensagem:
#             mandarMensagem("Aviso!\n" + t_msg)

#         if abrir_janela:
#             janela("Sistema Fora do Ar!", t_msg)
            
#         print("\nExceção:\n", e)
#         break