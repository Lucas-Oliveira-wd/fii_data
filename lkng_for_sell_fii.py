import pandas as pd # Para evitar escrever pandas e trocar pela escrita apenas de pd para facilitar
from pandas_datareader import data as web # Evita a escrita do data e troca pelo web
import time
import datetime
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mariadb

def verMinDate(date,vals): ## função para retornar a date que ocorreu o valor minimo
    for i in range(len(vals)):
        if vals[i] == min(vals):
            return date[i]

data_final = time.strftime('%m-%d-%y', time.localtime(time.time()))
##  criando a data inicial (3 meses)
one_day = 60*60*24
interval = 6 ## intervalo de tempo em meses

data_inicial = time.strftime('%m-%d-%y', time.localtime(time.time()-interval*30*one_day))
data_inicial = datetime.datetime.strptime(data_inicial, '%m-%d-%y')  ##definindo a data inicial

msg_aval_since = """\
Procurando por uma janela de oportunidade de venda para os fundos da planilha 'paricipacao.xlsx'.
Desde a data {}(Mês-Dia-Ano) até agr
"""
print(msg_aval_since.format(data_inicial))

empresas_df = ('BNFS11', 'BBPO11')  # FIIs na carteira)

#conectando com o banco de dados
mydb = mariadb.connect(
	host="localhost",
	user="root",
	password=None,
	database="invest"
)
mycursor = mydb.cursor()


for empresa in empresas_df:
    # montando a lista para conter os dados dos fiis
    sql = f"SELECT cot, ultInsert FROM fiib3daily WHERE cod = '{empresa}' ORDER BY ultInsert"  ## buscando o
    # ultimo balanço das empresas no db
    mycursor.execute(sql)
    result = mycursor.fetchall()
    cot_dados = []  # para conter os dados das cotações

    for r in result:
        if r[1] >= data_inicial:  # filtrando as datas acima da inicial
            cot_dados.append(r)

    df = pd.DataFrame(cot_dados, columns=('cotacao', 'data'))  # defininco o data frame

    if len(df['cotacao']) > 1:  # verificando se tem pelo menos mais de 2 valores para a cotação
        var = ((df['cotacao'].iloc[len(df['cotacao']) - 1]) - min(df['cotacao']))/min(df['cotacao'])

    wind = 0.2 # valor para janela de oportunidade

    if var > wind:

        sender_email = "emailautomatico11@gmail.com"  # Enter your address
        receiver_email = "lucasoliveira5978@gmail.com"  # Enter receiver address
        password = "nucxkwaaqoazgnxh"
        message = MIMEMultipart("alternative")
        message["Subject"] = f"!Oportunidade de venda de FII {empresa}"
        message["From"] = sender_email
        message["To"] = receiver_email

        # Create the plain-text and HTML version of your message
        msg = """\
                Há uma janela de oportunidade de venda para {0}.
                O fundo subiu mais de {1} % nos últimos {2} meses
                """

        text = msg.format(empresa, round(min(df["Adj Close"]), 2), str(verMinDate(dates,vals))[0:10],
                          round(df["Adj Close"][len(df["Adj Close"])-1], 2), round(var*100,2))

        msg = """\
        <html>
            <body style="text-align: center; background-color: #000; padding: 50px 20px; font-size: 20px; color: yellow;">
                <h3 style="background-color: rgb(6, 4, 27); max-width: max-content; margin: 0 auto; padding: 10px 30px;
                    border: 3px solid yellow; font-weight: 700;"> Há uma janela de oportunidade de venda para: </h3>
                    <div style='background-color: #000; max-width: 110px; padding: 10px 50px;
                    margin: 30px auto; font-size: 25px; border: 3px solid yellow;'>
                    <b>{0}</b> </div>
                <p style="color: #000; color: #ccc;"> O fundo estava cotado no valor de <b> R$ {1} </b> no dia <b> {2}</b>,</p>
                <p style="color: #000; color: #ccc;"> hoje está cotado no valor de <b>R$ {3}</b>,</p>
                <p style='border-bottom: 2px solid rgb(51, 57, 75); color: #fff; font-weight: 600; padding: 10px 0; margin: 20px auto;'>
                    <b>Uma subida de {4} %</b></p>
            </body>
          </html>
                """

        html = msg.format(empresa, round(max(df["cotacao"]), 2), str(verMinDate(df['data'], df['cotacao']))[0:10],
                          round(df["cotacao"].iloc[len(df["cotacao"])-1], 2), round(-var*100,2))

        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)

        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(
                sender_email, receiver_email, message.as_string().encode('utf-8')
            )
    else:
        msg = "Empresa {} analisado. Sem oportunidade"
        print(msg.format(empresa))

