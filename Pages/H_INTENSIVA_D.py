import streamlit as st
import pandas as pd
import numpy as np
import os
import oracledb
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(layout="wide")


#SETOR:
#H - INTENSIVA D
import datetime
def agora():
    agora = datetime.datetime.now()
    agora = agora.strftime("%Y-%m-%d %H-%M-%S")
    return str(agora)

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

@st.cache_data 
def pacientes_escalas():
    try:
        un = 'PIETRO'
        cs = '192.168.5.9:1521/TASYPRD'

        # Chamar a função para obter o caminho do Instant Client
        caminho_instantclient = encontrar_diretorio_instantclient()

        # Usar o caminho encontrado para inicializar o Oracle Client
        if caminho_instantclient:
            print(f'if caminho_instantclient:\n')
            print(f'oracledb.init_oracle_client(lib_dir=caminho_instantclient)\n')
            oracledb.init_oracle_client(lib_dir=caminho_instantclient)
        else:
            print("Erro ao localizar o Instant Client. Verifique o nome da pasta e o caminho.")
        
        connection = oracledb.connect( user="TASY", password="aloisk", dsn="192.168.5.9:1521/TASYPRD")
        
        with connection:
            print(f'with oracledb.connect(user=un, password=pw, dsn=cs) as connection\n')
            
            print(f'\nconnection.current_schema: {connection.current_schema}')
            
            with connection.cursor() as cursor:
                print(f'with connection.cursor() as cursor:\n')
                
                #####################################################################################
                #QUERY:
                sql = """ 
                
                        SELECT
                            APV.CD_SETOR_ATENDIMENTO AS SETOR_ATENDIMENTO,
                            OBTER_DESC_SETOR_ATEND(APV.CD_SETOR_ATENDIMENTO) AS SETOR,
                            REPLACE(OBTER_LEITO_ATUAL_PAC(APV.NR_ATENDIMENTO),'-',' ') AS LEITO,
                            APV.NR_ATENDIMENTO AS ATEND,
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
                                order by em.DT_LIBERACAO desc
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

                            --glasgow
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

                        --=============================================== REGRAS DE NEGOCIO: --===============================================
                        WHERE PH.dt_horario between SYSDATE - 1 and SYSDATE
                        AND APV.CD_SETOR_ATENDIMENTO = 61
                        AND APV.DT_ALTA IS NULL
                        GROUP BY 
                            APV.CD_SETOR_ATENDIMENTO,
                            APV.CD_PESSOA_FISICA,
                            APV.NR_ATENDIMENTO,
                            APV.IE_STATUS_ATENDIMENTO,
                            APV.cd_medico_resp,
                            APV.DT_ENTRADA
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
                print(f'results = cursor.fetchall()\n')
                results = cursor.fetchall()
        
                #Exibindo redultado no console:
                #print(f'Exibindo redultado no console:\n')    
                #for r in cursor.execute(sql):
                #    print(r)
                
                #Inserindo resultado em um data frame:
                #df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
                
                print(f'df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])')
                df = pd.DataFrame(results, columns=[desc[0] for desc in cursor.description])
                
                # Visualizar os primeiros 5 registros
                print(f'data_frame:\n{df.head()}')
                print("DataFrame salvo com sucesso!")

    except Exception as erro:
        print(f"Erro Inexperado:\n{erro}")
    
    return df   

# Caminho da sua imagem (ajuste conforme a sua estrutura de pastas)
logo_path = 'HSF_LOGO_-_1228x949_001.png'


if __name__ == "__main__":
    try:
        while True:
                
            st.logo(logo_path,size="large")

            df = pacientes_escalas()

            df = df = df.fillna('-')
            
            df['ATEND'] = df['ATEND'].apply(lambda x: "{:.0f}".format(x))

            print(f'df:\n{df}')

            #SETOR:
            st.markdown("# H - INTENSIVA D")
            st.sidebar.markdown("# H - INTENSIVA D")

            #Exibindo data frame:
            st.dataframe(df[['ATEND','PACIENTE','LEITO','MEWS','BRADEN','MORSE','FUGULIN','GLASGOW','PRECAUCAO', 'GRUPOS_PACIENTE' , 'GPT_STATUS']],hide_index=True, use_container_width=True)
            
            #Total de Pacientes:
            print(f'Total de: {str(df.shape[0])} pacientes')
            st.write('### '+ str(df.shape[0]) + ' pacientes')
            
            st.write('\n\n\n')
            st.write('\n\n\n')
            st.write('\n\n\n')
            st.write('\n\n\n')
            st.write('___________________')
            
            
            st.write('## Dados Sintéticos:')
            
            # Criando três colunas
            col1, col2 = st.columns(2)
            
            with col1:
                #MEWS
                #mews = df[['MEWS']].shape[0]
                #print(f'Mews: {mews}')
                #mews_Baixo = ["Baixo"]
                #mews_Medio = ["Médio"]
                #mews_Alto = ["Alto"]
                #st.write('#### Mews:')
                #st.write(
                #        'Baixo: ' + str(df[['MEWS']].query('MEWS in @mews_Baixo').shape[0])
                #        + '\n\nMédio: ' + str(df[['MEWS']].query('MEWS in @mews_Medio').shape[0])
                #        + '\n\nAlto: ' + str(df[['MEWS']].query('MEWS in @mews_Alto').shape[0])
                #)
                #
                #st.write('\n\n\n')
                #st.write('___________________')
                
                
                #GLASGOW
                GLASGOW = df[['GLASGOW']].shape[0]
                print(f'GLASGOW: {GLASGOW}')
                GLASGOW_disfun_severa = ['disfunção / lesão encefálica severa']
                GLASGOW_disfun_moderada = ['disfunção / lesão encefálica moderada']
                GLASGOW_disfun_leve = ['disfunção / lesão encefálica leve']
                GLASGOW_normal = ['normal']
                st.write('### Glasglow:')
                st.write(
                        'Severa: ' + str(df[['GLASGOW']].query('GLASGOW in @GLASGOW_disfun_severa').shape[0])
                        + '\n\nModerada: ' + str(df[['GLASGOW']].query('GLASGOW in @GLASGOW_disfun_moderada').shape[0])
                        + '\n\nLeve: ' + str(df[['GLASGOW']].query('GLASGOW in @GLASGOW_disfun_leve').shape[0])
                        + '\n\nNormal: ' + str(df[['GLASGOW']].query('GLASGOW in @GLASGOW_normal').shape[0])
                )
                
                st.write('\n\n\n')
                st.write('___________________')
                
                
                #PRECAUCAO
                PRECAUCAO = df[['PRECAUCAO']].shape[0]
                print(f'PRECAUCAO: {PRECAUCAO}')
                PRECAUCAO_Contato_Rastreando = ['Contato / Rastreando']
                PRECAUCAO_Rastreamento = ['Rastreamento']
                PRECAUCAO_Aerossois = ['Aerossóis']
                PRECAUCAO_Clostridium_Contato = ['Clostridium - Contato (Leito Privativo)']
                PRECAUCAO_Contato = ['Contato']
                PRECAUCAO_Covid_Cont_Aeross = ['Covid-19 Contato + Aerossóis']
                PRECAUCAO_Covid_Got_Cont = ['Covid-19 Gotículas + Contato']
                PRECAUCAO_Gotículas = ['Gotículas']
                PRECAUCAO_Herpes = ['Herpes Zoster Disseminada  Aerossol + Contato']
                PRECAUCAO_Contato_Isolamento = ['Precaução De Contato Com Isolamento (Quarto Privativo)']
                st.write('#### Precaução:')
                st.write(
                        '\n\nContato / Rastreando: ' + str(df[['PRECAUCAO']].query('PRECAUCAO in @PRECAUCAO_Contato_Rastreando').shape[0])
                        + ' \n\nRastreamento: ' + str(df[['PRECAUCAO']].query('PRECAUCAO in @PRECAUCAO_Rastreamento').shape[0])
                        + ' \n\nAerossóis: ' + str(df[['PRECAUCAO']].query('PRECAUCAO in @PRECAUCAO_Aerossois').shape[0])
                        + ' \n\nContato: ' + str(df[['PRECAUCAO']].query('PRECAUCAO in @PRECAUCAO_Contato').shape[0])
                        + ' \n\nGotículas: ' + str(df[['PRECAUCAO']].query('PRECAUCAO in @PRECAUCAO_Gotículas').shape[0])
                        + ' \n\nClostridium - Contato (Leito Privativo): ' + str(df[['PRECAUCAO']].query('PRECAUCAO in @PRECAUCAO_Clostridium_Contato').shape[0])
                        + ' \n\nCovid-19 Contato + Aerossóis: ' + str(df[['PRECAUCAO']].query('PRECAUCAO in @PRECAUCAO_Covid_Cont_Aeross').shape[0])
                        + ' \n\nCovid-19 Gotículas + Contato: ' + str(df[['PRECAUCAO']].query('PRECAUCAO in @PRECAUCAO_Covid_Got_Cont').shape[0])
                        + ' \n\nHerpes Zoster: ' + str(df[['PRECAUCAO']].query('PRECAUCAO in @PRECAUCAO_Herpes').shape[0])
                        + ' \n\nPrecaução De Contato Com Isolamento (Quarto Privativo): ' + str(df[['PRECAUCAO']].query('PRECAUCAO in @PRECAUCAO_Contato_Isolamento').shape[0])
                )
                
                st.write('\n\n\n')
                st.write('___________________')
                
                

            with col2:
                #BRADEN:
                braden = df[['BRADEN']].shape[0]
                print(f'Braden: {braden}')
                braden_leve = ["Risco Leve"]
                braden_Moderado = ["Risco Moderado"]
                braden_Muito_Elevado = ["Risco Muito Elevado"]
                st.write('### Braden:')
                st.write('Risco Leve: ' + str(df[['BRADEN']].query('BRADEN in @braden_leve').shape[0]) 
                        + '\n\nRisco Moderado: ' + str(df[['BRADEN']].query('BRADEN in @braden_Moderado').shape[0]) 
                        + '\n\nRisco Muito Elevado: ' + str(df[['BRADEN']].query('BRADEN in @braden_Muito_Elevado').shape[0])
                        )
                
                st.write('\n\n\n')
                st.write('___________________')
                
                #FUGULIN
                FUGULIN = df[['FUGULIN']].shape[0]
                print(f'FUGULIN: {FUGULIN}')
                FUGULIN_Cuidados_Minimos = ['Cuidados Mínimos']
                FUGULIN_Cuidados_Intermediarios = ['Cuidados Intermediários']
                FUGULIN_Alta_Dependencia = ['Alta Dependência']
                FUGULIN_Cuidados_Semi = ['Cuidados Semi Intensivos']
                st.write('### Fugulin:')
                st.write(
                        'Cuidados Mínimos: ' + str(df[['FUGULIN']].query('FUGULIN in @FUGULIN_Cuidados_Minimos').shape[0])
                        + '\n\nCuidados Intermediários: ' + str(df[['FUGULIN']].query('FUGULIN in @FUGULIN_Cuidados_Intermediarios').shape[0])
                        + '\n\nAlta Dependência: ' + str(df[['FUGULIN']].query('FUGULIN in @FUGULIN_Alta_Dependencia').shape[0])
                        + '\n\nCuidados Semi Intensivos: ' + str(df[['FUGULIN']].query('FUGULIN in @FUGULIN_Cuidados_Semi').shape[0])
                )
                
                st.write('\n\n\n')
                st.write('___________________')
            
                
                #MORSE
                morse = df[['MORSE']].shape[0]
                print(f'Morse: {morse}')
                morse_Baixo_Risco = ['Baixo Risco']
                morse_Risco_Medio = ['Risco Médio']
                morse_Risco_Elevado = ['Risco Elevado']
                st.write('### Morse:')
                st.write(
                        'Risco Baixo: ' + str(df[['MORSE']].query('MORSE in @morse_Baixo_Risco').shape[0])
                        + '\n\nRisco Médio: ' + str(df[['MORSE']].query('MORSE in @morse_Risco_Medio').shape[0])
                        + '\n\nRisco Elevado: ' + str(df[['MORSE']].query('MORSE in @morse_Risco_Elevado').shape[0])
                )
                
                st.write('\n\n\n')
                st.write('___________________')
            
            

            

            
            
            
            
            
            
            
            

            print(f'Pausar por 60 segundos!')
            print(f'{agora()}\n')
            time.sleep(60)  # Pausar por 60 segundos            
            print(f'\nst.experimental_rerun()\n')
            st.rerun()
        
    except Exception as err: 
        print(f"Inexperado {err=}, {type(err)=}") 