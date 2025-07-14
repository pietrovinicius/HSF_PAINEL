#AND APV.CD_SETOR_ATENDIMENTO = 64
# PAI - U.I. 1º ANDAR
'''
64   PAI - U.I. 1? ANDAR
65   PAI - U.I. 2? ANDAR
66   PAI - U.I. 3? ANDAR
110  LAR SANTA CLARA
208  PAI - U.I 2? ANDAR - ADOLESCENTE
252	 PAI - HOSPITAL DIA
'''


import streamlit as st
import pandas as pd
import numpy as np
import os
import oracledb
import time
import plotly.graph_objects as go
import locale
import datetime

#Configurando pagina para exibicao em modo WIDE:
st.set_page_config(layout="wide",initial_sidebar_state="collapsed",page_title="PAI - U.I. 1º ANDAR ")

def agora():
    agora = datetime.datetime.now()
    agora = agora.strftime("%Y-%m-%d %H-%M-%S")
    return str(agora)

def calcular_altura_dataframe(num_linhas, altura_base=150, altura_por_linha=30, max_altura=925):
            """Calcula a altura apropriada para um DataFrame com base no número de linhas.
                exemplo:
                        #altura_df = calcular_altura_dataframe(df_aguard_ps.shape[0])
                        #st.dataframe(df_aguard_ps, hide_index=True, use_container_width=True, height=altura_df)    
            """
            altura = altura_base + (num_linhas * altura_por_linha)
            return min(altura, max_altura)

#apontamento para usar o Think Mod
def encontrar_diretorio_instantclient(nome_pasta="instantclient-basiclite-windows.x64-23.6.0.24.10\\instantclient_23_6"):
  # Obtém o diretório do script atual
  diretorio_atual = os.path.dirname(os.path.abspath(__file__))

  # Constrói o caminho completo para a pasta do Instant Client
  caminho_instantclient = os.path.join(diretorio_atual, nome_pasta)

  # Verifica se a pasta existe
  if os.path.exists(caminho_instantclient):
    return caminho_instantclient
  else:
    print(f"A pasta '{nome_pasta}' nao foi encontrada na raiz do aplicativo.")
    return None

#@st.cache_data 
def pacientes_escalas():
    try:
        un = 'PIETRO'
        cs = '192.168.5.9:1521/TASYPRD'

        # Chamar a função para obter o caminho do Instant Client
        caminho_instantclient = encontrar_diretorio_instantclient()

        # Usar o caminho encontrado para inicializar o Oracle Client
        if caminho_instantclient:
            #print(f'if caminho_instantclient:\n')
            #print(f'oracledb.init_oracle_client(lib_dir=caminho_instantclient)\n')
            oracledb.init_oracle_client(lib_dir=caminho_instantclient)
        else:
            print("Erro ao localizar o Instant Client. Verifique o nome da pasta e o caminho.")
        
        connection = oracledb.connect( user="TASY", password="aloisk", dsn="192.168.5.9:1521/TASYPRD")
        
        with connection:
            #print(f'with oracledb.connect(user=un, password=pw, dsn=cs) as connection\n')
            
            #print(f'\nconnection.current_schema: {connection.current_schema}')
            
            with connection.cursor() as cursor:
                #print(f'with connection.cursor() as cursor:\n')
                
                #####################################################################################
                #QUERY:
                sql = """ 
                        SELECT 
                        CASE
                        WHEN PA.IE_CLASSIFICACAO IS NOT NULL THEN
                        'SIM'
                        ELSE
                        '-'
                        END ALERGIA,
                        APV.CD_SETOR_ATENDIMENTO AS SETOR_ATENDIMENTO,
                        OBTER_DESC_SETOR_ATEND(APV.CD_SETOR_ATENDIMENTO) AS SETOR,
                        REPLACE(OBTER_LEITO_ATUAL_PAC(APV.NR_ATENDIMENTO), '-', ' ') AS LEITO,
                        APV.NR_ATENDIMENTO AS ATENDIMENTO,
                        SUBSTR(OBTER_NOME_PF(APV.CD_PESSOA_FISICA), 1, 1) ||
                        SUBSTR(ABREVIA_NOME(OBTER_NOME_PF(APV.CD_PESSOA_FISICA), 'A'),  INSTR(ABREVIA_NOME(OBTER_NOME_PF(APV.CD_PESSOA_FISICA), 'A'),
                        ' ')) AS PACIENTE,
                        TO_CHAR(APV.DT_ENTRADA, 'DD/MM/YY HH24:MI') AS ENTRADA,
                        --MEWS
                        (SELECT EM.QT_PONTUACAO AS CLASSIFICACAO
                            FROM ESCALA_MEWS EM, ATENDIMENTO_PACIENTE_V A
                            WHERE A.NR_ATENDIMENTO = EM.NR_ATENDIMENTO
                            AND A.DT_ALTA IS NULL
                            AND A.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                            AND EM.IE_SITUACAO = 'A'
                            ORDER BY EM.DT_AVALIACAO DESC
                            FETCH FIRST 1 ROWS ONLY
                        ) AS MEWS,
                        --BRADEN
                        (SELECT INITCAP(OBTER_RESULTADO_BRADEN(AEB.QT_PONTO))
                            FROM ATEND_ESCALA_BRADEN AEB
                            WHERE (NR_ATENDIMENTO = APV.NR_ATENDIMENTO)
                            AND AEB.IE_SITUACAO = 'A'
                            ORDER BY 1 DESC
                            FETCH FIRST 1 ROWS ONLY
                        ) AS BRADEN,      
                        --MORSE
                        (SELECT INITCAP(OBTER_DESC_ESCALA_MORSE(QT_PONTUACAO))
                            FROM ESCALA_MORSE EMM
                            WHERE EMM.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                            AND EMM.IE_SITUACAO = 'A'
                            ORDER BY 1 DESC
                            FETCH FIRST 1 ROWS ONLY
                        ) AS MORSE,   
                        --SAPS3
                        (SELECT QT_PONTUACAO || ' / ' || PR_RISCO || '%'
                            FROM ESCALA_SAPS3 SAPS3
                            WHERE SAPS3.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                            AND SAPS3.IE_SITUACAO = 'A'
                            ORDER BY 1 DESC
                            FETCH FIRST 1 ROWS ONLY
                        ) AS SAPSIII,
                        --RASS
                        (SELECT CASE
                            WHEN LENGTH(OBTER_VALOR_DOMINIO(2088, IE_RASS)) > 21 THEN
                            SUBSTR(OBTER_VALOR_DOMINIO(2088, IE_RASS), 1, 21) || '...'
                            ELSE
                            OBTER_VALOR_DOMINIO(2088, IE_RASS)
                            END AS DS_AGITACAO_SEDACAO
                            FROM ESCALA_RICHMOND
                            WHERE 1 = 1
                            AND NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                            AND OBTER_SE_REG_LIB_ATENCAO(OBTER_PESSOA_ATENDIMENTO(NR_ATENDIMENTO,'C'),CD_PROFISSIONAL,IE_NIVEL_ATENCAO,NM_USUARIO,374) = 'S'
                            FETCH FIRST 1 ROWS ONLY
                        ) RASS,
                        --CD_RASS
                        (SELECT IE_RASS
                            FROM ESCALA_RICHMOND
                            WHERE 1 = 1
                            AND NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                            AND OBTER_SE_REG_LIB_ATENCAO(OBTER_PESSOA_ATENDIMENTO(NR_ATENDIMENTO,'C'),CD_PROFISSIONAL,IE_NIVEL_ATENCAO,NM_USUARIO,374) = 'S'
                            FETCH FIRST 1 ROWS ONLY
                        ) CD_RASS,      
                        --FUGULIN
                        /*(SELECT 
                                (SELECT
                                --DS_GRADACAO                
                                DECODE(DS_GRADACAO,'CM','CUIDADOS MÍNIMOS','CI','CUIDADOS INTERMEDIÁRIOS','AD','ALTA DEPENDÊNCIA','SI','CUIDADOS SEMI INTENSIVOS','I','CUIDADOS INTENSIVOS',DS_GRADACAO)                
                                FROM GCA_GRADACAO
                                WHERE NR_SEQUENCIA =
                                (SELECT NR_SEQ_GRADACAO
                                FROM GCA_ATENDIMENTO
                                WHERE NR_SEQUENCIA =
                                (SELECT MAX(NR_SEQUENCIA)
                                FROM GCA_ATENDIMENTO
                                WHERE NR_ATENDIMENTO = AP.NR_ATENDIMENTO
                                AND IE_SITUACAO = 'A'
                                AND TRUNC(DT_AVALIACAO) =
                                TRUNC(GCAA.DT_AVALIACAO))))
                            FROM ATENDIMENTO_PACIENTE AP
                            INNER JOIN GCA_ATENDIMENTO GCAA
                            ON GCAA.NR_ATENDIMENTO = AP.NR_ATENDIMENTO
                            INNER JOIN GCA_GRADACAO GCAG
                            ON GCAG.NR_SEQUENCIA = GCAA.NR_SEQ_GRADACAO
                            WHERE GCAA.IE_SITUACAO = 'A'
                            AND AP.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                            ORDER BY GCAA.DT_AVALIACAO DESC
                            FETCH FIRST 1 ROWS ONLY
                            ) AS FUGULIN,
                        */     
                        --MARTINS
                        (SELECT 
                            SUBSTR(OBTER_DESC_RESUL_SCORE_FLEX_2(EEI.QT_PONTOS,EEI.NR_SEQ_ESCALA),1,255)
                            FROM ESCALA_EIF_II EEII
                            INNER JOIN ESCALA_EIF_II EEI
                            ON (EEI.NR_SEQUENCIA = EEII.NR_SEQUENCIA)
                            INNER JOIN SCORE_AVALIACAO_RESULT SAR
                            ON (EEII.NR_SEQUENCIA = SAR.NR_SEQ_AVALIACAO)
                            INNER JOIN MED_ITEM_AVALIAR MIA
                            ON (MIA.NR_SEQUENCIA = SAR.NR_SEQ_ITEM)
                            INNER JOIN MED_TIPO_AVALIACAO MTA
                            ON (MTA.NR_SEQUENCIA = MIA.NR_SEQ_TIPO)
                            WHERE EEII.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                            AND SAR.DS_RESULTADO IS NOT NULL
                            AND EEII.DT_LIBERACAO IS NOT NULL
                            AND UPPER(MTA.DS_TIPO) LIKE '%MARTINS%'
                            AND EEII.IE_SITUACAO = 'A'
                            GROUP BY EEII.DT_AVALIACAO, EEI.QT_PONTOS, EEI.NR_SEQ_ESCALA
                            ORDER BY EEII.DT_AVALIACAO DESC
                            FETCH FIRST 1 ROWS ONLY      
                        ) AS MARTINS,      
                        --GLASGOW (RETORNA TEXTO)
                        (SELECT OBTER_RESULTADO_GLASGOW(AEI.QT_GLASGOW)
                            FROM ATEND_ESCALA_INDICE AEI
                            WHERE OBTER_SE_REG_LIB_ATENCAO(OBTER_PESSOA_ATENDIMENTO(AEI.NR_ATENDIMENTO,'C'),AEI.CD_PESSOA_FISICA,AEI.IE_NIVEL_ATENCAO,AEI.NM_USUARIO,374) = 'S'
                            AND AEI.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                            ORDER BY AEI.DT_AVALIACAO DESC
                            FETCH FIRST 1 ROWS ONLY        
                        ) AS GLASGOW,      
                        --MEDICO RESPONSAVEL
                        INITCAP(ABREVIA_NOME(OBTER_NOME_MEDICO(APV.CD_MEDICO_RESP, 'N'), 'A')) MEDICO_RESPONSAVEL,     
                        (SELECT DISTINCT INITCAP(DS_PRECAUCAO)
                            FROM ATENDIMENTO_PRECAUCAO_V
                            WHERE IE_SITUACAO = 'A'
                            AND DT_INATIVACAO IS NULL
                            AND NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                            ORDER BY DT_REGISTRO DESC
                            FETCH FIRST 1 ROWS ONLY
                        ) PRECAUCAO,     
                        OBTER_GRUPOS_PACIENTE(APV.NR_ATENDIMENTO, APV.CD_PESSOA_FISICA) GRUPOS_PACIENTE,      
                        TO_CHAR(OBTER_PRIM_PRESCR_MAT_HOR_GPT(APV.NR_ATENDIMENTO,APV.CD_PESSOA_FISICA,'ACMMEIRELES','1'),'DD/MM/YYYY HH24:MI:SS') PRIM_PRESCR_MAT_HORA_GPT,  
                        (--SEPARANDO:
                        SELECT DS_STATUS_ANALISE
                            FROM TABLE(GPT_UTILS_PCK.GET_PENDING_PATIENTS(NULL,
                            NULL,NULL,SYSDATE - 1,SYSDATE,NULL,'1',NULL,NULL,NULL,NULL,NULL,NULL,'N','N',2,'N','A','N',NULL,'S',1,
                            2,'N','N',NULL,'N','E','N','N',2,'N','N','A','T','N','T','E',NULL,2,'N','S','PVPLIMA',NULL,0,'15',NULL,
                            'N',NULL,NULL,NULL))
                            WHERE 1 = 1
                            AND NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                            FETCH FIRST 1 ROWS ONLY
                        ) GPT_STATUS

                        FROM ATENDIMENTO_PACIENTE_V APV
                        LEFT JOIN PRESCR_MEDICA PM
                            ON (PM.NR_ATENDIMENTO = APV.NR_ATENDIMENTO)
                        LEFT JOIN PRESCR_MAT_HOR PH
                            ON (PH.NR_PRESCRICAO = PM.NR_PRESCRICAO)
                        LEFT JOIN PACIENTE_ALERGIA PA
                            ON (APV.CD_PESSOA_FISICA = PA.CD_PESSOA_FISICA)

                        --=============================================== REGRAS DE NEGOCIO: --===============================================
                        WHERE PH.DT_HORARIO BETWEEN SYSDATE - 1 AND SYSDATE
                        AND APV.CD_SETOR_ATENDIMENTO = 64
                        /*AND APV.CD_SETOR_ATENDIMENTO IN (110,252,208,64,65,66)*/
                        AND APV.DT_ALTA IS NULL

                        GROUP BY APV.CD_SETOR_ATENDIMENTO,
                        APV.CD_PESSOA_FISICA,
                        APV.NR_ATENDIMENTO,
                        APV.IE_STATUS_ATENDIMENTO,
                        APV.CD_MEDICO_RESP,
                        APV.DT_ENTRADA,
                        PA.IE_CLASSIFICACAO

                        ORDER BY OBTER_DESC_SETOR_ATEND(APV.CD_SETOR_ATENDIMENTO),
                        OBTER_LEITO_ATUAL_PAC(APV.NR_ATENDIMENTO),
                        OBTER_NOME_PF(APV.CD_PESSOA_FISICA)                                                    
                    """
                #####################################################################################
                
                #Executando a query:
                #print(f'cursor.execute(sql)\n{sql}')
                cursor.execute(sql)
                
                # Imprimir os resultados da consulta para verificar
                #print(f'results = cursor.fetchall()\n')
                results = cursor.fetchall()
        
                #Exibindo redultado no console:
                #print(f'Exibindo redultado no console:\n')    
                #for r in cursor.execute(sql):
                #    print(r)
                
                #Inserindo resultado em um data frame:
                #df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                
                #print(f'df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])')
                df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
                
                # Visualizar os primeiros 5 registros
                print("# PAI - U.I. 1º ANDAR")
                

    except Exception as erro:
        print(f"Erro Inexperado:\n{erro}")
    
    return df   

def cor_status(val):
    if val == 'Pendente':
        return 'background-color: yellow; color: black ; font-weight: bold' # Amarelo com texto preto para melhor contraste
    elif val == 'Em análise':
        return 'background-color: lightblue; color: black ; font-weight: bold' # Verde claro com texto preto
    elif val == 'Sim':
        return 'background-color: sandybrown; color: black ; font-weight: bold' # Amarelo com texto preto para melhor contraste
    else:
        return ''


def cor_cdrass(val):
    # Aplica cor de fundo à célula RASS com base no valor, com cores suavizadas.
    try:
        v = int(val)
        if abs(v) == 4:
            return 'background-color: #D84B47; color: white; font-weight: bold'  # Sedação profunda / Agressivo (vermelho suave)
        elif abs(v) == 3:
            return 'background-color: #ef9642; color: black; font-weight: bold'  # Sedação moderada / Muito agitado (laranja suave)
        elif abs(v) == 2:
            return 'background-color: #F4D700; color: black; font-weight: bold'  # Sedação leve / Agitado (amarelo suave)
        elif abs(v) == 1:
            return 'background-color: #ffc8cb; color: black; font-weight: bold'  # Sonolento / Inquieto (rosa suave)
        elif v == 0:
            return 'background-color: #66D4C7; color: black; font-weight: bold'  # Alerta, calmo (verde suave)
        elif v == -5:
            return 'background-color: #8B0000; color: white; font-weight: bold'  # Incapaz de ser despertado (vinho suave)
        else:
            return ''
    except ValueError:
        return ''  # Caso não seja um número

        
        
logo_path = 'HSF_LOGO_-_1228x949_001.png'

if __name__ == "__main__":
    try:
        while True:
            print(f'\n{agora()} - PAI - U.I. 1º ANDAR  - if __name__ == "__main__" ')
            st.logo(logo_path,size="large")

            df = pacientes_escalas()
            df = df = df.fillna('-')
            df['ATENDIMENTO'] = df['ATENDIMENTO'].apply(lambda x: "{:.0f}".format(x))
            

            # CSS para maximizar a largura da tabela
            st.markdown(
                """
                <style>
                .dataframe {
                    width: 100% !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            
            # SELECIONA AS COLUNAS ANTES DE ESTILIZAR
            #colunas_selecionadas = ['LEITO', 'ATENDIMENTO','PACIENTE','GLASGOW','BRADEN','MORSE','MARTINS','PRECAUCAO', 'GRUPOS_PACIENTE', 'ALERGIA' , 'GPT_STATUS']
            colunas_selecionadas = ['LEITO', 'ATENDIMENTO','PACIENTE','GLASGOW','RASS','SAPSIII','BRADEN','MORSE','MARTINS','PRECAUCAO', 'GRUPOS_PACIENTE', 'ALERGIA' , 'GPT_STATUS']
            df_selecionado = df[colunas_selecionadas]

             # Define a configuração de largura para cada coluna para garantir consistência
            column_config = {
                "LEITO": st.column_config.TextColumn("LEITO", width="small"),
                "ATENDIMENTO": st.column_config.TextColumn("ATEND", width="small"),
                "PACIENTE": st.column_config.TextColumn("PACIENTE", width="small"),
                "GLASGOW": st.column_config.TextColumn("GLASGOW", width="small"),
                "RASS": st.column_config.TextColumn("RASS", width="small"),
                "SAPSIII": st.column_config.TextColumn("SAPS III", width="small"),
                "BRADEN": st.column_config.TextColumn("BRADEN", width="small"),
                "MORSE": st.column_config.TextColumn("MORSE", width="small"),
                "MARTINS": st.column_config.TextColumn("MARTINS"),
                "PRECAUCAO": st.column_config.TextColumn("PRECAUÇÃO", width="small"),
                "GRUPOS_PACIENTE": st.column_config.TextColumn("GRUPOS", width="small"),
                "ALERGIA": st.column_config.TextColumn("ALERGIA", width="small"),
                "GPT_STATUS": st.column_config.TextColumn("GPT_STATUS", width="small"),
            }
    
            # APLICA O ESTILO APENAS AO DATAFRAME SELECIONADO
            #df_styled = df_selecionado.style.applymap(cor_status, subset=['GPT_STATUS'])
            
            # APLICA O ESTILO APENAS AO DATAFRAME SELECIONADO
            #df_styled = df_selecionado.style.map(cor_status, subset=['GPT_STATUS'])\
            #                               .map(cor_status, subset=['ALERGIA'])
            # df_styled = df_selecionado.style\
            #.applymap(cor_status, subset=['GPT_STATUS'])\
            #.applymap(cor_status, subset=['ALERGIA'])\
            #.apply(lambda row: pd.Series({'RASS': cor_cdrass(row['CD_RASS'])}), axis=1)
            if 'CD_RASS' in df.columns:
                df_styled = df_selecionado.style\
                .applymap(cor_status, subset=['GPT_STATUS'])\
                .applymap(cor_status, subset=['ALERGIA'])\
                .apply(lambda row: pd.Series({'RASS': cor_cdrass(df.loc[row.name, 'CD_RASS'])}), axis=1)
            
            st.write("# PAI - U.I. 1º ANDAR")
            st.write(f'Atualizado: {datetime.datetime.now().strftime("%d/%m/%Y as %H:%M:%S")}')
            
            #Exibindo data frame:
            #st.dataframe(df_styled,hide_index=True, height= calcular_altura_dataframe(df.shape[0]) ,use_container_width=True)
            st.dataframe(df_styled,hide_index=True, height= calcular_altura_dataframe(df.shape[0]) ,use_container_width=True, column_config=column_config)
            

            print(f'{agora()} - Total de: {str(df.shape[0])} pacientes')
            st.write('### Ocupação: ' + str(df.shape[0]) + ' pacientes')
            st.write('\n\n\n')
            st.write('___________________')

    
            
            print(f'{agora()} - Pausar por 600 segundos!')
            
            time.sleep(600)  # Pausar por 600 segundos            
            print(f'PAI - U.I. 1º ANDAR \nst.rerun()\n')
            st.rerun()
        
    except Exception as err: 
        print(f"Inexperado {err=}, {type(err)=}")