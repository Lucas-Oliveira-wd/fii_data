import pandas as pd # Para evitar escrever pandas e trocar pela escrita apenas de pd para facilitar
from pandas_datareader import data as web # Evita a escrita do data e troca pelo web
import time
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def verMaxDate(date,vals): ## função para retornar a date que ocorreu o valor minimo
    for i in range(len(vals)):
        if vals[i] == max(vals):
            return date[i]


data_final = time.strftime('%m-%d-%y', time.localtime(time.time()))
##  criando a data inicial (3 meses)
one_day = 60*60*24
interval = 3 ## intervalo de tempo em meses

data_inicial = time.strftime('%m-%d-%y', time.localtime(time.time()-interval*30*one_day))

msg_aval_since = """\
Procurando por uma janela de oportunidade de compra para os fundos da planilha 'fiis.xlsx'.
Desde a data {}(Mês-Dia-Ano) até agr
"""
print(msg_aval_since.format(data_inicial))

empresas_df = pd.read_excel("fiis.xlsx")

for empresa in empresas_df['fiis']:
    df = web.DataReader(f'{empresa}.SA', data_source='yahoo', start=data_inicial, end=data_final)

    var = ((df["Adj Close"][len(df["Adj Close"])-1]) - max(df["Adj Close"]))/max(df["Adj Close"])
    wind = -0.1 # valor para janela de oportunidade

    dates = [] ## para conter as datas
    vals = []  ## para conter os valores

    for i in df.index:
        dates.append(i)
    for i in df["Adj Close"]:
        vals.append(i)

    if var < wind:

        sender_email = "emailautomatico11@gmail.com"     # Enter your address
        receiver_email = "lucasoliveira5978@gmail.com"      # Enter receiver address
        password = "nucxkwaaqoazgnxh"
        message = MIMEMultipart("alternative")
        message["Subject"] = f"!Oportunidade de compra de: {empresa}!"
        message["From"] = sender_email
        message["To"] = receiver_email

        # Create the plain-text and HTML version of your message
        msg = """\
        Há uma janela de oportunidade de compra para {0}.
        O fundo caiu mais de {1} % nos últimos {2} meses
        """

        text = msg.format(empresa, wind*-100, interval)

        msg = """\
        <html>
            <head>
                <link rel="preconnect" href="https://fonts.googleapis.com">
                <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                <link href="https://fonts.googleapis.com/css2?family=Space+Mono&display=swap" rel="stylesheet">
                <title>Email automático</title>                
            </head>
            <body style="text-align: center; padding: 50px 20px; font-size: 20px; background-color: #333;
                    border-top: 4px solid #666; color: #fff;">
                <h3 style="background-color: rgb(172, 204, 172); max-width: max-content; margin: 0 auto;
                padding: 10px 30px; border-radius: 5px; border: 3px solid rgb(16, 80, 16);
                    color: rgb(13, 39, 13); font: normal normal bold 30px/30px Space Mono;
                    text-shadow: 3px 2px 4px #00000099;">
                        Há uma janela de oportunidade de compra: {0} </h3>
                    <div style='background-color: rgb(39, 163, 39); max-width: 150px; padding: 10px 50px;
                    margin: 30px auto; font-size: 25px; border-radius: 60px; color: rgb(0, 0, 0);'>
                    <b>{0}</b> </div>
                <p> O fundo estava cotada no valor de <b> R$ {1} </b> no dia <b> {2}</b>,</p>
                <p> hoje está cotada no valor de <b>R$ {3}</b>,</p>
                <p style=' border-bottom: 4px solid #666; color: #fff; padding: 10px 0 150px;
                    text-shadow: 3px 2px 4px #00000099;'>
                    <b>Uma queda de {4} %</b></p>
            </body>
        </html>
        """

        html = msg.format(empresa, round(max(df["Adj Close"]), 2), str(verMaxDate(dates, vals))[0:10],
                          round(df["Adj Close"][len(df["Adj Close"])-1], 2), round(-var*100,2))

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
        msg = "Fundo {} analisado. Sem oportunidade"
        print(msg.format(empresa))
