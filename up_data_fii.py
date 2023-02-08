import mariadb
import time
import datetime
import smtplib, ssl
import pandas as pd # Para evitar escrever pandas e trocar pela escrita apenas de pd para facilitar
from pandas_datareader import data as web # Evita a escrita do data e troca pelo web
from selenium import webdriver
from bs4 import BeautifulSoup

one_day = 60*60*24
now = datetime.datetime.now()
def natozero(na):
    if na == 'N/A':
        return '0'
    else:
        return na
def isCorr (dic):   ## função para verificar se os dados estão corretos
    incorr = []
    for i in dic:
        if i == '' or i == '-' or i == '\n-':
            incorr.append(i)
    if len(incorr) > 0:
        for j in incorr:
            return j + ' is incorrect'  ## retornar o valor da variavel incorreta
    else:
        return True


def converComTD(strin):          ## função para transformar string com virgula in float
    wtt_dot = strin.replace('.', '')
    wtt_com = wtt_dot.replace(',', '.')
    wtt_perc = wtt_com.replace('%', '')
    wtt_rs = wtt_perc.replace('R$ ', '')
    conv = float(wtt_rs)
    return conv


def exec():
    if isCorr(dados):  ## verificando se os dados estão corretos
        val = (dados[0], dados[1], converComTD(natozero(dados[2])), converComTD(natozero(dados[3])),
               converComTD(natozero(dados[4])), converComTD(natozero(dados[16])),
               converComTD(natozero(dados[17])), converComTD(natozero(dados[23])),
               converComTD(natozero(dados[24])), converComTD(natozero(dados[25])))
        sql = """INSERT INTO fiib3 (codigo, setor, preco, liqDiaria, dividendo, patLiq, vpa, vacFis, vacFin,
                qtd) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        mycursor.execute(sql, val)
        mydb.commit()
        print(mycursor.rowcount, f"record inserted. vales {val}")

def execday():
    if isCorr(dados): ## verificando se os dados estão corretos
        val = (dados[0], converComTD((natozero(dados[2]))), converComTD(natozero(dados[3])))
        sql = """INSERT INTO fiib3daily (cod, cot, liqDiaria) VALUES (%s, %s, %s)""".encode('utf-8')
        mycursor.execute(sql, val)
        mydb.commit()
        print(mycursor.rowcount, f"record inserted into fiib3daily. vales {val}".encode('utf-8'))

mydb = mariadb.connect(
        host="localhost",
        user="root",
        password=None,
        database="invest"
      )
mycursor = mydb.cursor()

driver = webdriver.Chrome("C:\Program Files\Google\Chrome\Application\chromedriver_win32\chromedriver.exe")

driver.get("https://www.fundsexplorer.com.br/ranking")
content = driver.page_source
soup = BeautifulSoup(content)
#           Montando a lista de empresas                #
empresas = []
for a in soup.findAll('td', 'sorting_1'):
    element = a.find('a')
    if empresas.count(a.text) != True:  ## veridicando se o codiogo do fundo ja enta na lista
        empresas.append(a.text)


for tbody in soup.find('table', id='table-ranking').find('tbody'):
    dados = []
    for row in tbody:
        if hasattr(row, 'text') and row.text != '\n':
            dados.append(row.text)
    if len(dados) > 0:
        sql = f"SELECT MAX(ultAt) FROM fiib3 WHERE codigo = '{dados[0]}'"  ## buscando o ultimo balanço das empresas no db
        mycursor.execute(sql)
        result = mycursor.fetchall()
        result = result[0][0] ## tornando result em uma variavel
        if result == None:
            result = datetime.datetime.strptime('1970-01-01', '%Y-%m-%d')
        month_at = result.month
        year_at = result.year
        month_now = now.month
        year_now = now.year
        if year_now == year_at and month_now > month_at: ## verificando se o mes atual não é o mesmo do mes da ultima atualização
            exec()      # função para executar a inserção no banco de dados
        elif month_at >= month_now and year_now != year_at:
            exec()      # função para executar a inserção no banco de dados
        else:
            print(f"\n\n{dados[0]} ja foi atualizado esse mes, portanto nenhuma alteração foi feita")
        print('''\
Verificando se a cotação e liquidez diária já estão atualizadas no db fiib3daily
                ''')
        sql = f"SELECT MAX(ultAt) FROM fiib3daily WHERE cod = '{dados[0]}'"  ## buscando a ultima atualização no db
        mycursor.execute(sql)
        result = mycursor.fetchall()
        result = result[0][0]  ## tornando result em uma variavel
        if result == None:
            result = datetime.datetime.strptime("1970-01-01", '%Y-%m-%d')
        dif_at = now.date() - result.date()
        today = now.weekday()
        if dif_at.days > 0 and 0 < today < 6:
            execday()  # função para executar a incerção no db daily
        elif today == 0 and dif_at >= 3:
            execday()  # função para executar a incerção no db daily
        elif today == 6 and dif_at >= 1:
            execday()  # função para executar a incerção no db daily
        else:
            print("Cotação e liuidez já estão atualizadas!")
