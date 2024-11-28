import streamlit as st
import pandas as pd
import numpy as np
import os
import oracledb
import pandas as pd

from dash import Dash, html, dash_table


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
    print(f"A pasta '{nome_pasta}' não foi encontrada na raiz do aplicativo.")
    return None

@st.cache_data 
def pacientes_query():
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
                            --APV.NR_ATENDIMENTO AS ATEND,
                            INITCAP(ABREVIA_NOME(obter_nome_pf(APV.CD_PESSOA_FISICA), 'A')) AS PACIENTE,
                            TO_CHAR(APV.DT_ENTRADA,'dd/mm/yy hh24:mi') AS ENTRADA,
                            --MEWS
                            (
                                select
                                    decode(
                                            em.QT_PONTUACAO,
                                            0,'Baixo',
                                            1,'Baixo',
                                            2,'Baixo',
                                            3,'Baixo',
                                            4,'Baixo',
                                            5,'Medio',
                                            6,'Medio',
                                            7,'Alto',
                                            8,'Alto',
                                            9,'Alto',
                                            10,'Alto',
                                            11,'Alto',
                                            12,'Alto') 
                                    CLASSIFICACAO
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
                                order by DT_REGISTRO DESC
                                FETCH FIRST 1 ROWS ONLY
                            ) PRECAUCAO
                        FROM ATENDIMENTO_PACIENTE_V APV
                        LEFT JOIN prescr_medica PM ON (  PM.NR_ATENDIMENTO = APV.NR_ATENDIMENTO )
                        LEFT JOIN prescr_mat_hor PH ON ( PH.NR_PRESCRICAO = PM.NR_PRESCRICAO)

                        --=============================================== REGRAS DE NEGOCIO: --===============================================
                        WHERE PH.dt_horario between SYSDATE - 1 and SYSDATE
                        AND APV.CD_SETOR_ATENDIMENTO = 236
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
    
    df = pacientes_query()
    
    st.markdown("""
    <style>
        .dataframe(
            height: 1000px;
            width: 100%;
        )
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("# EMORP - Intensiva E")
    st.sidebar.markdown("# EMORP - Intensiva E")
    st.write("EMORP - Intensiva E")
    st.dataframe(df[['SETOR','PACIENTE','MEWS','BRADEN','MORSE','FUGULIN','MARTINS','GLASGOW','PRECAUCAO']], use_container_width=True)

