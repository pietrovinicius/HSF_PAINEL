#AND APV.CD_SETOR_ATENDIMENTO = 58
# H - Intensiva A 2º ANDAR
'''
58	H - Intensiva A
59	H - Intensiva B
60	H - Intensiva C
61	H - Intensiva D
63	H - Intensiva F
236	EMORP - Intensiva E
'''


import streamlit as st
import pandas as pd
import numpy as np
import os
import oracledb
import pandas as pd
import time
import plotly.graph_objects as go
import locale
import datetime

#Configurando pagina para exibicao em modo WIDE:
st.set_page_config(layout="wide",initial_sidebar_state="collapsed",page_title="H - Intensiva A ")

#SETOR:


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
                                WHEN  PA.IE_CLASSIFICACAO IS NOT NULL 
                                THEN 'Sim'
                                ELSE '-'
                            END ALERGIA,
                            APV.CD_SETOR_ATENDIMENTO AS SETOR_ATENDIMENTO,
                            OBTER_DESC_SETOR_ATEND(APV.CD_SETOR_ATENDIMENTO) AS SETOR,
                            REPLACE(OBTER_LEITO_ATUAL_PAC(APV.NR_ATENDIMENTO),'-',' ') AS LEITO,
                            APV.NR_ATENDIMENTO AS ATENDIMENTO,
                            SUBSTR(obter_nome_pf(APV.CD_PESSOA_FISICA), 1, 1) || 
                            SUBSTR(ABREVIA_NOME(obter_nome_pf(APV.CD_PESSOA_FISICA), 'A'), 
                            INSTR(ABREVIA_NOME(obter_nome_pf(APV.CD_PESSOA_FISICA), 'A'), ' ')) AS PACIENTE,
                            TO_CHAR(APV.DT_ENTRADA,'dd/mm/yy hh24:mi') AS ENTRADA,
                            --MEWS
                            (
                                select 
                                em.QT_PONTUACAO as CLASSIFICACAO
                                from ESCALA_MEWS EM, atendimento_paciente_v A
                                where A.nr_atendimento = em.nr_atendimento
                                and A.dt_alta is null
                                AND A.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                                AND EM.IE_SITUACAO = 'A'
                                order by em.DT_AVALIACAO desc
                                FETCH FIRST 1 ROWS ONLY
                            )   AS MEWS,

                            --BRADEN
                            (
                            select	
                                    initcap(obter_resultado_braden(AEB.qt_ponto))
                                from	atend_escala_braden AEB
                                where  	(nr_atendimento	= APV.nr_atendimento)
                                AND AEB.IE_SITUACAO = 'A'
                                order by	1 desc
                                FETCH FIRST 1 ROWS ONLY
                            ) AS BRADEN,
                            
                            --morse
                            (
                                
                                select	
                                    initcap(obter_desc_escala_morse(qt_pontuacao))
                                from 	escala_morse EMM
                                where EMM.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                                AND EMM.IE_SITUACAO = 'A'
                                order by	1 desc
                                FETCH FIRST 1 ROWS ONLY
                            ) AS MORSE,

                            --SAPS3
                            (
                                
                                select	
                                    QT_PONTUACAO||' / '||PR_RISCO||'%'
                                from 	escala_saps3 SAPS3
                                where SAPS3.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                                AND SAPS3.IE_SITUACAO = 'A'
                                order by	1 desc
                                FETCH FIRST 1 ROWS ONLY
                            ) AS SAPSIII,                            

                            --RASS
                            (
                                SELECT
                                  CASE 
                                    WHEN LENGTH(obter_valor_dominio(2088, IE_RASS)) > 21 THEN 
                                      SUBSTR(obter_valor_dominio(2088, IE_RASS), 1, 21) || '...'
                                    ELSE 
                                      obter_valor_dominio(2088, IE_RASS)
                                  END AS DS_AGITACAO_SEDACAO
                                FROM ESCALA_RICHMOND
                                WHERE 1 = 1
                                  AND nr_atendimento = APV.NR_ATENDIMENTO
                                  AND obter_se_reg_lib_atencao(obter_pessoa_atendimento(nr_atendimento, 'C'),cd_profissional,ie_nivel_atencao,nm_usuario,374) = 'S'
                                FETCH FIRST 1 ROWS ONLY
                            ) RASS,

                            --CD_RASS
                            (
                                SELECT                                   
                                      IE_RASS                                 
                                FROM ESCALA_RICHMOND
                                WHERE 1 = 1
                                  AND nr_atendimento = APV.NR_ATENDIMENTO
                                  AND obter_se_reg_lib_atencao(obter_pessoa_atendimento(nr_atendimento, 'C'),cd_profissional,ie_nivel_atencao,nm_usuario,374) = 'S'
                                FETCH FIRST 1 ROWS ONLY
                            ) CD_RASS,   

                            --fugulin
                            (
                                SELECT 
                                    (
                                        SELECT 
                                        --DS_GRADACAO 

                                        DECODE(
                                            DS_GRADACAO,
                                            'CM', 'Cuidados Mínimos',
                                            'CI', 'Cuidados Intermediários',
                                            'AD', 'Alta Dependência',
                                            'SI', 'Cuidados Semi Intensivos',
                                            'I', 'Cuidados Intensivos',
                                            DS_GRADACAO
                                        )
                                        
                                        FROM GCA_GRADACAO 
                                        WHERE NR_SEQUENCIA = (
                                                                SELECT NR_SEQ_GRADACAO 
                                                                FROM GCA_ATENDIMENTO 
                                                                WHERE NR_SEQUENCIA = 
                                                                    (
                                                                        SELECT MAX(NR_SEQUENCIA) 
                                                                        FROM GCA_ATENDIMENTO 
                                                                        WHERE NR_ATENDIMENTO = AP.NR_ATENDIMENTO 
                                                                        AND IE_SITUACAO = 'A' 
                                                                        AND TRUNC(DT_AVALIACAO) = TRUNC(GCAA.DT_AVALIACAO)
                                                                    )
                                                            )
                                    )
                                FROM ATENDIMENTO_PACIENTE AP
                                INNER JOIN GCA_ATENDIMENTO GCAA ON GCAA.NR_ATENDIMENTO = AP.NR_ATENDIMENTO
                                INNER JOIN GCA_GRADACAO GCAG ON GCAG.NR_SEQUENCIA = GCAA.NR_SEQ_GRADACAO
                                WHERE GCAA.IE_SITUACAO = 'A'
                                AND AP.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                                order by GCAA.DT_AVALIACAO desc
                                FETCH FIRST 1 ROWS ONLY
                            ) AS FUGULIN,

                            --martins
                            (

                                SELECT
                                    substr(obter_desc_resul_score_flex_2(EEI.qt_pontos,EEI.nr_seq_escala),1,255)
                                FROM ESCALA_EIF_II EEII
                                INNER JOIN escala_eif_ii EEI ON (EEI.NR_SEQUENCIA = EEII.NR_SEQUENCIA)
                                INNER JOIN SCORE_AVALIACAO_RESULT SAR ON (EEII.NR_SEQUENCIA = SAR.NR_SEQ_AVALIACAO)
                                INNER JOIN MED_ITEM_AVALIAR MIA ON (MIA.NR_SEQUENCIA = SAR.NR_SEQ_ITEM)
                                INNER JOIN MED_TIPO_AVALIACAO MTA ON (MTA.NR_SEQUENCIA = MIA.NR_SEQ_TIPO)
                                WHERE EEII.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                                AND SAR.DS_RESULTADO IS NOT NULL
                                AND EEII.DT_LIBERACAO IS NOT NULL
                                AND UPPER(MTA.DS_TIPO) LIKE '%MARTINS%'
                                AND EEII.IE_SITUACAO = 'A'
                                GROUP BY        EEII.DT_AVALIACAO,        EEI.qt_pontos,        EEI.nr_seq_escala
                                ORDER BY EEII.DT_AVALIACAO DESC
                                FETCH FIRST 1 ROWS ONLY


                            ) AS MARTINS,

                            --glasgow (retorna texto)
                            (

                                select	
                                    obter_resultado_glasgow(AEI.qt_glasgow)
                                from	atend_escala_indice AEI
                                WHERE 	obter_se_reg_lib_atencao(
                                        obter_pessoa_atendimento(
                                            AEI.nr_atendimento,'C'), 
                                            AEI.cd_pessoa_fisica, 
                                            AEI.ie_nivel_atencao, 
                                            AEI.nm_usuario, 374) = 'S'
                                AND AEI.NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                                order bY AEI.dt_avaliacao desc
                                FETCH FIRST 1 ROWS ONLY

                            ) AS GLASGOW,

                            --MEDICO RESPONSAVEL
                            INITCAP(ABREVIA_NOME(obter_nome_medico(APV.cd_medico_resp,'N'), 'A')) MEDICO_RESPONSAVEL,

                            (
                                select distinct 
                                    INITCAP(ds_precaucao)
                                from atendimento_precaucao_v
                                WHERE IE_SITUACAO = 'A'
                                AND DT_INATIVACAO IS NULL
                                AND NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                                order by DT_REGISTRO DESC
                                FETCH FIRST 1 ROWS ONLY
                            ) PRECAUCAO,

                            OBTER_GRUPOS_PACIENTE(APV.NR_ATENDIMENTO, APV.CD_PESSOA_FISICA) GRUPOS_PACIENTE,

                            to_char(
                                    obter_prim_prescr_mat_hor_gpt(apv.nr_atendimento, apv.cd_pessoa_fisica, 'acmmeireles', '1')
                                    ,'dd/mm/yyyy hh24:mi:ss') prim_prescr_mat_hora_gpt,

                            (
                                --SEPARANDO:
                                SELECT   
                                    ds_status_analise
                                FROM	 
                                table
                                (
                                    gpt_utils_pck.get_pending_patients
                                    (   
                                    null,
                                    null,
                                    null,
                                    --to_date('27/11/2024 00:00:00',	'dd/mm/yyyy hh24:mi:ss'),
                                    --to_date('28/11/2024 23:59:59',	'dd/mm/yyyy hh24:mi:ss'),
                                    SYSDATE - 1 ,
                                    SYSDATE,
                                    null,
                                    '1',
                                    null,
                                    null,
                                    null,
                                    null,
                                    null,
                                    null,
                                    'N',
                                    'N',
                                    2,
                                    'N',
                                    'A',
                                    'N',
                                    null,
                                    'S',
                                    1,
                                    2,
                                    'N',
                                    'N',
                                    null,
                                    'N',
                                    'E',
                                    'N',
                                    'N',
                                    2,
                                    'N',
                                    'N',
                                    'A',
                                    'T',
                                    'N',
                                    'T',
                                    'E',
                                    null,
                                    2,
                                    'N',
                                    'S',
                                    'pvplima',
                                    null,
                                    0,
                                    '15',
                                    null,
                                    'N',
                                    null,
                                    null,
                                    null  
                                    )
                                ) 
                                WHERE 1 = 1
                                AND NR_ATENDIMENTO = APV.NR_ATENDIMENTO
                                FETCH FIRST 1 ROWS ONLY
                            ) GPT_STATUS

                        FROM ATENDIMENTO_PACIENTE_V APV
                        LEFT JOIN prescr_medica PM ON (  PM.NR_ATENDIMENTO = APV.NR_ATENDIMENTO )
                        LEFT JOIN prescr_mat_hor PH ON ( PH.NR_PRESCRICAO = PM.NR_PRESCRICAO)
                        LEFT JOIN PACIENTE_ALERGIA PA ON ( APV.CD_PESSOA_FISICA = PA.CD_PESSOA_FISICA)

                        --=============================================== REGRAS DE NEGOCIO: --===============================================
                        WHERE PH.dt_horario between SYSDATE - 1 and SYSDATE
                        AND APV.CD_SETOR_ATENDIMENTO = 58
                        AND APV.DT_ALTA IS NULL
                        GROUP BY 
                            APV.CD_SETOR_ATENDIMENTO,
                            APV.CD_PESSOA_FISICA,
                            APV.NR_ATENDIMENTO,
                            APV.IE_STATUS_ATENDIMENTO,
                            APV.cd_medico_resp,
                            APV.DT_ENTRADA,
                            PA.IE_CLASSIFICACAO
                        ORDER BY 
                            OBTER_DESC_SETOR_ATEND(APV.CD_SETOR_ATENDIMENTO),
                            OBTER_LEITO_ATUAL_PAC(APV.NR_ATENDIMENTO),
                            obter_nome_pf(APV.CD_PESSOA_FISICA)
                        
                            
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
                print("# H - Intensiva A ")
                #print(f'data_frame:\n{df.head(5)}')
                #print("DataFrame salvo com sucesso!")
                #print("H - Intensiva A ")

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
            print(f'\n{agora()} - H - Intensiva A  - if __name__ == "__main__" ')
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
            # colunas_selecionadas = ['LEITO', 'ATENDIMENTO','PACIENTE','GLASGOW','BRADEN','MORSE','FUGULIN','PRECAUCAO', 'GRUPOS_PACIENTE', 'ALERGIA' , 'GPT_STATUS']
            colunas_selecionadas = ['LEITO', 'ATENDIMENTO','PACIENTE','GLASGOW','RASS','SAPSIII','BRADEN','MORSE','FUGULIN','PRECAUCAO', 'GRUPOS_PACIENTE', 'ALERGIA' , 'GPT_STATUS']
            df_selecionado = df[colunas_selecionadas]
    
    
             # Define a configuração de largura para cada coluna para garantir consistência
            column_config = {
                "LEITO": st.column_config.TextColumn("LEITO", width="small"),
                "ATENDIMENTO": st.column_config.TextColumn("ATEND", width="small"),
                "PACIENTE": st.column_config.TextColumn("PACIENTE", width="small"),
                "GLASGOW": st.column_config.TextColumn("GLASGOW", width=225),
                "RASS": st.column_config.TextColumn("RASS", width=180),
                "SAPSIII": st.column_config.TextColumn("SAPS III", width="small"),
                "BRADEN": st.column_config.TextColumn("BRADEN", width=150),
                "MORSE": st.column_config.TextColumn("MORSE", width="small"),
                "FUGULIN": st.column_config.TextColumn("FUGULIN", width=150),
                "PRECAUCAO": st.column_config.TextColumn("PRECAUÇÃO", width=150),
                "GRUPOS_PACIENTE": st.column_config.TextColumn("GRUPOS", width="small"),
                "ALERGIA": st.column_config.TextColumn("ALERGIA", width="small"),
                "GPT_STATUS": st.column_config.TextColumn("GPT_STATUS", width="small"),
            }
            
            # APLICA O ESTILO APENAS AO DATAFRAME SELECIONADO
            #df_styled = df_selecionado.style.applymap(cor_status, subset=['GPT_STATUS'])
            
            # APLICA O ESTILO APENAS AO DATAFRAME SELECIONADO
            #df_styled = df_selecionado.style.map(cor_status, subset=['GPT_STATUS'])\
            #                               .map(cor_status, subset=['ALERGIA'])
            if 'CD_RASS' in df.columns:
                df_styled = df_selecionado.style\
                .applymap(cor_status, subset=['GPT_STATUS'])\
                .applymap(cor_status, subset=['ALERGIA'])\
                .apply(lambda row: pd.Series({'RASS': cor_cdrass(df.loc[row.name, 'CD_RASS'])}), axis=1)                              
            
            st.write("# H - Intensiva A ")
            st.write(f'Atualizado: {datetime.datetime.now().strftime("%d/%m/%Y as %H:%M:%S")}')
            
            #Exibindo data frame:            
            st.dataframe(df_styled,hide_index=True, height= calcular_altura_dataframe(df.shape[0]) ,use_container_width=True, column_config=column_config)
            

            print(f'{agora()} - Total de: {str(df.shape[0])} pacientes')
            st.write('### Ocupação: ' + str(df.shape[0]) + ' pacientes')
            st.write('\n\n\n')
            st.write('___________________')

            with st.sidebar:
                st.write('# Indicadores:')
                BRADEN = df[['BRADEN']].shape[0]
                BRADEN = df[df['BRADEN'] != '-']
                BRADEN = len(BRADEN)
                #print(f'BRADEN: {BRADEN}')
                st.write(f'Braden: {BRADEN}')
                FUGULIN = df[['FUGULIN']].shape[0]
                FUGULIN = df[df['FUGULIN'] != '-']
                FUGULIN = len(FUGULIN)
                #print(f'FUGULIN: {FUGULIN}')
                st.write(f'Fugulin: {FUGULIN}')
                GLASGOW = df[['GLASGOW']].shape[0]
                GLASGOW = df[df['GLASGOW'] != '-']
                GLASGOW = len(GLASGOW)
                #print(f'GLASGOW: {GLASGOW}')
                st.write(f'Glasgow: {GLASGOW}')   
                RASS = df[['RASS']].shape[0]
                RASS = df[df['RASS'] != '-']
                RASS = len(RASS)
                #print(f'RASS: {RASS}')
                st.write(f'RASS: {RASS}')                                 
                SAPSIII = df[['SAPSIII']].shape[0]
                SAPSIII = df[df['SAPSIII'] != '-']
                SAPSIII = len(SAPSIII)
                #print(f'SAPSIII: {SAPSIII}')
                st.write(f'Saps3: {SAPSIII}')                 
                MORSE = df[['MORSE']].shape[0]
                MORSE = df[df['MORSE'] != '-']
                MORSE = len(MORSE)
                #print(f'MORSE: {MORSE}')
                st.write(f'Morse: {MORSE}')
                PRECAUCAO = df[['PRECAUCAO']].shape[0]
                PRECAUCAO = df[df['PRECAUCAO'] != '-']
                PRECAUCAO = len(PRECAUCAO)
                #print(f'PRECAUCAO: {PRECAUCAO}')
                st.write(f'Precaução: {PRECAUCAO}')

            print(f'{agora()} - Pausar por 600 segundos!')
            
            time.sleep(600)  # Pausar por 600 segundos            
            print(f'H - Intensiva A \nst.rerun()\n')
            st.rerun()
        
    except Exception as err: 
        print(f"Inexperado {err=}, {type(err)=}")