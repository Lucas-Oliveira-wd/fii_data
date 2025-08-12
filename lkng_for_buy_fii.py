import pandas as pd
import time
import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import mariadb
import locale

# --- CONFIGURAÇÃO INICIAL ---

# Configura o locale para formatação em Reais (R$). Essencial para o e-mail.
# Se o comando abaixo der erro no seu sistema, tente 'pt_BR' ou 'Portuguese_Brazil.1252'
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    print("Locale 'pt_BR.UTF-8' não encontrado. Tentando outros. A formatação de moeda no e-mail pode ser afetada.")
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            print(
                "Não foi possível configurar um locale em português. A formatação de moeda usará o padrão do sistema.")


def encontrar_indice_maximo(dataframe, coluna_valor):
    """Retorna o índice da linha que contém o valor máximo de uma coluna."""
    return dataframe[coluna_valor].idxmax()


# Define o intervalo de tempo para a análise (em meses)
interval = 3
one_day = 60 * 60 * 24
data_inicial_dt = datetime.datetime.now() - datetime.timedelta(days=interval * 30)

print(f"Iniciando análise de oportunidades...")
print(f"Período considerado: de {data_inicial_dt.strftime('%d/%m/%Y')} até hoje.\n")

# --- CONEXÃO COM O BANCO DE DADOS ---

try:
    mydb = mariadb.connect(
        host="localhost",
        user="root",
        password=None,
        database="invest"
    )
    mycursor = mydb.cursor()
    print("Conexão com o banco de dados estabelecida com sucesso.")
except mariadb.Error as e:
    print(f"Erro ao conectar com o MariaDB: {e}")
    exit()  # Encerra o script se não conseguir conectar ao DB

# --- LÓGICA PRINCIPAL ---

empresas_df = pd.read_excel("fiis.xlsx")

for empresa in empresas_df['fiis']:

    print(f"Analisando o fundo: {empresa}...")

    # Busca os dados do FII no banco de dados
    sql = f"SELECT cot, nCotas, ultInsert FROM fiib3daily WHERE cod = ? ORDER BY ultInsert"
    mycursor.execute(sql, (empresa,))
    result = mycursor.fetchall()

    # Filtra os dados para o período de tempo desejado
    cot_dados = [r for r in result if r[2] >= data_inicial_dt]

    if not cot_dados:
        print(f"Fundo {empresa} não possui nenhum dado no período de análise.\n")
        continue

    df_bruto = pd.DataFrame(cot_dados, columns=('cotacao', 'n_cotas', 'data'))

    # 1. LIMPEZA DOS DADOS: Cria um novo DataFrame apenas com as linhas onde o número de cotas é válido (maior que 0).
    df = df_bruto[df_bruto['n_cotas'] > 0].copy()

    # Prossegue apenas se houver dados válidos suficientes para analisar
    if len(df) > 1:

        # 2. OBTENÇÃO SEGURA DO NÚMERO DE COTAS ATUAL: Pega o número de cotas da última linha VÁLIDA.
        ncotas_atual = df['n_cotas'].iloc[-1]

        # 3. AJUSTE DE PREÇOS: Aplica sua fórmula para normalizar os preços históricos
        df['preco_ajustado'] = df['cotacao'] * (df['n_cotas'] / ncotas_atual)

        # 4. ANÁLISE DA VARIAÇÃO
        preco_atual = df['cotacao'].iloc[-1]
        max_preco_ajustado = df['preco_ajustado'].max()

        if max_preco_ajustado > 0:
            var = (preco_atual - max_preco_ajustado) / max_preco_ajustado
        else:
            var = 0

        # Define o gatilho de oportunidade (queda de 10%)
        wind = -0.1

        if var < wind:
            # 5. ENVIO DE E-MAIL: Oportunidade encontrada
            print(f"--> Oportunidade encontrada para {empresa}! Preparando e-mail...")

            sender_email = "emailautomatico11@gmail.com"
            receiver_email = "lucasoliveira5978@gmail.com"
            password = "nucxkwaaqoazgnxh"

            message = MIMEMultipart("alternative")
            message["Subject"] = f"!Oportunidade de compra de: {empresa}!"
            message["From"] = sender_email
            message["To"] = receiver_email

            # Obtém os dados para o corpo do e-mail
            idx_max = encontrar_indice_maximo(df, 'preco_ajustado')
            preco_historico_max_original = df.loc[idx_max, 'cotacao']
            data_max = df.loc[idx_max, 'data']

            # Versão em texto puro
            text = f"""
            Alerta de Oportunidade de Compra para {empresa}!

            Após ajuste pela variação no número de cotas, o fundo apresenta uma queda de {round(-var * 100, 2)}% nos últimos {interval} meses.

            - Preço máximo (original) no período: {locale.currency(preco_historico_max_original, grouping=True)} em {data_max.strftime('%d/%m/%Y')}.
            - Preço atual: {locale.currency(preco_atual, grouping=True)}.
            """

            # Versão em HTML
            html = f"""
            <html>
                <head>
                    <link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
                    <title>Alerta de Oportunidade FII</title>                
                </head>
                <body style="text-align: center; padding: 40px 20px; font-size: 18px; background-color: #2c2c2c;
                        color: #f0f0f0; font-family: 'Space Mono', monospace;">
                    <div style="max-width: 600px; margin: auto; background-color: #333; border-radius: 8px; overflow: hidden;">
                        <div style="background-color: #22c55e; color: #14532d; padding: 20px;">
                            <h2 style="margin: 0; font-size: 28px;">
                                Oportunidade de Compra: {empresa}
                            </h2>
                        </div>
                        <div style="padding: 30px;">
                            <p style="font-size: 22px;">
                                O preço máximo original foi de <b>{locale.currency(preco_historico_max_original, grouping=True)}</b><br>
                                <span style="font-size: 16px;">em {data_max.strftime('%d/%m/%Y')}</span>
                            </p>
                            <p style="font-size: 22px;">
                                Hoje, a cotação está em <b>{locale.currency(preco_atual, grouping=True)}</b>.
                            </p>
                            <div style="background-color: #444; padding: 20px; border-radius: 8px; margin-top: 30px;">
                                <p style="margin: 0; font-size: 24px; color: #f87171; font-weight: bold;">
                                    Queda de {round(-var * 100, 2)}%
                                </p>
                                <p style="margin: 5px 0 0; font-size: 14px; color: #a1a1aa;">
                                    (percentual calculado após ajuste pela variação de cotas)
                                </p>
                            </div>
                        </div>
                    </div>
                </body>
            </html>
            """

            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)

            context = ssl.create_default_context()
            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(sender_email, password)
                    server.sendmail(
                        sender_email, receiver_email, message.as_string().encode('utf-8')
                    )
                print(f"--> E-mail de oportunidade para {empresa} enviado com sucesso!\n")
            except Exception as e:
                print(f"--> ERRO ao enviar e-mail para {empresa}: {e}\n")

        else:
            print(f"Fundo {empresa} analisado. Nenhuma oportunidade encontrada.\n")
    else:
        print(f"Fundo {empresa} não possui dados válidos suficientes no período para análise.\n")

print("Análise concluída para todos os fundos.")
mycursor.close()
mydb.close()